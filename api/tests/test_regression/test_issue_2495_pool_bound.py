"""The pool must not be able to exhaust the database.

The ceiling is per process and the database's is per cluster, and nothing in
this process can see how many processes there are. The shipped values allowed
200 connections per process against a `max_connections` of 255; with 13
mod_wsgi processes that is 2,600, and production reached the ceiling on
2026-09-10 and refused connections for twelve days.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import SimpleTestCase

from oedb.connection import OEDB_MAX_OVERFLOW, OEDB_POOL_SIZE
from oeplatform.settings import ANON_CONNECTION_LIMIT


class PoolIsBoundedTest(SimpleTestCase):
    """The ceiling is per process; the database's is per cluster.

    Production runs 13 mod_wsgi processes against `max_connections = 255` with
    8 reserved. Nothing in the process can see the 13, so the arithmetic is
    asserted here rather than left in a comment nobody re-checks.
    """

    PROCESSES = 13
    USABLE_CONNECTIONS = 255 - 8

    def test_the_pool_cannot_exhaust_the_database(self):
        per_process = OEDB_POOL_SIZE + OEDB_MAX_OVERFLOW
        worst_case = per_process * self.PROCESSES

        self.assertLess(
            worst_case,
            self.USABLE_CONNECTIONS,
            f"{self.PROCESSES} processes x {per_process} connections = {worst_case}, "
            f"which exceeds the {self.USABLE_CONNECTIONS} a client may hold",
        )

    def test_the_pool_is_actually_bounded(self):
        # pool_size=0 means unbounded retention for QueuePool, which is what
        # shipped and what let the pool climb to max_overflow and stay there
        self.assertGreater(OEDB_POOL_SIZE, 0)

    def test_a_burst_is_not_capped_below_the_thread_count(self):
        # mod_wsgi runs threads=15, so a smaller ceiling would make request
        # threads queue on the pool rather than on the database
        self.assertGreaterEqual(OEDB_MAX_OVERFLOW, 15)

    def test_the_anonymous_limit_fits_inside_the_pool(self):
        # above the pool ceiling the pool refuses first, with an opaque error,
        # instead of api/sessions.py refusing with its own explanatory message
        self.assertLessEqual(ANON_CONNECTION_LIMIT, OEDB_POOL_SIZE + OEDB_MAX_OVERFLOW)
