"""Make message nullable

Revision ID: 4ce486182650
Revises: b4e662a73272
Create Date: 2019-04-30 09:04:34.330485

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4ce486182650"
down_revision = "b4e662a73272"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "_edit_base", "_message", existing_type=sa.VARCHAR(length=500), nullable=True
    )


def downgrade():
    op.alter_column(
        "_edit_base", "_message", existing_type=sa.VARCHAR(length=500), nullable=False
    )
