from django.core.management.base import BaseCommand, CommandError
from sqlalchemy.orm.session import sessionmaker
from api.connection import _get_engine
from dataedit.models import Table
from dataedit.views import schema_whitelist
import sqlalchemy as sqla


class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        real_tables = {(schema, table_name) for schema in schema_whitelist
            for table_name in inspector.get_table_names(schema=schema) if schema in schema_whitelist}
        table_objects = {(t.schema.name, t.name) for t in Table.objects.all() if t.schema.name in schema_whitelist}
        for schema, table in table_objects.difference(real_tables):
            Table.objects.get(name=table, schema__name=schema).delete()
        for schema, table in real_tables.difference(table_objects):
            Table.objects.create(name=table, schema__name=schema)