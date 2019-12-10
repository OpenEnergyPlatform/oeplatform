"""Add API constraints table

Revision ID: 96bafa638b4d
Revises: 4ce486182650
Create Date: 2019-11-26 15:33:05.377190

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96bafa638b4d'
down_revision = '4ce486182650'
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