import sqlalchemy as sqla
from django.core.management.base import BaseCommand
from django.db import transaction

from api.connection import _get_engine
from dataedit.models import Schema, Table
from dataedit.views import schema_whitelist
from api.actions import has_table
from oeplatform.settings import PLAYGROUNDS


class Command(BaseCommand):
    def handle(self, *args, **options):
        engine = _get_engine()
        inspector = sqla.inspect(engine)
        real_tables = {
            (schema, table_name)
            for schema in schema_whitelist
            for table_name in inspector.get_table_names(schema=schema)
            if schema in schema_whitelist
        }
        table_objects = {
            (t.schema.name, t.name)
            for t in Table.objects.all()
            if t.schema.name in schema_whitelist
        }
        for schema, table in table_objects.difference(real_tables):
            print(schema, table)
            Table.objects.get(name=table, schema__name=schema).delete()
        print("---")
        for schema, table in real_tables.difference(table_objects):
            print(schema, table)
            s, _ = Schema.objects.get_or_create(name=schema)
            t = Table(name=table, schema=s)
            t.save()

def migrate(check=True, verbose=True):
    def vprint(x):
        if verbose:
            print(x)
        else:
            return
    result = False
    if not check:
        answer = None
        while answer != "y":
            answer = input(
                "Warning! This opperation may alter your database. Continue only if you know possible implications! Continue (y/n)")
            if answer == "n":
                return False
    try:
        db_not_model = []
        with transaction.atomic():
            for table in Table.objects.all():
                if table.schema.name not in PLAYGROUNDS:
                    if not has_table(dict(schema=table.schema.name, table=table.name)):

                        if not check:
                            table.delete()
            if db_not_model:
                vprint("In model but not in database:")
                for t in db_not_model:
                    vprint(t)
            else:
                vprint("All models correspond to database tables :)")

            model_not_db = []
            engine = _get_engine()
            insp = sqla.inspect(engine)
            for schema in insp.get_schema_names():
                if schema in schema_whitelist and schema not in PLAYGROUNDS:
                    for table in insp.get_table_names(schema=schema):
                        try:
                            Table.objects.get(name=table, schema__name=schema)
                        except Table.DoesNotExist:
                            model_not_db.append((table.schema.name, table.name))
                            if not check:
                                table = Table.load(schema, table)
                                table.save()

            if model_not_db:
                vprint("In database but not in model:")
                for t in db_not_model:
                    vprint(t)
            else:
                vprint("All tables are reflected by models :)")
                if not db_not_model:
                    result = True

    except:
        print("An error occured during the migration of metadata")
        raise

    return result