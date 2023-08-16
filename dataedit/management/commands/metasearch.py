import sqlalchemy as sqla
from django.core.management.base import BaseCommand

from api.actions import update_meta_search
from api.connection import _get_engine
from dataedit.views import get_schema_whitelist


class Command(BaseCommand):
    def handle(self, *args, **options):
        schema_whitelist = get_schema_whitelist()
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        for schema in schema_whitelist:
            for table_name in inspector.get_table_names(schema=schema):
                update_meta_search(table_name, schema)
