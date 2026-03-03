"""Make message nullable

Revision ID: b4e662a73272
Revises: 1a73867b1e79
Create Date: 2019-04-30 09:04:34.330485

SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4e662a73272"
down_revision = "1a73867b1e79"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "_edit_base", "_message", existing_type=sa.VARCHAR(length=500), nullable=False
    )


def downgrade():
    op.alter_column(
        "_edit_base", "_message", existing_type=sa.VARCHAR(length=500), nullable=True
    )
