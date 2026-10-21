"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Which data database (OEDB) a process uses when it runs the test suite.

A test run gets its own OEDB, as Django gives it its own Django database: the
configured name with ``test_`` in front, or ``LOCAL_TEST_DB_NAME`` when set
(two sessions testing at once give each run its own name). Without this, the
tests wrote to the developer's own OEDB, and ``test_clear_sandbox`` dropped
every table in its sandbox schema.

``oeplatform.settings`` reads this module while it is being imported, so it
imports nothing. ``oeplatform.test_runner`` creates and migrates the database.
"""  # noqa: 501

# Set by the test runner for the ``alembic upgrade`` subprocess that migrates
# the test OEDB: that process is not ``manage.py test``, but must connect to
# the same database.
FOR_TESTS_VARIABLE = "OEP_OEDB_FOR_TESTS"
TEST_NAME_VARIABLE = "LOCAL_TEST_DB_NAME"


def running_tests(argv, environ) -> bool:
    """Whether this process runs the test suite (or migrates its OEDB)."""
    return argv[1:2] == ["test"] or environ.get(FOR_TESTS_VARIABLE) == "1"


def oedb_name_for_tests(configured: str, override) -> str:
    """The OEDB a test run uses, for the configured name ``configured``."""
    return override or f"test_{configured}"
