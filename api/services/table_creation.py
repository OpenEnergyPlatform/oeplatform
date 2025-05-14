from django.db import transaction

from api import actions
from api.error import APIError
from dataedit.models import Schema as DBSchema
from dataedit.models import Table as DBTable


class DjangoTableService:
    def create(self, schema_obj, table_name):
        return DBTable.objects.create(name=table_name, schema=schema_obj)

    def delete(self, schema_obj, table_name):
        DBTable.objects.filter(name=table_name, schema=schema_obj).delete()


class OEDBTableService:
    def create(self, schema, table, columns, constraints):
        actions.table_create(schema, table, columns, constraints)

    def drop(self, schema, table):
        if not actions.has_table({"schema": schema, "table": table}):
            return

        real_schema, real_table = actions.get_table_name(schema, table)
        meta_schema = actions.get_meta_schema_name(real_schema)
        edit_table = actions.get_edit_table_name(real_schema, real_table)
        engine = actions._get_engine()

        # drop the revision table
        engine.execute(f'DROP TABLE "{meta_schema}"."{edit_table}" CASCADE;')
        # drop the actual data table
        engine.execute(f'DROP TABLE "{real_schema}"."{real_table}" CASCADE;')


class TableCreationOrchestrator:
    def __init__(self, django_svc=None, oedb_svc=None):
        self.django_svc = django_svc or DjangoTableService()
        self.oedb_svc = oedb_svc or OEDBTableService()

    def create_table(
        self,
        schema_name: str,
        table_name: str,
        column_defs: list,
        constraint_defs: list,
    ):
        # ensure the Django-side schema row exists
        schema_obj, _ = DBSchema.objects.get_or_create(name=schema_name)

        try:
            # both steps live inside one try/except
            with transaction.atomic():
                # 1) create the physical table first
                self.oedb_svc.create(
                    schema_name, table_name, column_defs, constraint_defs
                )

                # 2) only once the physical table is up, create our metadata row
                table_obj = self.django_svc.create(schema_obj, table_name)

        except Exception as e:
            # if anything failed above, drop whatever physical table was made
            self.oedb_svc.drop(schema_name, table_name)
            # the atomic block will have rolled back any DBTable row
            raise APIError(f"Could not create table {schema_name}.{table_name}: {e}")

        return table_obj
