"""The safeguard in migration 0066, which cannot be re-run to be tested.

`null=True` does not keep `AddField` from filling existing rows: Django's
schema editor special-cases `auto_now`/`auto_now_add` in `_effective_default`
and writes the moment the migration runs into every one of them. Measured on a
real database -- the first run of 0066 gave every pre-existing factsheet a
`created` equal to the migration's own timestamp, which would have opened all
339 of them to deletion by any logged-in account for a week after the deploy.

The migration therefore clears the column explicitly. This file guards that
step. It is structural rather than behavioural on purpose: the migration has
already run everywhere it matters and cannot be replayed, and this app follows
the convention set in `dataedit/tests/test_migrations.py` of not standing up a
migration-test framework. What it can still catch is somebody reading the
`RunSQL` as redundant and deleting it.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

from importlib import import_module

from django.db import migrations
from django.test import SimpleTestCase


def _operations():
    """The migration's operations, imported by name.

    `import_module` rather than an import statement: the module name starts
    with a digit, so it is not a legal identifier.
    """
    module = import_module("modelview.migrations.0066_basicfactsheet_created")
    return module.Migration.operations


class TestTheGracePeriodMigration(SimpleTestCase):

    def test_it_adds_the_column(self):
        added = [op for op in _operations() if isinstance(op, migrations.AddField)]

        self.assertEqual(len(added), 1)
        self.assertEqual(added[0].name, "created")

    def test_it_clears_the_column_after_adding_it(self):
        ops = _operations()
        add = next(i for i, op in enumerate(ops) if isinstance(op, migrations.AddField))
        clears = [
            i
            for i, op in enumerate(ops)
            if isinstance(op, migrations.RunSQL) and "created = NULL" in str(op.sql)
        ]

        self.assertTrue(
            clears,
            msg=(
                "Migration 0066 must clear `created` after adding it. Without "
                "it every pre-existing factsheet is stamped with the migration "
                "time and falls inside the delete grace period."
            ),
        )
        self.assertGreater(clears[0], add)
