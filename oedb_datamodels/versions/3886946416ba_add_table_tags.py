"""Add association between tags and labels

Revision ID: 3886946416ba
Revises: c22f0a3643d0
Create Date: 2019-04-25 15:43:17.074048

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3886946416ba"
down_revision = "c22f0a3643d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "table_tags",
        sa.Column("tag", sa.BigInteger(), nullable=False),
        sa.Column("schema_name", sa.String(length=100), nullable=False),
        sa.Column("table_name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["tag"], ["public.tags.id"]),
        sa.PrimaryKeyConstraint(
            "tag", "schema_name", "table_name", name="table_tags_pkey"
        ),
        schema="public",
    )


def downgrade():
    op.drop_table("table_tags", schema="public")
