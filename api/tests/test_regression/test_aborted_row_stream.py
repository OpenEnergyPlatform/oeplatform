"""An aborted row stream gives its connection back when its response closes.

`GET .../rows/` streams through a server-side cursor on a connection of its
own, and the cursor, commit and close run only after the last row. A client
that stops reading never gets there: the server calls `close()` on the
response instead. The connection used to be closed in `OEPStream.__del__`,
but the response always sits in a reference cycle -- Django's
`request_finished` reaches an asgiref `Local` whose swallowed exception keeps
the closing frame alive, and DRF's view and request point at each other -- so
`__del__` ran only at the cyclic garbage collector's next full collection.
Until then the request kept its pool slot, its transaction, its snapshot and
a lock on the table, `idle in transaction` on `FETCH FORWARD 1`.

Measured on production: about 90 such aborts a day, some still holding their
connection 72 minutes later.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import gc

from api import sessions
from api.tests import APITestCaseWithTable
from oedb.connection import _get_engine


class AbortedRowStreamTest(APITestCaseWithTable):
    test_table = "aborted_row_stream"
    test_data = [{"name": "row %d" % i} for i in range(50)]

    def tearDown(self):
        # Without the fix the aborted stream still holds a lock on the table,
        # and the teardown's DROP would wait for it forever.
        gc.collect()
        super().tearDown()

    def artificial_sessions(self):
        return sum(1 for s in sessions._SESSION_CONTEXTS.values() if not s.counted)

    def fetching_backends(self):
        """Backends left mid-stream on a server-side cursor."""
        with _get_engine().connect() as connection:
            return connection.execute(
                "select count(*) from pg_stat_activity "
                "where datname = current_database() and pid <> pg_backend_pid() "
                "and state = 'idle in transaction' and query like 'FETCH%%'"
            ).scalar()

    def abort(self, form):
        """Read the start of a rows stream, then close it as a server does."""
        response = self.client.get(f"/api/v0/tables/{self.test_table}/rows/?{form}")
        self.assertEqual(200, response.status_code)
        body = response.streaming_content
        for _ in range(3):
            next(body)
        self.assertEqual(1, self.artificial_sessions(), "the stream is not running")
        # The test client's iterator closes the response when it is closed,
        # which is what a WSGI server does on an abort; `streaming_content`
        # itself is a fresh `map` over it and has no `close`.
        response._iterator.close()

    def assert_given_back(self, form):
        pool = _get_engine().pool
        checked_out = pool.checkedout()
        # Off for the whole exchange: the point is that nothing waits for it.
        gc.disable()
        try:
            self.abort(form)
            self.assertEqual(0, self.artificial_sessions())
            self.assertEqual(checked_out, pool.checkedout())
            self.assertEqual(0, self.fetching_backends())
        finally:
            gc.enable()

    def test_an_aborted_json_stream_gives_its_connection_back(self):
        self.assert_given_back("")

    def test_an_aborted_csv_stream_gives_its_connection_back(self):
        self.assert_given_back("form=csv")

    def test_an_aborted_datapackage_stream_gives_its_connection_back(self):
        self.assert_given_back("form=datapackage")
