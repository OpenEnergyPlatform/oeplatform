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
        if actions.has_table({"schema": schema, "table": table}):
            return
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
        schema_obj, _ = DBSchema.objects.get_or_create(name=schema_name)

        if actions.has_table({"schema": schema_name, "table": table_name}):
            raise APIError(f"Table {schema_name}.{table_name} already exists.", 409)

        physical_created = False
        metadata_created = False
        table_obj = None

        try:
            with transaction.atomic():
                self.oedb_svc.create(
                    schema_name, table_name, column_defs, constraint_defs
                )
                physical_created = True

                table_obj = self.django_svc.create(schema_obj, table_name)
                metadata_created = True

            return table_obj

        except Exception as e:
            self._cleanup(
                schema_name, table_name, schema_obj, physical_created, metadata_created
            )
            raise APIError(f"Could not create table {schema_name}.{table_name}: {e}")

    def _cleanup(
        self, schema_name, table_name, schema_obj, physical_created, metadata_created
    ):
        if physical_created:
            self.oedb_svc.drop(schema_name, table_name)
        if metadata_created:
            self.django_svc.delete(schema_obj, table_name)
