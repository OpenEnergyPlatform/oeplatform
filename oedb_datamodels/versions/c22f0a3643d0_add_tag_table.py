# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@gmail.com>
#
# SPDX-License-Identifier: MIT

"""Add tag table

Revision ID: c22f0a3643d0
Revises: 46fb02acc3b1
Create Date: 2019-04-25 14:23:13.389346

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c22f0a3643d0"
down_revision = "46fb02acc3b1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tags",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(length=40), nullable=True),
        sa.Column("color", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="tags_pkey"),
        schema="public",
    )


def downgrade():
    op.drop_table("tags", schema="public")
