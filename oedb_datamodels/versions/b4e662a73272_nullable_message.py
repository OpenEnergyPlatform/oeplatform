"""Make message nullable

Revision ID: b4e662a73272
Revises: 1a73867b1e79
Create Date: 2019-04-30 09:04:34.330485

"""
from alembic import op
import sqlalchemy as sa


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
