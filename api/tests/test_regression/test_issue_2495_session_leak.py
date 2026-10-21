"""A failed query must not leak its database connection.

Sessions were closed on the success path only, so any exception between
opening and closing left the connection checked out for the life of the
process -- and `idle in transaction`, which also holds back autovacuum across
the whole database. Production leaked roughly 17 connections a day that way
and exhausted a 255-connection cluster in about a fortnight, after which every
request that needed a connection answered `400 {"reason": "Invalid request"}`.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import SimpleTestCase

from oedb.connection import _get_engine, oedb_session


class SessionLeakTest(SimpleTestCase):
    def checked_out(self):
        return _get_engine().pool.checkedout()

    def test_a_raising_block_returns_its_connection(self):
        before = self.checked_out()

        with self.assertRaises(ValueError):
            with oedb_session() as session:
                session.execute("select 1")
                raise ValueError("whatever the query did")

        self.assertEqual(
            before,
            self.checked_out(),
            "the connection stayed checked out after the block raised, which is "
            "the leak that exhausted production",
        )

    def test_an_early_return_returns_its_connection(self):
        # perform_sql returns early for an empty statement, and that return used
        # to sit between the session being opened and the try that closed it
        before = self.checked_out()

        def returns_early():
            with oedb_session() as session:
                session.execute("select 1")
                return "done"

        self.assertEqual("done", returns_early())
        self.assertEqual(before, self.checked_out())


class CallSitesDoNotLeakTest(SimpleTestCase):
    """The helper existing is not the fix; every call site using it is.

    This is the test that would have caught the original defect, and the one
    that catches a new query function written in the old shape.
    """

    def checked_out(self):
        return _get_engine().pool.checkedout()

    def test_describe_columns_returns_its_connection_when_the_query_raises(self):
        from api import actions

        before = self.checked_out()

        def boom(session, *args, **kwargs):
            # Acquire the connection first, exactly as a real query does. A
            # Session checks nothing out until it executes, so a mock that only
            # raises leaves nothing to leak and the test passes over the hole
            # it was written for.
            session.execute("select 1")
            raise RuntimeError("the database said no")

        real = actions._execute
        actions._execute = boom
        try:
            with self.assertRaises(RuntimeError):
                actions.describe_columns(_AnyTable())
        finally:
            actions._execute = real

        self.assertEqual(
            before,
            self.checked_out(),
            "describe_columns leaked its connection when the query raised",
        )

    def test_no_query_function_opens_a_session_without_the_context_manager(self):
        # a structural check, because the behavioural one above can only cover
        # the sites somebody remembered to write a test for
        import pathlib

        source = pathlib.Path("api/actions.py").read_text()
        self.assertNotIn(
            "_create_oedb_session()",
            source,
            "api/actions.py opens a session directly again; use oedb_session() so "
            "the connection is returned however the block ends",
        )


class _AnyTable:
    """The two attributes describe_columns reads off a Table."""

    name = "whatever"
    oedb_schema = "sandbox"
