"""Add _insert_base

Revision ID: 6887c442bbee
Revises: 3886946416ba
Create Date: 2019-04-25 16:09:20.572057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6887c442bbee"
down_revision = "3886946416ba"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "_insert_base",
        sa.Column("_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("_message", sa.Text(), nullable=True),
        sa.Column("_user", sa.String(length=50), nullable=True),
        sa.Column(
            "_submitted", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "_autocheck", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
        sa.Column(
            "_humancheck", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
        sa.Column("_type", sa.String(length=8), nullable=True),
        sa.Column(
            "_applied", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
        sa.PrimaryKeyConstraint("_id"),
        schema="public",
    )


def downgrade():
    op.drop_table("_insert_base", schema="public")
