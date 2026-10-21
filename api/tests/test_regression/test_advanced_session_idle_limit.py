"""An explicit session with an open cursor never expired.

The idle sweep freed a session only when it had no open cursor. A client that
died, timed out at the web server or left a result half-read kept its cursor
open, and its session then held its place in the connection limit until the
server process restarted. For anonymous clients, who share one limit, a few
such sessions refused every other anonymous client.

Now a session that no request has used for `CURSOR_TIME_OUT` is closed whether
or not it has cursors. "No request has used it" is a marker, not a time
argument: a session stays busy from the moment a request loads it until that
request has finished, streaming included, and a busy session is never swept.
And closing or rolling back an id the server no longer holds answers success
without rebuilding a session for it, so a client at the limit can still free
what it holds.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
import time
from unittest import mock

from django.contrib.auth.models import AnonymousUser

from api import actions, sessions
from api.error import APIError
from api.sessions import _PENDING, SessionContext, close_all_for_user
from api.tests.test_regression.test_issue_2491_commit_after_release import (
    AdvancedAPICase,
)
from api.tests.test_regression.test_issue_2492_exact_connection_count import (
    RendezvousEngine,
    SessionRegistryTestCase,
)
from login.models import myuser


class FakeCursor:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class IdleLimitTest(SessionRegistryTestCase):
    def setUp(self):
        super().setUp()
        self.anonymous = AnonymousUser()

    def explicit(self, owner=None):
        self.use_engine(RendezvousEngine(1))
        return SessionContext(owner=owner or self.owner)

    def with_cursor(self, owner=None, idle=0):
        sess = self.explicit(owner)
        cursor = FakeCursor()
        sess.cursors[1] = cursor
        sess.last_activity = time.time() - idle
        return sess, cursor

    def loaded(self, sess):
        """Load `sess` as a request would, and leave that request running."""
        self.addCleanup(sessions._release_loaded)
        return sessions.load_session_from_context(
            {"connection_id": sess.connection._id, "user": sess.owner}
        )

    def test_a_session_with_a_cursor_idle_past_the_limit_is_closed(self):
        stuck, cursor = self.with_cursor(idle=sessions.CURSOR_TIME_OUT + 1)

        self.explicit()  # any construction runs the sweep

        self.assertNotIn(stuck, self.registered_for(self.owner))
        self.assertTrue(cursor.closed)
        self.assertTrue(stuck.connection.closed)

    def test_it_stops_counting_against_the_limit(self):
        limit = sessions.ANON_CONNECTION_LIMIT
        for _ in range(limit):
            self.with_cursor(self.anonymous, idle=sessions.CURSOR_TIME_OUT + 1)

        for _ in range(limit):
            self.explicit(self.anonymous)

        self.assertEqual(limit, len(self.registered_for(self.anonymous)))

    def test_a_cursor_still_keeps_a_session_past_the_short_limit(self):
        """`TIME_OUT` alone does not close a session with a cursor."""
        kept, cursor = self.with_cursor(idle=sessions.TIME_OUT + 1)

        self.explicit()

        self.assertIn(kept, self.registered_for(self.owner))
        self.assertFalse(cursor.closed)

    def test_a_session_a_request_is_using_is_never_closed(self):
        """However long ago it was loaded: a stream does not touch it."""
        busy, cursor = self.with_cursor()
        self.loaded(busy)
        busy.last_activity = time.time() - 10 * sessions.CURSOR_TIME_OUT

        self.explicit()

        self.assertIn(busy, self.registered_for(self.owner))
        self.assertFalse(cursor.closed)

    def test_the_idle_time_counts_from_the_end_of_the_last_request(self):
        sess, _ = self.with_cursor()
        self.loaded(sess)
        sess.last_activity = time.time() - 10 * sessions.CURSOR_TIME_OUT

        sessions._release_loaded()  # what the request's end sends
        self.explicit()

        self.assertIn(sess, self.registered_for(self.owner))
        self.assertEqual(0, sess.in_use)

    def test_a_refused_open_still_sweeps(self):
        """The sweep runs before the count, so whoever is refused frees too."""
        stuck, _ = self.with_cursor(idle=sessions.CURSOR_TIME_OUT + 1)
        for _ in range(sessions.ANON_CONNECTION_LIMIT):
            self.explicit(self.anonymous)

        with self.assertRaises(APIError):
            self.explicit(self.anonymous)

        self.assertNotIn(stuck, self.registered_for(self.owner))

    def test_a_failing_cursor_close_still_closes_the_connection(self):
        """And the open that ran the sweep is not refused for it."""
        stuck, cursor = self.with_cursor(idle=sessions.CURSOR_TIME_OUT + 1)
        cursor.close = mock.Mock(side_effect=RuntimeError("transaction aborted"))

        with self.assertLogs("oeplatform", "ERROR"):
            opened = self.explicit()

        self.assertTrue(stuck.connection.closed)
        self.assertIn(opened, self.registered_for(self.owner))


class UnknownIdTest(SessionRegistryTestCase):
    """Closing what is already gone succeeds, and takes no place to do it."""

    def setUp(self):
        super().setUp()
        self.anonymous = AnonymousUser()
        self.use_engine(RendezvousEngine(1))
        for _ in range(sessions.ANON_CONNECTION_LIMIT):
            SessionContext(owner=self.anonymous)
        self.unknown = {"connection_id": 4711, "user": self.anonymous}

    def assert_nothing_rebuilt(self):
        self.assertNotIn(4711, sessions._SESSION_CONTEXTS)
        self.assertNotIn(4711, _PENDING)

    def test_close_at_the_limit_answers_success(self):
        self.assertEqual(
            {"success": True}, actions.close_raw_connection({}, self.unknown)
        )
        self.assert_nothing_rebuilt()

    def test_rollback_at_the_limit_answers_success(self):
        self.assertEqual(
            {"success": True}, actions.rollback_raw_connection({}, self.unknown)
        )
        self.assert_nothing_rebuilt()

    def test_other_commands_still_rebuild_the_id(self):
        """`oedialect` relies on it; refusing it is a separate decision."""
        with self.assertRaises(APIError) as caught:
            actions.commit_raw_connection({}, self.unknown)

        self.assertEqual(429, caught.exception.status)


class ThroughTheViewsTest(AdvancedAPICase):
    """End to end, through the real views, the real engine and the real pool."""

    test_table = "advanced_session_idle_limit"
    test_data = [{"name": "Hans"}]

    def setUp(self):
        super().setUp()
        self.me = myuser.objects.get(pk=self.user.pk)
        self.addCleanup(close_all_for_user, self.me)

    def open(self):
        status, body = self.post("connection/open", {})
        self.assertEqual(200, status, body)
        return json.loads(body)["content"]["connection_id"]

    def test_close_on_an_unknown_id_at_the_limit_answers_200(self):
        for _ in range(sessions.USER_CONNECTION_LIMIT):
            self.open()

        status, body = self.post("connection/close", {"connection_id": 4711})

        self.assertEqual(200, status, body)
        self.assertNotIn(4711, sessions._SESSION_CONTEXTS)

    def test_a_finished_request_leaves_its_session_idle(self):
        connection_id = self.open()

        status, body = self.post("cursor/open", {"connection_id": connection_id})

        self.assertEqual(200, status, body)
        self.assertEqual(0, sessions._SESSION_CONTEXTS[connection_id].in_use)

    def test_a_session_is_busy_until_its_stream_has_been_read(self):
        connection_id = self.open()
        query = {"from": {"type": "table", "table": self.test_table}}

        response = self.client.post(
            "/api/v0/advanced/search",
            data=json.dumps({"connection_id": connection_id, "query": query}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Token %s" % self.token,
        )
        sess = sessions._SESSION_CONTEXTS[connection_id]
        busy_while_streaming = sess.in_use
        body = b"".join(response.streaming_content).decode()

        self.assertIn("Hans", body)
        self.assertEqual(1, busy_while_streaming)
        self.assertEqual(0, sess.in_use)
