"""A pooled OEDB connection the server has already closed must not reach a
request.

The pool discards a connection for being old (`pool_recycle`) but not for
being dead, so before `pool_pre_ping` the next checkout after Postgres or the
network dropped a connection handed out the corpse. psycopg2 raised, the
catch-all in `api.helper.api_exception` turned that into
`400 {"reason": "Invalid request"}`, and the retry succeeded because
SQLAlchemy had meanwhile invalidated the connection -- which is what made it
read as a flaky table page rather than as a defect.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

import psycopg2

from api.tests import APITestCaseWithTable
from oedb.connection import _get_engine
from oeplatform.settings import dbhost, dbname, dbpasswd, dbport, dbuser

COUNT_QUERY = {
    "fields": [{"type": "function", "function": "count", "operands": ["*"]}],
}


class StalePooledConnectionTest(APITestCaseWithTable):
    test_table = "stale_pooled_connection"

    def _search(self):
        """POST the count query the table page sends, and read the body.

        A success streams, a refusal does not, so which attribute carries the
        body is itself part of what this asserts.
        """
        query = dict(
            COUNT_QUERY, **{"from": {"type": "table", "table": self.test_table}}
        )
        response = self.client.post(
            "/api/v0/advanced/search",
            data=json.dumps({"query": query}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Token %s" % self.token,
        )
        if hasattr(response, "streaming_content"):
            body = b"".join(response.streaming_content).decode()
        else:
            body = response.content.decode()
        return response.status_code, body

    def _sole_pooled_backend_pid(self):
        """Leave exactly one connection in the pool and return its backend pid.

        `dispose()` first, because the pool is process-wide and whatever else
        has run in this process leaves connections in it -- kill one of those
        and the request under test is handed a healthy one instead, so the
        test passes while proving nothing.
        """
        engine = _get_engine()
        engine.dispose()
        raw = engine.raw_connection()
        try:
            cursor = raw.cursor()
            cursor.execute("select pg_backend_pid()")
            pid = cursor.fetchone()[0]
            cursor.close()
        finally:
            raw.close()
        return pid

    def _terminate(self, pid):
        """Kill one backend from outside the pool.

        Deliberately not `pg_terminate_backend` over every connection to this
        database: the OEDB is a real local database, not a throwaway test one,
        so a second test run on the same machine would be collateral.
        """
        conn = psycopg2.connect(
            dbname=dbname, user=dbuser, password=dbpasswd, host=dbhost, port=dbport
        )
        try:
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("select pg_terminate_backend(%s)", (pid,))
            cursor.close()
        finally:
            conn.close()

    def test_a_search_survives_its_pooled_connection_being_killed(self):
        status_code, body = self._search()
        self.assertEqual(200, status_code, body)

        self._terminate(self._sole_pooled_backend_pid())

        status_code, body = self._search()
        self.assertEqual(
            200,
            status_code,
            "a killed pooled connection reached the request instead of being "
            "replaced at checkout: %s" % body,
        )
        self.assertNotIn("Invalid request", body)
