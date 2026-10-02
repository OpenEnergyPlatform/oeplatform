__license__ = """
SPDX-FileCopyrightText: Christian Winger
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations

# One statement per table, both set-based: production holds ~195,000 views, almost
# all of them duplicate "default" views the table page used to insert on every
# visit (#2217). The filters go first because Django's CASCADE runs in Python, not
# in the database, so a plain DELETE of a view that still has filters would fail.
#
# Per (table, type, name) the row kept is the one marked default, and among those
# (or if none is) the newest.
DOOMED_VIEWS = """
    SELECT id FROM (
        SELECT id, row_number() OVER (
            PARTITION BY "table", type, name
            ORDER BY is_default DESC, id DESC
        ) AS rank
        FROM dataedit_view
    ) ranked
    WHERE rank > 1
"""

# Django creates foreign keys DEFERRABLE INITIALLY DEFERRED, so each deleted view
# would leave an FK check pending until commit, and Postgres refuses the ALTER TABLE
# below while a table has pending trigger events. Checking immediately for the two
# deletes leaves nothing pending; deferral is restored afterwards.
REMOVE_DUPLICATE_VIEWS = [
    "SET CONSTRAINTS ALL IMMEDIATE;",
    f"DELETE FROM dataedit_filter WHERE view_id IN ({DOOMED_VIEWS});",
    f"DELETE FROM dataedit_view WHERE id IN ({DOOMED_VIEWS});",
    "SET CONSTRAINTS ALL DEFERRED;",
]


class Migration(migrations.Migration):
    dependencies = [
        ("dataedit", "0053_alter_bulkloadevent_status"),
    ]

    operations = [
        # Not reversible in content: the removed duplicates are gone. Reversing
        # only drops the constraint.
        migrations.RunSQL(REMOVE_DUPLICATE_VIEWS, migrations.RunSQL.noop),
        migrations.AlterUniqueTogether(
            name="view",
            unique_together={("table", "type", "name")},
        ),
    ]
