"""A browser could refuse its own table view on the connection limit.

The connection limits were written for explicit sessions: a client such as
`oedialect` opens one with `advanced/connection/open` and keeps it across many
requests, so a client that forgets to close it could otherwise drain the pool.
But the same counter also counted *artificial* connections -- the ones
`load_cursor` opens for a single request that brought no `connection_id` and
closes when that request ends. That covers every search the table view sends
and the whole table REST API. The browser sends two such searches per redraw,
so an account paging through a couple of tabs reached the limit and was told
about an `oedialect` bug it had never used (WF-20).

Decided on 2026-09-23 (slice 4 of #2492): an artificial connection cannot
outlive its request, so it does not count. Only explicit sessions do. A limit
refusal now says what is true for the caller who reaches it, and a request
that waited too long for a pooled connection is told the server is busy
instead of that its request was invalid.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from sqlalchemy.exc import TimeoutError as PoolTimeout

from api import sessions
from api.error import APIError
from api.sessions import SessionContext, close_all_for_user
from api.tests.test_regression.test_issue_2491_commit_after_release import (
    AdvancedAPICase,
)
from api.tests.test_regression.test_issue_2492_exact_connection_count import (
    RendezvousEngine,
    SessionRegistryTestCase,
)
from login.models import myuser


class ArtificialConnectionsAreNotCountedTest(SessionRegistryTestCase):
    def setUp(self):
        super().setUp()
        self.limit = sessions.USER_CONNECTION_LIMIT

    def explicit(self, owner=None):
        self.use_engine(RendezvousEngine(1))
        return SessionContext(owner=owner or self.owner)

    def artificial(self, owner=None):
        self.use_engine(RendezvousEngine(1))
        return SessionContext(owner=owner or self.owner, counted=False)

    def test_an_account_at_its_limit_still_gets_artificial_connections(self):
        for _ in range(self.limit):
            self.explicit()

        for _ in range(3 * self.limit):
            self.artificial()

    def test_artificial_connections_leave_the_explicit_limit_untouched(self):
        for _ in range(3 * self.limit):
            self.artificial()

        for _ in range(self.limit):
            self.explicit()
        with self.assertRaises(APIError):
            self.explicit()

    def test_many_concurrent_artificial_connections_are_all_opened(self):
        """The browser's concurrency, from one barrier, well over the limit."""
        n = 3 * self.limit
        results, engine = self.construct_concurrently(n, self.owner, counted=False)

        self.assertEqual(
            [], [r for r in results if not isinstance(r, SessionContext)], results
        )
        self.assertEqual(n, engine.connections)

    def test_the_anonymous_limit_does_not_count_them_either(self):
        anonymous = AnonymousUser()
        for _ in range(sessions.ANON_CONNECTION_LIMIT):
            self.explicit(anonymous)

        self.artificial(anonymous)

    def test_an_artificial_connection_is_still_released_with_the_account(self):
        """Not counted is not unmanaged: close_all still reaches it."""
        self.artificial()

        close_all_for_user(self.owner)

        self.assertEqual([], self.registered_for(self.owner))


class LimitRefusalTest(SessionRegistryTestCase):
    """What a caller at the limit is told. Only explicit sessions reach this."""

    def refusal(self, owner, limit):
        self.use_engine(RendezvousEngine(1))
        for _ in range(limit):
            SessionContext(owner=owner)
        with self.assertRaises(APIError) as caught:
            SessionContext(owner=owner)
        return caught.exception

    def test_an_account_is_told_its_count_and_the_way_out(self):
        limit = sessions.USER_CONNECTION_LIMIT
        refusal = self.refusal(self.owner, limit)

        self.assertEqual(429, refusal.status)
        self.assertIn(str(limit), refusal.message)
        self.assertIn(reverse("api:advanced-connection-close"), refusal.message)
        self.assertIn(reverse("api:advanced-connection-close-all"), refusal.message)
        self.assertNotIn("oedialect", refusal.message)
        self.assertNotIn("openenergy", refusal.message)  # no domain, relative paths

    def test_an_anonymous_caller_is_told_the_limit_is_shared(self):
        limit = sessions.ANON_CONNECTION_LIMIT
        refusal = self.refusal(AnonymousUser(), limit)

        self.assertEqual(429, refusal.status)
        self.assertIn(str(limit), refusal.message)
        self.assertIn("share a limit", refusal.message)
        self.assertIn("Log in", refusal.message)
        # close_all needs a login, so it is not advice to somebody without one
        self.assertNotIn(reverse("api:advanced-connection-close-all"), refusal.message)


class BrowserCannotRefuseItselfTest(AdvancedAPICase):
    """End to end, through the real views, the real engine and the real pool."""

    test_table = "issue_2492_browser"
    test_data = [{"name": "Hans"}]

    def tearDown(self):
        close_all_for_user(myuser.objects.get(pk=self.user.pk))
        super().tearDown()

    def open_connection(self):
        status, body = self.post("connection/open", {})
        return status, json.loads(body)

    def search(self):
        return self.post(
            "search", {"query": {"from": {"type": "table", "table": self.test_table}}}
        )

    def test_a_search_is_answered_while_the_account_holds_its_limit(self):
        for _ in range(sessions.USER_CONNECTION_LIMIT):
            status, body = self.open_connection()
            self.assertEqual(200, status, body)

        status, body = self.search()

        self.assertEqual(200, status, body)
        self.assertIn("Hans", body)

    def test_one_session_over_the_limit_is_refused_with_429(self):
        for _ in range(sessions.USER_CONNECTION_LIMIT):
            self.open_connection()

        status, body = self.open_connection()

        self.assertEqual(429, status, body)
        self.assertIn(reverse("api:advanced-connection-close-all"), body["reason"])


class PoolTimeoutTest(AdvancedAPICase):
    """Waiting too long for a pooled connection is not an invalid request."""

    test_table = "issue_2492_pool"
    test_data = [{"name": "Hans"}]

    def test_a_pool_timeout_answers_503_with_retry_after(self):
        class ExhaustedPool:
            def connect(self):
                raise PoolTimeout("QueuePool limit reached, connection timed out")

        with mock.patch.object(sessions, "_get_engine", ExhaustedPool):
            response = self.client.post(
                "/api/v0/advanced/search",
                data=json.dumps(
                    {"query": {"from": {"type": "table", "table": self.test_table}}}
                ),
                content_type="application/json",
                HTTP_AUTHORIZATION="Token %s" % self.token,
            )

        self.assertEqual(503, response.status_code, response.content)
        self.assertTrue(response["Retry-After"].isdigit())
        reason = json.loads(response.content)["reason"]
        self.assertIn("busy", reason)
        self.assertNotIn("Invalid request", reason)
