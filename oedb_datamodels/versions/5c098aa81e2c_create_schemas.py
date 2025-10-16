"""create schemas

Revision ID: 5c098aa81e2c
Revises: 46fb02acc3b1
Create Date: 2017-11-23 15:53:57.716306

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from alembic import op

from oeplatform.securitysettings import SCHEMA_DATA, SCHEMA_DEFAULT_TEST_SANDBOX

# revision identifiers, used by Alembic.
revision = "5c098aa81e2c"
down_revision = "048215319c74"
branch_labels = None
depends_on = None


schemas = [SCHEMA_DATA, SCHEMA_DEFAULT_TEST_SANDBOX]


def upgrade():
    for s in schemas:
        op.execute("CREATE SCHEMA IF NOT EXISTS " + s)
    for s in schemas:
        op.execute("CREATE SCHEMA IF NOT EXISTS _" + s)


def downgrade():
    # don't delete schemas automatically
    pass
