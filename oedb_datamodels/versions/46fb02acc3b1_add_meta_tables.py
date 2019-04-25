"""Add meta tables

Revision ID: 46fb02acc3b1
Revises: 
Create Date: 2017-11-23 11:08:50.199160

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '46fb02acc3b1'
down_revision = '71463e8fd9c3'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        'api_columns',
        sa.Column('column_name', sa.String(50)),
        sa.Column('not_null', sa.Boolean),
        sa.Column('data_type', sa.String(50)),
        sa.Column('new_name', sa.String(50)),
        sa.Column('reviewed', sa.Boolean, default=False),
        sa.Column('changed', sa.Boolean, default=False),
        sa.Column('id', sa.BigInteger, nullable=False, primary_key=True),
        sa.Column('c_schema', sa.String(50)),
        sa.Column('c_table', sa.String(50))
    )

def downgrade():
    op.drop_table('api_columns')
