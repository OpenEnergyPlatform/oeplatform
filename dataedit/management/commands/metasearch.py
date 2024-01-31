import sqlalchemy as sqla
from django.core.management.base import BaseCommand

from api.actions import update_meta_search
from api.connection import _get_engine
from oeplatform.settings import SCHEMA_WHITELIST


class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        for schema in SCHEMA_WHITELIST:
            for table_name in inspector.get_table_names(schema=schema):
                update_meta_search(table_name, schema)
