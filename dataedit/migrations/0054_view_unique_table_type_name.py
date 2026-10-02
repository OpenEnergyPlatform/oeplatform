__license__ = """
SPDX-FileCopyrightText: Christian Winger
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations

# Production holds ~195,000 saved views, almost all of them empty "default" table
# views the table page used to insert on every visit (#2217). Before the unique
# constraint on (table, type, name) can exist, each such group must be one row.
#
# Nothing a user saved may be lost. A view has content if it carries filters or
# options. Per group:
#   1. empty copies go: all of them if the group has a view with content, else
#      all but one (the one marked default, else the newest);
#   2. views with content that still share a name are renamed "name (id)" -
#      except one, which keeps the name (again: marked default, else newest).
# Step 1 only deletes views without filters, so no filter is ever deleted.

# Taken first: the previous release keeps serving pages while this runs and
# inserts a view per visit. One inserted between the cleanup and the ALTER would
# make the unique index fail and roll everything back. This lock blocks writes
# (reads go on) until the migration's transaction ends.
LOCK = "LOCK TABLE dataedit_view IN SHARE ROW EXCLUSIVE MODE;"

# Django creates foreign keys DEFERRABLE INITIALLY DEFERRED, so each deleted view
# would leave an FK check pending until commit, and Postgres refuses the ALTER
# TABLE below while a table has pending trigger events. Checking immediately
# leaves nothing pending.
CHECK_IMMEDIATELY = "SET CONSTRAINTS ALL IMMEDIATE;"

DELETE_EMPTY_COPIES = """
DELETE FROM dataedit_view WHERE id IN (
    SELECT id FROM (
        SELECT
            id,
            has_content,
            bool_or(has_content) OVER (PARTITION BY "table", type, name)
                AS group_has_content,
            row_number() OVER (
                PARTITION BY "table", type, name, has_content
                ORDER BY is_default DESC, id DESC
            ) AS rank
        FROM (
            SELECT
                v.id, v."table", v.type, v.name, v.is_default,
                coalesce(v.options, '{}'::jsonb) NOT IN ('{}'::jsonb, 'null'::jsonb)
                OR EXISTS (SELECT 1 FROM dataedit_filter f WHERE f.view_id = v.id)
                    AS has_content
            FROM dataedit_view v
        ) flagged
    ) ranked
    WHERE NOT has_content AND (group_has_content OR rank > 1)
);
"""

# name is varchar(50): cut the name so that the suffix always fits
RENAME_COLLISIONS = """
UPDATE dataedit_view v
SET name = left(v.name, 50 - length(' (' || v.id || ')')) || ' (' || v.id || ')'
FROM (
    SELECT id, row_number() OVER (
        PARTITION BY "table", type, name ORDER BY is_default DESC, id DESC
    ) AS rank
    FROM dataedit_view
) ranked
WHERE v.id = ranked.id AND ranked.rank > 1;
"""

REMOVE_DUPLICATE_VIEWS = [
    LOCK,
    CHECK_IMMEDIATELY,
    DELETE_EMPTY_COPIES,
    RENAME_COLLISIONS,
]


class Migration(migrations.Migration):
    dependencies = [
        ("dataedit", "0053_alter_bulkloadevent_status"),
    ]

    operations = [
        # Not reversible in content: the removed copies are gone and renamed
        # views keep their new names. Reversing only drops the constraint.
        migrations.RunSQL(REMOVE_DUPLICATE_VIEWS, migrations.RunSQL.noop),
        migrations.AlterUniqueTogether(
            name="view",
            unique_together={("table", "type", "name")},
        ),
    ]
