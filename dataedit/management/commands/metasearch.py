from django.core.management.base import BaseCommand, CommandError
from sqlalchemy.orm.session import sessionmaker
from api.connection import _get_engine
from api.actions import update_meta_search
from dataedit.views import schema_whitelist
import sqlalchemy as sqla

class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        for schema in schema_whitelist:
            for table_name in inspector.get_table_names(schema=schema):
                update_meta_search(table_name, schema)