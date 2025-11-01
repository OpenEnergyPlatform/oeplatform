from django.db import transaction

from api import actions
from api.error import APIError
from dataedit.models import Table as DBTable
from oedb.connection import _get_engine
from oeplatform.settings import IS_SANDBOX, SCHEMA_DEFAULT_TEST_SANDBOX


class DjangoTableService:
    def create(self, table: str, is_sandbox: bool = IS_SANDBOX):
        return DBTable.objects.create(name=table, is_sandbox=is_sandbox)

    def delete(self, table: str):
        DBTable.objects.filter(name=table).delete()


class OEDBTableService:
    def create(self, schema: str, table: str, columns, constraints):
        if actions.has_table({"schema": schema, "table": table}):
            return
        actions.table_create(schema, table, columns, constraints)

    def drop(self, schema, table):
        try:
            real_schema, real_table = actions.get_table_name(schema, table)
        except Exception:
            # does not exist
            return
        meta_schema = actions.get_meta_schema_name(real_schema)

        edit_table = actions.get_edit_table_name(real_schema, real_table)
        insert_table = actions.get_insert_table_name(real_schema, real_table)
        delete_table = actions.get_delete_table_name(real_schema, real_table)

        engine = _get_engine()

        # drop the revision tables
        engine.execute(f'DROP TABLE IF EXISTS "{meta_schema}"."{edit_table}" CASCADE;')
        engine.execute(
            f'DROP TABLE IF EXISTS "{meta_schema}"."{insert_table}" CASCADE;'
        )
        engine.execute(
            f'DROP TABLE IF EXISTS "{meta_schema}"."{delete_table}" CASCADE;'
        )

        # drop the actual data table
        engine.execute(f'DROP TABLE IF EXISTS "{real_schema}"."{real_table}" CASCADE;')


class TableCreationOrchestrator:
    def __init__(self, django_svc=None, oedb_svc=None):
        self.django_svc = django_svc or DjangoTableService()
        self.oedb_svc = oedb_svc or OEDBTableService()

    def create_table(
        self,
        schema: str,
        table: str,
        column_defs: list,
        constraint_defs: list,
    ):
        if actions.has_table({"schema": schema, "table": table}):
            raise APIError(f"Table {schema}.{table} already exists.", 409)

        physical_created = False
        metadata_created = False
        table_obj = None

        try:
            with transaction.atomic():
                self.oedb_svc.create(
                    schema=schema,
                    table=table,
                    columns=column_defs,
                    constraints=constraint_defs,
                )
                physical_created = True
                is_sandbox = schema == SCHEMA_DEFAULT_TEST_SANDBOX
                table_obj = self.django_svc.create(table=table, is_sandbox=is_sandbox)
                metadata_created = True

            return table_obj

        except Exception as e:
            self._cleanup(
                schema=schema,
                table=table,
                physical_created=physical_created,
                metadata_created=metadata_created,
            )
            raise APIError(f"Could not create table {schema}.{table}: {e}")

    def _cleanup(self, schema, table, physical_created, metadata_created):
        if physical_created:
            self.oedb_svc.drop(schema, table)
        if metadata_created:
            self.django_svc.delete(table=table)

    def drop_table(self, schema, table):
        self.oedb_svc.drop(schema, table)
        self.django_svc.delete(table=table)
