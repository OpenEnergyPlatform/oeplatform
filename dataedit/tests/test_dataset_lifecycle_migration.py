"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

What migration dataedit.0058 writes into ``Dataset.published_at`` and
``Dataset.modified_at`` (#2618).

Every Dataset that exists when the lifecycle arrives was publicly listed, so
it is migrated as published, since its creation: ``published_at =
created_at``, never the moment of the deploy. ``modified_at`` stays NULL,
because nothing recorded a Modification before it existed.

Unlike ``dataedit.0057`` neither column is ``auto_now_add``, so ``sqlmigrate``
shows no DEFAULT on the ADD COLUMN; the test below still runs the step
against rows as ``AddField`` leaves them and holds it after the
``AddField``, as ``modelview/tests/test_delete_grace_migration.py`` does,
because a migration that has run cannot be replayed.
"""  # noqa: 501

from datetime import datetime, timezone
from importlib import import_module

from django.apps import apps
from django.db import migrations
from django.test import SimpleTestCase, TestCase

from dataedit.models import Dataset


def _migration():
    # import_module: the module name starts with a digit
    return import_module("dataedit.migrations.0058_dataset_lifecycle")


def moment(*args):
    return datetime(*args, tzinfo=timezone.utc)


class FillPublishedTests(TestCase):
    def setUp(self):
        self.created = {
            "old": moment(2025, 11, 3, 10, 0, 1, 2),
            "recent": moment(2026, 9, 30, 14, 2, 3, 4),
        }
        for name, created_at in self.created.items():
            dataset = Dataset.objects.create(name=name)
            # auto_now_add ignores a value passed to create()
            Dataset.objects.filter(pk=dataset.pk).update(created_at=created_at)
        # what AddField leaves behind: both columns NULL
        Dataset.objects.update(published_at=None, modified_at=None)
        _migration().fill_published(apps, None)

    def test_every_existing_dataset_is_published_since_its_creation(self):
        for name, created_at in self.created.items():
            self.assertEqual(
                Dataset.objects.get(name=name).published_at, created_at, msg=name
            )

    def test_nothing_is_modified(self):
        self.assertFalse(Dataset.objects.filter(modified_at__isnull=False).exists())


class MigrationStructureTests(SimpleTestCase):
    def operations(self):
        return _migration().Migration.operations

    def test_it_adds_both_columns_without_a_default(self):
        added = {
            op.name: op.field
            for op in self.operations()
            if isinstance(op, migrations.AddField)
        }

        self.assertEqual(set(added), {"published_at", "modified_at"})
        for name, field in added.items():
            # auto_now / auto_now_add would make the ADD COLUMN stamp every
            # existing row with the deploy time (the modelview.0066 trap)
            self.assertTrue(field.null, msg=name)
            self.assertFalse(getattr(field, "auto_now", False), msg=name)
            self.assertFalse(getattr(field, "auto_now_add", False), msg=name)

    def test_it_fills_published_at_after_adding_it(self):
        ops = self.operations()
        add = next(
            i
            for i, op in enumerate(ops)
            if isinstance(op, migrations.AddField) and op.name == "published_at"
        )
        fills = [
            i
            for i, op in enumerate(ops)
            if isinstance(op, migrations.RunPython)
            and op.code is _migration().fill_published
        ]

        self.assertTrue(
            fills,
            msg=(
                "Migration 0058 must fill published_at for existing Datasets. "
                "Without it every Dataset on the platform becomes a draft on "
                "deploy and drops out of every public reader."
            ),
        )
        self.assertGreater(fills[0], add)
