"""Add API constraints table

Revision ID: 96bafa638b4d
Revises: 4ce486182650
Create Date: 2019-11-26 15:33:05.377190


SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "96bafa638b4d"
down_revision = "4ce486182650"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_constraints",
        sa.Column("id", sa.BigInteger(), nullable=False, primary_key=True),
        sa.Column("action", sa.String(length=100)),
        sa.Column("constraint_type", sa.String(length=100)),
        sa.Column("constraint_name", sa.String(length=100)),
        sa.Column("constraint_parameter", sa.String(length=100)),
        sa.Column("reference_table", sa.String(length=100)),
        sa.Column("reference_column", sa.String(length=100)),
        sa.Column("c_schema", sa.String(length=100)),
        sa.Column("c_table", sa.String(length=100)),
        sa.Column("reviewed", sa.Boolean, default=False),
        sa.Column("changed", sa.Boolean, default=False),
        schema="public",
    )


def downgrade():
    op.drop_table("api_constraints", schema="public")
