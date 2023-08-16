"""ensure schemas

Revision ID: 4f01a68dcf6f
Revises: 3c2369dfcc55
Create Date: 2023-08-16 13:57:22.942292

"""
# import sqlalchemy as sa
from alembic import op

from oeplatform.settings import ALL_SCHEMAS

# revision identifiers, used by Alembic.
revision = "4f01a68dcf6f"
down_revision = "3c2369dfcc55"
branch_labels = None
depends_on = None


def upgrade():
    for s in ALL_SCHEMAS:
        op.execute("CREATE SCHEMA IF NOT EXISTS " + s)
    for s in ALL_SCHEMAS:
        op.execute("CREATE SCHEMA IF NOT EXISTS _" + s)


def downgrade():
    # do not delete schemas
    pass
