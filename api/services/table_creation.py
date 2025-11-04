from api import actions
from api.error import APIError
from api.services.permissions import assign_table_holder
from dataedit.models import Table
from login.models import myuser as User


class TableCreationOrchestrator:
    def create_table(
        self,
        table: str,
        user: User,
        is_sandbox: bool,
        column_definitions: list,
        constraints_definitions: list,
    ) -> Table:
        """Perform multiple actions to create table, cleanup if any step fails"""
        table_obj = None
        try:
            # create django table object
            table_obj = Table.objects.create(name=table, is_sandbox=is_sandbox)

            # assign creator permission holder
            assign_table_holder(user=user, table=table_obj)

            # create oedb main table
            actions._table_create(
                table_obj,
                column_definitions=column_definitions,
                constraints_definitions=constraints_definitions,
            )
        except Exception:
            if table_obj:
                # if anything goes wrong:
                # delete django object which will also automatically clean up
                # left over oedb tables
                table_obj.delete()
            raise APIError(f"Could not create table {table}")

        return table_obj
