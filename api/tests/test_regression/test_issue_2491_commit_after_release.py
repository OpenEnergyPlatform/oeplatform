"""A streamed read must not commit a connection it has already given back.

`load_cursor` built its after-streaming triggers as
`[close_cursor, close_raw_connection, connection.commit]`. Trigger 2 returns
the connection to the pool and trigger 3 commits it afterwards -- on whatever
transaction is open on it by then. `connection` is a SQLAlchemy
`_ConnectionFairy` with no `commit` of its own, so the bound method captured
when the list was built belonged to the raw psycopg2 connection and stayed
callable across the checkout, which is why the stray commit succeeded quietly
instead of raising.

So a request that had already answered could commit an unrelated request's
in-flight transaction, and that request's own rollback then did nothing. The
decorator is shared by `/api/v0/advanced/search`, `/insert`, `/delete` and
`/update` (issue #2491).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

import psycopg2

import api.helper as helper
from api.actions import load_session_from_context
from api.tests import APITestCaseWithTable
from oedb.connection import OEDB_POOL_SIZE, _get_engine
from oeplatform.settings import (
    SCHEMA_DEFAULT_TEST_SANDBOX,
    dbhost,
    dbname,
    dbpasswd,
    dbport,
    dbuser,
)

MARKER = "issue-2491"


class AdvancedSearchConnectionTest(APITestCaseWithTable):
    """Everything here runs against the real engine and the real pool.

    A mock hands back the connection it was given and so cannot show the pool
    handing the *same* raw connection to somebody else, which is the whole of
    this defect.
    """

    test_table = "issue_2491"
    test_data = [{"name": "Hans"}, {"name": "Petra"}]

    def setUp(self):
        super().setUp()
        self.engine = _get_engine()
        # The pool is process-wide, so whatever ran before this test left
        # connections in it. Emptying it first is what makes "the connection
        # request A gave back" and "the connection request B was handed" the
        # same object rather than a coincidence.
        self.engine.dispose()

    def search(self, connection_id=None):
        """POST the search the table page sends, and drain the streamed body.

        The triggers fire when the generator is exhausted, so nothing under
        test has happened until the body has been read.
        """
        payload = {"query": {"from": {"type": "table", "table": self.test_table}}}
        if connection_id is not None:
            payload["connection_id"] = connection_id
        response = self.client.post(
            "/api/v0/advanced/search",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Token %s" % self.token,
        )
        if hasattr(response, "streaming_content"):
            body = b"".join(response.streaming_content).decode()
        else:
            body = response.content.decode()
        return response.status_code, body

    def rows_named(self, name):
        """Count committed rows from outside the engine.

        Deliberately not `engine.raw_connection()`: a checkout and return of
        its own moves the pool the test is reasoning about.
        """
        connection = psycopg2.connect(
            dbname=dbname, user=dbuser, password=dbpasswd, host=dbhost, port=dbport
        )
        try:
            cursor = connection.cursor()
            cursor.execute(
                'select count(*) from "%s"."%s" where name = %%s'
                % (SCHEMA_DEFAULT_TEST_SANDBOX, self.test_table),
                (name,),
            )
            return cursor.fetchone()[0]
        finally:
            connection.close()

    def on_connection_returned(self, act):
        """Run `act(raw_connection)` the instant request A gives its connection back.

        That instant is the whole of the defect: it is the first moment another
        request can be handed the connection, and on the shipped order a
        trigger still fired after it. The interleaving is forced rather than
        raced for, so the test is deterministic -- and it is pinned to *the
        connection being returned*, not to a position in the trigger list, so
        it keeps its meaning if the list is rewritten.
        """
        real = helper.close_raw_connection

        def hooked(request, context):
            raw = load_session_from_context(context).connection.connection
            # Take every idle connection out of the pool first, so the one A is
            # about to return is the only one there and is necessarily the one
            # handed out next. The pool is FIFO, so without this A's connection
            # queues behind whatever its own request left behind.
            drained = []
            while self.engine.pool.checkedin() > 0:
                drained.append(self.engine.connect())
            try:
                result = real(request, context)
                act(raw)
            finally:
                for connection in drained:
                    connection.close()
            return result

        helper.close_raw_connection = hooked
        self.addCleanup(setattr, helper, "close_raw_connection", real)

    def test_the_next_request_to_take_the_connection_keeps_its_rollback(self):
        """The issue's own demonstration, against the real pool.

        Request A has answered. Request B is handed the same raw connection,
        inserts a row and rolls back. The row must be gone.
        """
        taken = {}

        def take_the_connection_and_write(a_raw):
            fairy = self.engine.connect().connection
            taken["fairy"] = fairy
            self.addCleanup(fairy.close)
            self.assertIs(
                fairy.connection,
                a_raw,
                "the pool did not hand request B the connection request A "
                "returned, so this test cannot say anything about the defect",
            )
            cursor = fairy.cursor()
            cursor.execute(
                'insert into "%s"."%s" (name) values (%%s)'
                % (SCHEMA_DEFAULT_TEST_SANDBOX, self.test_table),
                (MARKER,),
            )
            cursor.close()

        self.on_connection_returned(take_the_connection_and_write)

        status_code, body = self.search()
        self.assertEqual(200, status_code, body)

        taken["fairy"].rollback()

        self.assertEqual(
            0,
            self.rows_named(MARKER),
            "request B's rollback did not hold: a request that had already "
            "answered committed B's transaction after giving the connection back",
        )

    def test_no_trigger_holds_a_method_bound_to_a_connection(self):
        """The early binding, which is the fault underneath the ordering.

        A bound method that outlives the checkout is a loaded gun whatever
        order the list is in, so this is asserted separately from the
        behaviour above: reordering alone would leave the next person free to
        move the lines back.
        """
        captured = []
        real = helper.transform_results

        def hooked(cursor, triggers, trigger_args):
            captured.extend(triggers)
            return real(cursor, triggers, trigger_args)

        helper.transform_results = hooked
        self.addCleanup(setattr, helper, "transform_results", real)

        status_code, body = self.search()
        self.assertEqual(200, status_code, body)
        self.assertTrue(captured, "the streamed read built no triggers")

        for trigger in captured:
            self.assertIsNone(
                getattr(trigger, "__self__", None),
                "trigger %r carries a database object bound when the trigger "
                "list was built; it must resolve the connection through the "
                "context at the moment it fires" % trigger,
            )

    def test_a_streamed_read_still_returns_its_rows(self):
        """The ordering the comment protects: the cursor still closes first.

        `/advanced/search` runs on `load_cursor(named=True)`, a server-side
        named cursor, and committing before the cursor is closed destroys it.
        """
        status_code, body = self.search()
        self.assertEqual(200, status_code, body)
        self.assertIn("Hans", body)
        self.assertIn("Petra", body)


class CallerSuppliedConnectionTest(APITestCaseWithTable):
    """The same triggers fire for a client that brought its own connection.

    `oedialect` opens a connection, works across several requests and commits
    at the end, so on this path the commit has something to commit -- which is
    why it is kept rather than dropped.
    """

    test_table = "issue_2491_session"
    test_data = [{"name": "Hans"}]

    def setUp(self):
        super().setUp()
        self.engine = _get_engine()
        self.engine.dispose()

    def post(self, path, payload):
        response = self.client.post(
            "/api/v0/advanced/%s" % path,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Token %s" % self.token,
        )
        if hasattr(response, "streaming_content"):
            body = b"".join(response.streaming_content).decode()
        else:
            body = response.content.decode()
        return response.status_code, body

    def rows_named(self, name):
        connection = psycopg2.connect(
            dbname=dbname, user=dbuser, password=dbpasswd, host=dbhost, port=dbport
        )
        try:
            cursor = connection.cursor()
            cursor.execute(
                'select count(*) from "%s"."%s" where name = %%s'
                % (SCHEMA_DEFAULT_TEST_SANDBOX, self.test_table),
                (name,),
            )
            return cursor.fetchone()[0]
        finally:
            connection.close()

    def open_connection_and_insert(self):
        status_code, body = self.post("connection/open", {"query": {}})
        self.assertEqual(200, status_code, body)
        connection_id = json.loads(body)["content"]["connection_id"]

        status_code, body = self.post(
            "insert",
            {
                "connection_id": connection_id,
                "query": {
                    "table": self.test_table,
                    "schema": "sandbox",
                    "values": [{"name": MARKER}],
                },
            },
        )
        self.assertEqual(200, status_code, body)
        self.assertEqual(
            0, self.rows_named(MARKER), "the insert committed before it was asked to"
        )
        return connection_id

    def search(self, connection_id):
        return self.post(
            "search",
            {
                "connection_id": connection_id,
                "query": {"from": {"type": "table", "table": self.test_table}},
            },
        )

    def test_a_read_still_commits_the_transaction_it_was_handed(self):
        """A guard on the fix, not a demonstration of the defect.

        Dropping the commit is the other move this ticket weighed -- the pool
        rolls a returned connection back anyway and a `SELECT` has nothing to
        commit. It would silently discard the write on this path, so it is
        pinned here.
        """
        connection_id = self.open_connection_and_insert()

        status_code, body = self.search(connection_id)
        self.assertEqual(200, status_code, body)

        self.assertEqual(
            1,
            self.rows_named(MARKER),
            "the streamed read no longer commits the connection it was given",
        )

    def test_a_read_survives_the_pool_discarding_its_connection(self):
        """The second way the late trigger showed: it raised, mid-stream.

        A connection returned to a full pool is closed rather than kept, and
        `commit` on a closed psycopg2 connection raises `InterfaceError` --
        out of the response generator, after the headers have gone. The pool
        is filled here deliberately, because leaving it to chance makes the
        test pass or fail on what ran before it.
        """
        connection_id = self.open_connection_and_insert()

        idle = [self.engine.connect() for _ in range(OEDB_POOL_SIZE)]
        for connection in idle:
            connection.close()
        self.assertEqual(OEDB_POOL_SIZE, self.engine.pool.checkedin())

        try:
            status_code, body = self.search(connection_id)
        except psycopg2.InterfaceError as error:
            self.fail(
                "a trigger fired against the connection after the pool had "
                "discarded it: %s" % error
            )
        self.assertEqual(200, status_code, body)
        self.assertIn("Hans", body)
