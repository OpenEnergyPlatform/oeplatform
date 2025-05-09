# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@gmail.com>
# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@gmail.com>
#
# SPDX-License-Identifier: MIT

"""create schemas

Revision ID: 5c098aa81e2c
Revises: 46fb02acc3b1
Create Date: 2017-11-23 15:53:57.716306

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "5c098aa81e2c"
down_revision = "048215319c74"
branch_labels = None
depends_on = None

schemas = [
    "demand",
    "economy",
    "emission",
    "environment",
    "grid",
    "boundaries",
    "society",
    "supply",
    "scenario",
    "climate",
    "model_draft",
    "openstreetmap",
    "reference",
]


def upgrade():
    for s in schemas:
        op.execute("CREATE SCHEMA " + s)
    for s in schemas:
        op.execute("CREATE SCHEMA _" + s)


def downgrade():
    for s in schemas:
        op.execute("DROP SCHEMA _" + s + " CASCADE")
    for s in schemas:
        op.execute("DROP SCHEMA " + s + " CASCADE")
