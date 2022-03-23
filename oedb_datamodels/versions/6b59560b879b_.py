"""empty message

Revision ID: 3c2369dfcc55
Revises: 7dd42bf4925b
Create Date: 2022-01-27 10:12:56.713893

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3c2369dfcc55'
down_revision = '7dd42bf4925b'
branch_labels = None
depends_on = None

def upgrade():    
    # add new column name_normalized (allow nullable at first)
    op.add_column(
        table_name="tags",
        column=sa.Column("name_normalized", sa.String(length=40), nullable=True),
        schema="public",
    )               

    # create normalized names
    op.execute(
        """        
        -- create normalized names
        UPDATE public.tags
        SET name_normalized = TRIM(BOTH '_' FROM REGEXP_REPLACE(LOWER(name), '[^a-z0-9]+', '_', 'g'))
        ;

        -- create temporary column id_normalized
        ALTER TABLE public.tags ADD id_normalized BIGINT
        ;

        UPDATE public.tags t
        SET id_normalized = n.id_normalized
        FROM (
            SELECT name_normalized, MIN(id) AS id_normalized
            FROM public.tags
            GROUP BY name_normalized
        ) n
        WHERE n.name_normalized = t.name_normalized
        ;

        -- change tag usage
        -- !! changing ids could lead to duplicates which will cause an error
        -- so this is why the query is a little more complicated
        UPDATE public.table_tags tt
        SET tag = t.id_normalized
        FROM (
            SELECT
            tt.schema_name, tt.table_name, MIN(tt.tag) as tag, t.id_normalized
            FROM public.table_tags tt
            JOIN public.tags t
            ON tt.tag = t.id
            --> these three must be unique after the change
            GROUP BY tt.schema_name, tt.table_name, t.id_normalized
            HAVING MIN(t.id) != t.id_normalized
        ) t
        WHERE t.schema_name = tt.schema_name
        AND t.table_name = tt.table_name
        AND t.tag = tt.tag
        ;

        -- delete duplicates
        DELETE FROM public.table_tags tt
        WHERE tag IN
        (
            SELECT id 
            FROM public.tags
            WHERE id != id_normalized
            OR COALESCE(name_normalized, '') = ''
        )
        ;

        DELETE FROM public.tags
        WHERE id != id_normalized
        OR COALESCE(name_normalized, '') = ''
        ;


        -- drop temporary table
        ALTER TABLE public.tags DROP COLUMN id_normalized
        ;
        """
    )

    # change column to unique not null
    op.alter_column(
        table_name="tags",
        column_name="name_normalized",
        nullable=False,        
        schema="public",
    )
    op.create_unique_constraint(
        constraint_name="uq_name_normalized",
        table_name="tags",
        columns=["name_normalized"],        
        schema="public"
    )


def downgrade():
    op.drop_constraint(
        constraint_name="uq_name_normalized",
        table_name="tags",
        schema="public",
    )
    op.drop_column(
        table_name="tags",
        column_name="name_normalized",
        schema="public",
    )
