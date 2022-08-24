"""create schemas

Revision ID: 5c098aa81e2c
Revises: 46fb02acc3b1
Create Date: 2017-11-23 15:53:57.716306

"""
import sqlalchemy as sa
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
