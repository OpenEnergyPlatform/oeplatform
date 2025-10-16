from django.db import transaction

from api import actions
from api.error import APIError
from dataedit.models import Table as DBTable
from oeplatform.securitysettings import SCHEMA_DEFAULT_TEST_SANDBOX


class DjangoTableService:
    def create(self, table_name: str, is_sandbox: bool = True):
        return DBTable.objects.create(name=table_name, is_sandbox=is_sandbox)

    def delete(self, table_name: str):
        DBTable.objects.filter(name=table_name).delete()


class OEDBTableService:
    def create(self, schema_name: str, table_name: str, columns, constraints):
        if actions.has_table({"schema": schema_name, "table": table_name}):
            return
        actions.table_create(schema_name, table_name, columns, constraints)

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
        if actions.has_table({"schema": schema_name, "table": table_name}):
            raise APIError(f"Table {schema_name}.{table_name} already exists.", 409)

        physical_created = False
        metadata_created = False
        table_obj = None

        try:
            with transaction.atomic():
                self.oedb_svc.create(
                    schema_name=schema_name,
                    table_name=table_name,
                    columns=column_defs,
                    constraints=constraint_defs,
                )
                physical_created = True
                is_sandbox = schema_name == SCHEMA_DEFAULT_TEST_SANDBOX
                table_obj = self.django_svc.create(
                    table_name=table_name, is_sandbox=is_sandbox
                )
                metadata_created = True

            return table_obj

        except Exception as e:
            self._cleanup(
                schema_name=schema_name,
                table_name=table_name,
                physical_created=physical_created,
                metadata_created=metadata_created,
            )
            raise APIError(f"Could not create table {schema_name}.{table_name}: {e}")

    def _cleanup(self, schema_name, table_name, physical_created, metadata_created):
        if physical_created:
            self.oedb_svc.drop(schema_name, table_name)
        if metadata_created:
            self.django_svc.delete(table_name=table_name)
