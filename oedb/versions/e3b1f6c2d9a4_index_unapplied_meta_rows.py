"""Add partial index on unapplied rows to all existing meta tables

Every write to a table is journaled in its meta tables
(_<name>_insert/_edit/_delete) and applied by scanning them with
``WHERE _applied = FALSE``. Without an index those scans are sequential
and grow with the journal, which slows every upload as tables age
(issue #2362). New meta tables get this index on creation; this
migration back-fills all existing ones. Meta tables are found via
postgres inheritance from public._edit_base.

How it runs, because production has one meta table per journaled write
type of every table and the platform keeps serving while this runs:

- One commit per index (alembic's autocommit block). Building all of
  them in the single transaction alembic would otherwise use holds two
  locks per meta table until the end - enough meta tables overflow
  Postgres' lock table ("out of shared memory") - and keeps every
  journal write-locked for the whole run.
- Not CONCURRENTLY: that waits for every older transaction in the
  database, and a connection left idle in a transaction would hang the
  deploy. A plain build locks only its own meta table, only while it
  builds.
- A meta table that stays locked for LOCK_TIMEOUT is skipped and
  reported, not fatal. Its index only speeds things up; the table works
  without it, and running this function again creates what is missing.

Revision ID: e3b1f6c2d9a4
Revises: 89f049e538aa
Create Date: 2026-07-03


SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import hashlib
import logging

from alembic import op
from sqlalchemy.exc import OperationalError

# revision identifiers, used by Alembic.
revision = "e3b1f6c2d9a4"
down_revision = "89f049e538aa"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

LOCK_TIMEOUT = "10s"

META_TABLES_QUERY = """
    SELECT n.nspname, c.relname
    FROM pg_inherits i
    JOIN pg_class c ON c.oid = i.inhrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_class p ON p.oid = i.inhparent
    JOIN pg_namespace pn ON pn.oid = p.relnamespace
    WHERE p.relname = '_edit_base' AND pn.nspname = 'public'
    ORDER BY n.nspname, c.relname
"""


def _index_name(table_name):
    # A frozen copy of oedb.utils.unapplied_index_name; a test keeps them equal.
    name = f"{table_name}_unapplied_idx"
    if len(name) <= 63:
        return name
    digest = hashlib.sha1(table_name.encode()).hexdigest()[:8]
    return f"{table_name[:46]}_{digest}_uidx"


def index_meta_tables(connection, lock_timeout=LOCK_TIMEOUT, schema=None):
    """Create the missing indexes, one statement (and commit) each.

    `connection` must be in autocommit mode. `schema` limits the run to one
    schema (the tests use their own). Returns the meta tables that were skipped
    because they stayed locked, as (schema, table) pairs.
    """
    connection.execute(f"SET lock_timeout = '{lock_timeout}'")
    skipped = []
    for table_schema, table in connection.execute(META_TABLES_QUERY).fetchall():
        if schema is not None and table_schema != schema:
            continue
        try:
            connection.execute(
                f'CREATE INDEX IF NOT EXISTS "{_index_name(table)}" '
                f'ON "{table_schema}"."{table}" (_id) WHERE _applied = FALSE;'
            )
        except OperationalError as error:
            if getattr(error.orig, "pgcode", None) != "55P03":  # lock_not_available
                raise
            skipped.append((table_schema, table))
    connection.execute("RESET lock_timeout")
    return skipped


def upgrade():
    with op.get_context().autocommit_block():
        skipped = index_meta_tables(op.get_bind())
    for schema, table in skipped:
        logger.warning(
            "No unapplied-rows index on %s.%s: it stayed locked for %s. "
            "Uploads to it work, only slower; rerun "
            "index_meta_tables from this migration to add it.",
            schema,
            table,
            LOCK_TIMEOUT,
        )


def downgrade():
    # One commit per index here too: dropping them all in one transaction
    # overflows the lock table just like creating them would.
    with op.get_context().autocommit_block():
        connection = op.get_bind()
        for schema, table in connection.execute(META_TABLES_QUERY).fetchall():
            connection.execute(
                f'DROP INDEX IF EXISTS "{schema}"."{_index_name(table)}";'
            )
