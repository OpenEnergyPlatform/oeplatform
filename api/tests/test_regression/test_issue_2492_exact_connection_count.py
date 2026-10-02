"""The connection limit was a likelihood, not a limit.

`SessionContext.__init__` counted the owner's open sessions by walking the
module-level `_SESSION_CONTEXTS` dict, then opened a connection, and only then
registered itself -- and nothing guarded the dict. A request that had passed
the count but not yet registered was invisible to every other request counting
at that moment, so at *n* concurrent requests from one account the number
refused depended on how the threads happened to interleave. WF-20 measured it
against the real endpoint with a limit of 4: 0 of 10 runs refused anything at
4 concurrent, 5 of 10 at 8, 9 of 10 at 12 -- where exactly *n - 4* was meant.

The same gap let two constructions for one connection id both pass the
"already open" check, the second overwriting the first.

The engine is replaced by one that holds every connecting thread until all the
others have either reached it too or been refused. That is the widest the
window between counting and registering can be, so the harness reproduces the
worst interleaving on every run instead of racing for it. The class and the
module dict are the real ones.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import threading
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase

from api import sessions
from api.error import APIError
from api.sessions import _SESSION_CONTEXTS, SessionContext, close_all_for_user
from login.models import myuser

TIMEOUT = 10


class FakeDBAPIConnection:
    """Enough of a DBAPI connection for a session to be built around it."""

    def __init__(self):
        self.closed = False

    def cursor(self, name=None):
        raise AssertionError("this test opens no cursors")

    def close(self):
        self.closed = True


class RendezvousEngine:
    """Holds each `connect()` until every participant has settled.

    A participant settles by reaching `connect()` or by having its
    construction refused. So a connection is only handed out once every other
    thread has had its chance to count -- the interleaving in which a count
    that does not see in-flight constructions is most wrong.
    """

    def __init__(self, participants):
        self.participants = participants
        self.settled = 0
        self.connections = 0
        self.condition = threading.Condition()

    def settle(self):
        with self.condition:
            self.settled += 1
            self.condition.notify_all()

    def connect(self):
        with self.condition:
            self.connections += 1
        self.settle()
        with self.condition:
            if not self.condition.wait_for(
                lambda: self.settled >= self.participants, TIMEOUT
            ):
                raise AssertionError("not every participant settled")
        return mock.Mock(connection=FakeDBAPIConnection())


class SessionRegistryTestCase(SimpleTestCase):
    def setUp(self):
        previous = dict(_SESSION_CONTEXTS)
        _SESSION_CONTEXTS.clear()
        self.addCleanup(lambda: _SESSION_CONTEXTS.update(previous))
        self.addCleanup(_SESSION_CONTEXTS.clear)

        self.owner = myuser(id=1, name="owner")

    def use_engine(self, engine):
        patch = mock.patch.object(sessions, "_get_engine", lambda: engine)
        patch.start()
        self.addCleanup(patch.stop)

    def construct_concurrently(self, n, owner, connection_id=None, **session_kwargs):
        """Release *n* constructions from one barrier and collect what each got."""
        engine = RendezvousEngine(n)
        self.use_engine(engine)
        barrier = threading.Barrier(n)
        results = [None] * n

        def build(i):
            barrier.wait(TIMEOUT)
            try:
                results[i] = SessionContext(
                    connection_id=connection_id, owner=owner, **session_kwargs
                )
            except BaseException as error:  # noqa: B036 - the refusal is the result
                results[i] = error
                engine.settle()

        threads = [
            threading.Thread(target=build, args=(i,), daemon=True) for i in range(n)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(TIMEOUT)
        self.assertFalse(
            any(thread.is_alive() for thread in threads), "a construction hung"
        )
        return results, engine

    def registered_for(self, owner):
        return [s for s in _SESSION_CONTEXTS.values() if s.owner == owner]


class ExactCountTest(SessionRegistryTestCase):
    def assert_exactly_the_excess_is_refused(self, n, owner, limit):
        results, engine = self.construct_concurrently(n, owner)

        refused = [r for r in results if isinstance(r, APIError)]
        opened = [r for r in results if isinstance(r, SessionContext)]
        self.assertEqual(
            len(refused) + len(opened), n, f"unexpected failures: {results}"
        )
        self.assertEqual(max(n - limit, 0), len(refused))
        self.assertEqual(min(n, limit), len(self.registered_for(owner)))
        # a refused request never reached the pool: the limit is also what
        # keeps a burst from one account off the connections everyone shares
        self.assertEqual(min(n, limit), engine.connections)

    def test_at_the_limit_nothing_is_refused(self):
        limit = sessions.USER_CONNECTION_LIMIT
        self.assert_exactly_the_excess_is_refused(limit, self.owner, limit)

    def test_at_twice_the_limit_exactly_the_excess_is_refused(self):
        limit = sessions.USER_CONNECTION_LIMIT
        self.assert_exactly_the_excess_is_refused(2 * limit, self.owner, limit)

    def test_at_three_times_the_limit_exactly_the_excess_is_refused(self):
        limit = sessions.USER_CONNECTION_LIMIT
        self.assert_exactly_the_excess_is_refused(3 * limit, self.owner, limit)

    def test_the_anonymous_limit_is_exact_too(self):
        limit = sessions.ANON_CONNECTION_LIMIT
        self.assert_exactly_the_excess_is_refused(limit + 3, AnonymousUser(), limit)

    def test_the_count_is_per_account(self):
        other = myuser(id=2, name="other")
        limit = sessions.USER_CONNECTION_LIMIT
        for _ in range(limit):
            self.use_engine(RendezvousEngine(1))
            SessionContext(owner=other)

        self.assert_exactly_the_excess_is_refused(limit + 1, self.owner, limit)


class ConnectionIdCollisionTest(SessionRegistryTestCase):
    def test_two_constructions_for_one_id_do_not_both_open(self):
        results, engine = self.construct_concurrently(2, self.owner, connection_id=7)

        opened = [r for r in results if isinstance(r, SessionContext)]
        self.assertEqual(1, len(opened), f"expected one winner: {results}")
        self.assertIs(opened[0], _SESSION_CONTEXTS[7])
        # the loser was stopped before it took a connection, so none leaked
        self.assertEqual(1, engine.connections)


class FailedConnectTest(SessionRegistryTestCase):
    """A place is reserved before the connection opens, and must be given back."""

    def test_a_failed_connect_does_not_keep_its_place(self):
        class BrokenEngine:
            def connect(self):
                raise OSError("database unreachable")

        self.use_engine(BrokenEngine())
        for _ in range(sessions.USER_CONNECTION_LIMIT):
            with self.assertRaises(OSError):
                SessionContext(owner=self.owner)

        self.use_engine(RendezvousEngine(1))
        for _ in range(sessions.USER_CONNECTION_LIMIT):
            SessionContext(owner=self.owner)

        self.assertEqual(
            sessions.USER_CONNECTION_LIMIT, len(self.registered_for(self.owner))
        )

    def test_a_failed_connect_does_not_keep_its_id(self):
        class BrokenEngine:
            def connect(self):
                raise OSError("database unreachable")

        self.use_engine(BrokenEngine())
        with self.assertRaises(OSError):
            SessionContext(connection_id=7, owner=self.owner)

        self.use_engine(RendezvousEngine(1))
        self.assertIs(
            SessionContext(connection_id=7, owner=self.owner), _SESSION_CONTEXTS[7]
        )


class LockIsNotHeldWhileConnectingTest(SessionRegistryTestCase):
    """`engine.connect()` can block; a module lock across it would queue the group."""

    def test_the_registry_stays_usable_while_a_connection_is_being_opened(self):
        connecting = threading.Event()
        release = threading.Event()

        class SlowEngine:
            calls = 0

            def connect(self):
                SlowEngine.calls += 1
                if SlowEngine.calls == 1:
                    connecting.set()
                    release.wait(TIMEOUT)
                return mock.Mock(connection=FakeDBAPIConnection())

        self.use_engine(SlowEngine())
        slow = threading.Thread(
            target=lambda: SessionContext(owner=self.owner), daemon=True
        )
        slow.start()
        self.addCleanup(release.set)
        self.assertTrue(connecting.wait(TIMEOUT), "the first connect never started")

        other = myuser(id=2, name="other")

        def meanwhile():
            SessionContext(owner=other)
            close_all_for_user(other)

        quick = threading.Thread(target=meanwhile, daemon=True)
        quick.start()
        quick.join(TIMEOUT)
        stuck = quick.is_alive()

        release.set()
        slow.join(TIMEOUT)
        self.assertFalse(stuck, "the registry was locked while a connection opened")
        self.assertEqual(1, len(self.registered_for(self.owner)))
