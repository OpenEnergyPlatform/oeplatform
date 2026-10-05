"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

What migration dataedit.0057 writes into ``Table.created`` (#2559).

``null=True`` does not keep ``AddField`` from filling the existing rows: for
an ``auto_now_add`` column Django's schema editor adds it with a DEFAULT of
the moment the migration runs (``sqlmigrate dataedit 0057`` shows it), so
every existing Table would read as created at the deploy. The migration's
``fill_created`` step therefore writes every row: ``date_updated`` above the
rollout line, NULL at or below it.

Like ``modelview/tests/test_delete_grace_migration.py`` this does not stand
up a migration-test framework. The step itself is run against Tables as
``AddField`` leaves them, every one stamped with one moment; a structural
check holds it after the ``AddField``.
"""  # noqa: 501

from datetime import datetime, timezone
from importlib import import_module

from django.apps import apps
from django.db import migrations
from django.test import SimpleTestCase, TestCase

from dataedit.models import Table


def _migration():
    # import_module: the module name starts with a digit
    return import_module("dataedit.migrations.0057_table_created")


def moment(*args):
    return datetime(*args, tzinfo=timezone.utc)


MIGRATION_RAN = moment(2026, 10, 20, 9, 0)


class FillCreatedTests(TestCase):
    def setUp(self):
        line = _migration().ROLLOUT_LINE
        # (id, date_updated) as production holds them: below the line a
        # date the metadata declared (midnight) or none, above it the
        # creation time
        self.tables = {
            line - 1: moment(2019, 5, 1),
            line: None,
            line + 16: moment(2025, 11, 5, 8, 47, 12, 345678),
            line + 900: moment(2026, 9, 30, 14, 2, 3, 4),
        }
        # bulk_create: Table.save() cannot take an explicit id
        Table.objects.bulk_create(Table(id=pk, name=f"t_{pk}") for pk in self.tables)
        for pk, date_updated in self.tables.items():
            # what AddField leaves behind: every row stamped alike
            Table.objects.filter(pk=pk).update(
                date_updated=date_updated, created=MIGRATION_RAN
            )
        _migration().fill_created(apps, None)

    def created(self, pk):
        return Table.objects.get(pk=pk).created

    def test_at_or_below_the_line_nothing_is_known(self):
        line = _migration().ROLLOUT_LINE
        self.assertIsNone(self.created(line - 1))
        self.assertIsNone(self.created(line))

    def test_above_the_line_date_updated_is_the_creation_time(self):
        line = _migration().ROLLOUT_LINE
        for pk in (line + 16, line + 900):
            self.assertEqual(self.created(pk), self.tables[pk])

    def test_no_row_keeps_the_moment_the_migration_ran(self):
        self.assertFalse(Table.objects.filter(created=MIGRATION_RAN).exists())

    def test_date_updated_is_untouched(self):
        for pk, date_updated in self.tables.items():
            self.assertEqual(Table.objects.get(pk=pk).date_updated, date_updated)


class MigrationShapeTests(SimpleTestCase):
    def test_the_line_is_the_measured_one(self):
        self.assertEqual(_migration().ROLLOUT_LINE, 69915)

    def test_every_row_is_written_after_the_column_is_added(self):
        operations = _migration().Migration.operations
        [add] = [
            i for i, op in enumerate(operations) if isinstance(op, migrations.AddField)
        ]
        fills = [
            i
            for i, op in enumerate(operations)
            if isinstance(op, migrations.RunPython)
            and op.code is _migration().fill_created
        ]
        self.assertTrue(
            fills,
            msg=(
                "Migration 0057 must write every row after adding `created`. "
                "Without it AddField stamps every existing Table with the "
                "moment the migration ran."
            ),
        )
        self.assertGreater(fills[0], add)
