"""drop table meta search

Revision ID: 4a999e7a3f93
Revises: 3c2369dfcc55
Create Date: 2025-10-17 16:23:49.731335

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later

"""  # noqa: 501

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "4a999e7a3f93"
down_revision = "3c2369dfcc55"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("meta_search", schema="public")


def downgrade():
    op.create_table(
        "meta_search",
        sa.Column("schema", sa.String(length=100), nullable=False),
        sa.Column("table", sa.String(length=100), nullable=False),
        sa.Column("comment", postgresql.TSVECTOR(), nullable=True),
        sa.PrimaryKeyConstraint("schema", "table"),
        schema="public",
    )
