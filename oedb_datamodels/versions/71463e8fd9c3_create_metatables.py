"""create metatables

Revision ID: 71463e8fd9c3
Revises: 
Create Date: 2017-09-18 17:48:59.971501

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from api.connection import _get_engine


# revision identifiers, used by Alembic.
revision = "71463e8fd9c3"
down_revision = "5c098aa81e2c"
branch_labels = None
depends_on = None

engine = _get_engine()


def upgrade():

    Session = sessionmaker(bind=engine)
    sess = Session()
    try:
        if not engine.dialect.has_table(sess, table_name="_edit_base"):
            op.create_table(
                "_edit_base",
                sa.Column("_id", sa.BigInteger, primary_key=True, autoincrement=True),
                sa.Column("_message", sa.String(500), nullable=True),
                sa.Column("_user", sa.String(50), nullable=False),
                sa.Column(
                    "_submitted",
                    sa.TIMESTAMP,
                    nullable=False,
                    server_default=sa.text("now()"),
                ),
                sa.Column("_autocheck", sa.Boolean, nullable=False, default=False),
                sa.Column("_humancheck", sa.Boolean, nullable=False, default=False),
                sa.Column("_type", sa.String(8), nullable=False),
                sa.Column("_applied", sa.Boolean, nullable=False, default=False),
                keep_existing=True,
            )
        sess.commit()
    except:
        sess.rollback()
        raise
    finally:
        sess.close()


def downgrade():
    op.drop_table("_edit_base")
