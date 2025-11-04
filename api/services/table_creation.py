from api import actions
from api.error import APIError
from dataedit.models import Table


class TableCreationOrchestrator:
    def create_table(
        self,
        table: str,
        is_sandbox: bool,
        column_defs: list,
        constraint_defs: list,
    ) -> Table:

        table_obj = None
        try:
            table_obj = Table.objects.create(name=table, is_sandbox=is_sandbox)

            actions.table_create(
                table_obj.oedb_schema, table_obj.name, column_defs, constraint_defs
            )
        except Exception:
            if table_obj:
                # if anything goes wrong:
                # delete django object which will also automatically clean up
                # left over oedb tables
                table_obj.delete()
            raise APIError(f"Could not create table {table}")

        return table_obj
