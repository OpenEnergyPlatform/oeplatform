"""Add partial index on unapplied rows to all existing meta tables

Every write to a table is journaled in its meta tables
(_<name>_insert/_edit/_delete) and applied by scanning them with
``WHERE _applied = FALSE``. Without an index those scans are sequential
and grow with the journal, which slows every upload as tables age
(issue #2362). New meta tables get this index on creation; this
migration back-fills all existing ones. Meta tables are found via
postgres inheritance from public._edit_base.

Revision ID: e3b1f6c2d9a4
Revises: 89f049e538aa
Create Date: 2026-07-03


SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from alembic import op

# revision identifiers, used by Alembic.
revision = "e3b1f6c2d9a4"
down_revision = "89f049e538aa"
branch_labels = None
depends_on = None

META_TABLES_QUERY = """
    SELECT n.nspname, c.relname
    FROM pg_inherits i
    JOIN pg_class c ON c.oid = i.inhrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_class p ON p.oid = i.inhparent
    JOIN pg_namespace pn ON pn.oid = p.relnamespace
    WHERE p.relname = '_edit_base' AND pn.nspname = 'public'
"""


def _index_name(table_name):
    # postgres truncates identifiers to 63 bytes; truncate explicitly so
    # the name matches what CREATE INDEX IF NOT EXISTS uses at runtime
    return f"{table_name}_unapplied_idx"[:63]


def upgrade():
    connection = op.get_bind()
    for schema, table in connection.execute(META_TABLES_QUERY).fetchall():
        connection.execute(
            f'CREATE INDEX IF NOT EXISTS "{_index_name(table)}" '
            f'ON "{schema}"."{table}" (_id) WHERE _applied = FALSE;'
        )


def downgrade():
    connection = op.get_bind()
    for schema, table in connection.execute(META_TABLES_QUERY).fetchall():
        connection.execute(f'DROP INDEX IF EXISTS "{schema}"."{_index_name(table)}";')
