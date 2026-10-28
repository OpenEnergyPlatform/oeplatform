"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

``create_example_tables``, which the dev container runs on every start. It
must leave one complete example table behind however often it runs and
whatever state an earlier run (or a test run) left: the record, the table in
the schema the record names, its rows and its metadata.
"""  # noqa: 501

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from sqlalchemy import text

from api.actions import _get_engine
from dataedit.management.commands.create_example_tables import (
    CSV_FILE,
    EXAMPLE_TABLE,
)
from dataedit.models import Table

CSV_ROWS = sum(1 for _ in open(CSV_FILE, encoding="utf-8")) - 1


class CreateExampleTablesTests(TestCase):
    def setUp(self):
        self._drop_physical()

    def tearDown(self):
        self._drop_physical()

    def _drop_physical(self):
        proxy = Table(name=EXAMPLE_TABLE, is_sandbox=True)
        proxy.drop_oedb_table()

    def run_command(self):
        out, err = StringIO(), StringIO()
        call_command("create_example_tables", stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    def rows(self, table):
        with _get_engine().connect() as connection:
            return connection.execute(
                text(f'SELECT count(*) FROM "{table.oedb_schema}"."{table.name}"')
            ).scalar()

    def assert_complete(self):
        table = Table.objects.get(name=EXAMPLE_TABLE)
        self.assertTrue(table.get_oedb_table_proxy().exists())
        self.assertEqual(self.rows(table), CSV_ROWS)
        self.assertTrue(table.oemetadata)
        fields = table.oemetadata["resources"][0]["schema"]["fields"]
        self.assertIn("technology", [field["name"] for field in fields])
        return table

    def test_a_fresh_run_leaves_a_complete_table(self):
        out, err = self.run_command()
        self.assertEqual(err, "")
        table = self.assert_complete()
        # the messages name the schema the table is really in
        self.assertIn(f"{table.oedb_schema}.{EXAMPLE_TABLE}", out)
        self.assertGreater(CSV_ROWS, 0)

    def test_running_again_changes_nothing_and_reports_no_error(self):
        self.run_command()
        out, err = self.run_command()
        self.assertEqual(err, "")
        self.assertEqual(Table.objects.filter(name=EXAMPLE_TABLE).count(), 1)
        self.assert_complete()
        self.assertIn("already exists", out)

    def test_a_record_whose_table_has_gone_is_repaired(self):
        """What a test run's ``clear_sandbox`` used to leave in the dev
        database: the record, with no table behind it."""
        self.run_command()
        self._drop_physical()
        out, err = self.run_command()
        self.assertEqual(err, "")
        self.assert_complete()
        self.assertIn("has no table", out)

    def test_a_table_without_its_record_is_replaced(self):
        self.run_command()
        Table.objects.get(name=EXAMPLE_TABLE).delete_record()
        out, err = self.run_command()
        self.assertEqual(err, "")
        self.assert_complete()
