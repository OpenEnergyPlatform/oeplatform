# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@gmail.com>
#
# SPDX-License-Identifier: MIT

"""Set defaults in meta table

Revision ID: 7dd42bf4925b
Revises: 96bafa638b4d
Create Date: 2019-11-26 16:49:42.862276

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7dd42bf4925b"
down_revision = "96bafa638b4d"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "_edit_base",
        "_autocheck",
        existing_type=sa.Boolean,
        server_default=sa.text("false"),
    )
    op.alter_column(
        "_edit_base",
        "_humancheck",
        existing_type=sa.Boolean,
        server_default=sa.text("false"),
    )
    op.alter_column(
        "_edit_base",
        "_applied",
        existing_type=sa.Boolean,
        server_default=sa.text("false"),
    )


def downgrade():
    op.alter_column(
        "_edit_base", "_autocheck", existing_type=sa.Boolean, server_default=None
    )
    op.alter_column(
        "_edit_base", "_humancheck", existing_type=sa.Boolean, server_default=None
    )
    op.alter_column(
        "_edit_base", "_applied", existing_type=sa.Boolean, server_default=None
    )
