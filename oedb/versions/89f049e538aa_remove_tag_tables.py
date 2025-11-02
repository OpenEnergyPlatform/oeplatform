"""remove tag tables

SPDX-FileCopyrightText: 2025 Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later


Revision ID: 89f049e538aa
Revises: 9f80bb4b215a
Create Date: 2025-10-24 11:53:31.660463

"""

import sqlalchemy as sa
from alembic import op

revision = "89f049e538aa"
down_revision = "9f80bb4b215a"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("table_tags", schema="public")
    op.drop_table("tags", schema="public")


def downgrade():
    op.create_table(
        "tags",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(length=40), nullable=True),
        sa.Column("color", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="tags_pkey"),
        schema="public",
    )
    op.create_table(
        "table_tags",
        sa.Column("tag", sa.BigInteger(), nullable=False),
        sa.Column("schema_name", sa.String(length=100), nullable=False),
        sa.Column("table_name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["tag"], ["public.tags.id"]),
        sa.PrimaryKeyConstraint(
            "tag", "schema_name", "table_name", name="table_tags_pkey"
        ),
        schema="public",
    )
