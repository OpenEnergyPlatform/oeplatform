from django.core.management.base import BaseCommand, CommandError
from sqlalchemy.orm.session import sessionmaker
from api.connection import _get_engine
from api.actions import update_meta_search
from dataedit.views import schema_whitelist
import sqlalchemy as sqla


class Command(BaseCommand):
    def handle(self, *args, **options):
        Session = sessionmaker()
        engine = _get_engine()
        conn = engine.connect()
        session = Session(bind=conn)
        meta = sqla.MetaData(bind=conn)
        meta.reflect()

        from sqlalchemy import inspect
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()

        try:
            for schema in schemas:
                if schema in schema_whitelist:
                    for table_name in inspector.get_table_names(schema=schema):
                        update_meta_search(session, table_name, schema)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()