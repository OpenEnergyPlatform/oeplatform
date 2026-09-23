"""A session was reachable from other threads before it knew whose it was.

`SessionContext.__init__` registered the new object in the module-level
`_SESSION_CONTEXTS` dict and assigned `self.owner` only afterwards, and the
class carried no `owner` default. Every reader of that dict -- the counting
sweep in the constructor itself, `close_all_for_user` and
`load_session_from_context` -- reads `sess.owner` and catches `KeyError` only.
A session observed inside that window therefore raised
`AttributeError: 'SessionContext' object has no attribute 'owner'`, which
nothing catches: the caller receives a 500, not a wrong count.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import threading
from contextlib import contextmanager
from unittest import mock

from django.test import SimpleTestCase

from api import sessions
from api.sessions import (
    _SESSION_CONTEXTS,
    SessionContext,
    close_all_for_user,
    load_session_from_context,
)
from login.models import myuser

MISSING = object()


class FakeDBAPIConnection:
    """Enough of a DBAPI connection for a session to be built around it.

    The defect is in the bookkeeping, not in the database, so no OEDB
    connection is opened here. The class under test and the module dict it
    registers into are the real ones.
    """

    def __init__(self):
        self.closed = False

    def cursor(self, name=None):
        raise AssertionError("this test opens no cursors")

    def close(self):
        self.closed = True


class FakeEngine:
    def connect(self):
        return mock.Mock(connection=FakeDBAPIConnection())


class SessionContextTestCase(SimpleTestCase):
    """Shared scaffolding: a replaced engine and an empty session registry."""

    TIMEOUT = 5

    def setUp(self):
        engine = mock.patch.object(sessions, "_get_engine", FakeEngine)
        engine.start()
        self.addCleanup(engine.stop)

        previous = dict(_SESSION_CONTEXTS)
        _SESSION_CONTEXTS.clear()
        self.addCleanup(lambda: _SESSION_CONTEXTS.update(previous))
        self.addCleanup(_SESSION_CONTEXTS.clear)

        self.owner = myuser(id=1, name="owner")

    @contextmanager
    def first_registration_paused(self):
        """Hold the very first session inside its registration.

        The window is two bytecodes wide, so it is forced rather than raced
        for: forty attempts at racing two real constructions never hit it.
        `_add_entry` is the one place a session is published into the module
        dict, so pausing there parks a session in whatever state the
        constructor has published it in, and a second thread then walks the
        dict and finds it.
        """
        inserted = threading.Event()
        release = threading.Event()
        real_add_entry = sessions._add_entry

        def add_entry_then_wait(value, dictionary, key=None):
            key = real_add_entry(value, dictionary, key)
            if not inserted.is_set():  # only the first session is held
                inserted.set()
                release.wait(self.TIMEOUT)
            return key

        patch = mock.patch.object(sessions, "_add_entry", add_entry_then_wait)
        patch.start()
        try:
            yield inserted, release
        finally:
            release.set()
            patch.stop()

    def construct_in_a_thread(self, results, key):
        def build():
            try:
                results[key] = SessionContext(owner=self.owner)
            except BaseException as error:  # noqa: B036 - the defect is the error
                results[key] = error

        thread = threading.Thread(target=build, daemon=True)
        thread.start()
        return thread


class ConcurrentConstructionTest(SessionContextTestCase):
    def test_a_session_registered_but_not_yet_finished_does_not_break_the_next_one(
        self,
    ):
        results = {}
        with self.first_registration_paused() as (inserted, release):
            first = self.construct_in_a_thread(results, "first")
            self.assertTrue(
                inserted.wait(self.TIMEOUT), "the first session never registered"
            )

            # the window is open here, and this is what it proves: the paused
            # session is reachable from this thread
            observed = list(_SESSION_CONTEXTS.values())

            second = SessionContext(owner=self.owner)
            release.set()
            first.join(self.TIMEOUT)

        self.assertEqual(
            1,
            len(observed),
            "the pause did not overlap the second construction, so this test "
            "proved nothing",
        )
        self.assertIsInstance(
            results.get("first"), SessionContext, "the first construction failed"
        )
        self.assertIsInstance(second, SessionContext)

    def test_the_registered_session_already_carries_its_owner(self):
        """`owner` is assigned before the object is published, not after."""
        seen = []
        real_add_entry = sessions._add_entry

        def record(value, dictionary, key=None):
            seen.append(getattr(value, "owner", MISSING))
            return real_add_entry(value, dictionary, key)

        with mock.patch.object(sessions, "_add_entry", record):
            SessionContext(owner=self.owner)

        self.assertEqual([self.owner], seen)


class HalfBuiltSessionIsReadableTest(SessionContextTestCase):
    """The class default, which is the belt to the ordering's braces.

    No reader may raise `AttributeError` even when it does meet an object whose
    `owner` has not been assigned. The reasoning is beside the attribute in
    `api/sessions.py`.
    """

    def half_built_session(self):
        session = SessionContext(owner=self.owner)
        del session.__dict__["owner"]
        return session

    def test_the_class_carries_an_owner_default(self):
        self.assertIsNone(getattr(SessionContext, "owner", MISSING))

    def test_the_counting_sweep_does_not_raise(self):
        self.half_built_session()

        SessionContext(owner=self.owner)

    def test_close_all_for_user_does_not_raise(self):
        self.half_built_session()

        close_all_for_user(self.owner)

    def test_load_session_from_context_reaches_its_permission_check(self):
        session = self.half_built_session()
        connection_id = session.connection._id

        with self.assertRaises(PermissionError):
            load_session_from_context(
                {"connection_id": connection_id, "user": self.owner}
            )
