"""add column category

SPDX-FileCopyrightText: 2025 wingechr
SPDX-License-Identifier: AGPL-3.0-or-later


Revision ID: 9f80bb4b215a
Revises: 4a999e7a3f93
Create Date: 2025-10-23 20:12:43.897144

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f80bb4b215a"
down_revision = "4a999e7a3f93"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="tags",
        column=sa.Column("category", sa.String(length=40), nullable=True),
        schema="public",
    )


def downgrade():
    op.drop_column(
        table_name="tags",
        column_name="category",
        schema="public",
    )
