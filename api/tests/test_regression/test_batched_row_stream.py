"""A streamed read fetches its rows in batches, not one round trip per row.

`GET .../rows/` and the advanced API's streamed results read from a
server-side cursor, where every `fetchone()` is one `FETCH FORWARD 1` round
trip to the database. Measured against the OEDB in Docker: 5,726 rows/s one at
a time against 2,934,907 in batches of 2,000, and the endpoint as a whole at
5,242 rows/s, so about 92 % of a download was spent waiting for single rows.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

import psycopg2.extensions

from api import sessions
from api.tests import APITestCaseWithTable


class CountingCursor(psycopg2.extensions.cursor):
    """A cursor that counts the calls which can each be a round trip."""

    fetches = 0

    def fetchone(self):
        CountingCursor.fetches += 1
        return super().fetchone()

    def fetchmany(self, *args, **kwargs):
        CountingCursor.fetches += 1
        return super().fetchmany(*args, **kwargs)

    def fetchall(self):
        CountingCursor.fetches += 1
        return super().fetchall()


class BatchedRowStreamTest(APITestCaseWithTable):
    test_table = "batched_row_stream"
    test_data = [{"name": "row %03d" % i} for i in range(250)]

    def setUp(self):
        super().setUp()
        real = sessions.SessionContext.open_cursor
        raw_connections = []

        def counting(session, named=False):
            raw = session.connection.connection
            raw.cursor_factory = CountingCursor
            raw_connections.append(raw)
            return real(session, named=named)

        def restore():
            sessions.SessionContext.open_cursor = real
            # The connection goes back to the pool; the next user gets a plain one.
            for raw in raw_connections:
                raw.cursor_factory = psycopg2.extensions.cursor

        sessions.SessionContext.open_cursor = counting
        self.addCleanup(restore)
        CountingCursor.fetches = 0

    def test_a_download_reads_its_rows_in_batches(self):
        response = self.client.get(f"/api/v0/tables/{self.test_table}/rows/?orderby=id")
        self.assertEqual(200, response.status_code)
        rows = json.loads(b"".join(response.streaming_content))

        self.assertEqual([r["name"] for r in rows], [d["name"] for d in self.test_data])
        self.assertGreater(
            CountingCursor.fetches, 0, "the counting cursor was not used"
        )
        self.assertLess(
            CountingCursor.fetches,
            10,
            "250 rows took %d fetches: one round trip per row" % CountingCursor.fetches,
        )

    def test_a_csv_download_is_unchanged(self):
        response = self.client.get(
            f"/api/v0/tables/{self.test_table}/rows/?orderby=id&form=csv"
        )
        lines = b"".join(response.streaming_content).decode().splitlines()

        self.assertEqual(251, len(lines))
        self.assertTrue(lines[1].startswith('1,"row 000"'), lines[1])
        self.assertTrue(lines[-1].startswith('250,"row 249"'), lines[-1])
