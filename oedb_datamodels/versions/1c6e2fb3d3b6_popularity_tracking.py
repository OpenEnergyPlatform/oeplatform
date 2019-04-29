"""Add columns to track popularity of tags

Revision ID: 1c6e2fb3d3b6
Revises: 6887c442bbee
Create Date: 2019-04-29 11:30:45.528110

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c6e2fb3d3b6'
down_revision = '6887c442bbee'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tags', sa.Column('usage_count', sa.BigInteger(), server_default='0', nullable=True))
    op.add_column('tags', sa.Column('usage_tracked_since', sa.DateTime(), server_default=sa.text('now()'), nullable=True))


def downgrade():
    op.drop_column('tags', 'usage_tracked_since')
    op.drop_column('tags', 'usage_count')
