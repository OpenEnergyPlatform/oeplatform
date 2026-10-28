"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

A test run gets its own data database (OEDB), as it gets its own Django
database. Before, the tests wrote to the developer's configured OEDB:
``api.tests.test_clear_sandbox`` dropped every table in its sandbox schema,
including the dev container's example table, while the Table record in the
dev database survived with nothing behind it.
"""  # noqa: 501

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from oedb.connection import _get_engine
from oeplatform import settings
from oeplatform.oedb_for_tests import oedb_name_for_tests, running_tests
from oeplatform.runner import prepare_test_oedb


class TestDataDatabaseNameTests(SimpleTestCase):
    def test_the_name_is_derived_from_the_configured_one(self):
        self.assertEqual(oedb_name_for_tests("oedb", None), "test_oedb")
        self.assertEqual(oedb_name_for_tests("oedb", ""), "test_oedb")

    def test_an_explicit_name_wins(self):
        """Two sessions testing at once each name their own."""
        self.assertEqual(oedb_name_for_tests("oedb", "test_oedb_7"), "test_oedb_7")

    def test_a_test_run_is_recognised(self):
        self.assertTrue(running_tests(["manage.py", "test", "api"], {}))
        self.assertTrue(running_tests(["manage.py", "test"], {}))
        self.assertFalse(running_tests(["manage.py", "runserver"], {}))
        self.assertFalse(running_tests(["manage.py"], {}))
        # the runner's alembic subprocess is not "manage.py test" but must
        # migrate the same database
        self.assertTrue(
            running_tests(["alembic", "upgrade"], {"OEP_OEDB_FOR_TESTS": "1"})
        )


class TestDataDatabaseInUseTests(SimpleTestCase):
    def test_this_run_is_connected_to_its_own_data_database(self):
        self.assertEqual(settings.dbname, settings.OEDB_TEST_NAME)
        self.assertNotEqual(settings.dbname, settings.OEDB_CONFIGURED_NAME)
        self.assertEqual(_get_engine().url.database, settings.OEDB_TEST_NAME)

    def test_the_runner_never_prepares_the_configured_database(self):
        with self.assertRaises(ImproperlyConfigured):
            prepare_test_oedb(settings.OEDB_CONFIGURED_NAME)
