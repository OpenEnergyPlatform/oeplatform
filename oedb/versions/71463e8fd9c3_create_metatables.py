"""create metatables

Revision ID: 71463e8fd9c3
Revises:
Create Date: 2017-09-18 17:48:59.971501


SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "71463e8fd9c3"
down_revision = "5c098aa81e2c"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "_edit_base",
        sa.Column("_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("_message", sa.String(500), nullable=True),
        sa.Column("_user", sa.String(50), nullable=False),
        sa.Column(
            "_submitted",
            sa.TIMESTAMP,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("_autocheck", sa.Boolean, nullable=False, default=False),
        sa.Column("_humancheck", sa.Boolean, nullable=False, default=False),
        sa.Column("_type", sa.String(8), nullable=False),
        sa.Column("_applied", sa.Boolean, nullable=False, default=False),
        keep_existing=True,
    )


def downgrade():
    op.drop_table("_edit_base")
