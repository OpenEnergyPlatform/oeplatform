import logging

from api.error import APIError
from api.parser import parse_table_parts
from api.services.permissions import assign_table_holder
from dataedit.models import Table
from login.models import myuser as User

logger = logging.getLogger("oeplatform")


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

        column_definitions, constraints_definitions = parse_table_parts(
            column_definitions=column_definitions,
            constraints_definitions=constraints_definitions,
        )

        table_obj = None

        try:
            # create django table object
            table_obj = Table.objects.create(name=table, is_sandbox=is_sandbox)

            # assign creator permission holder
            assign_table_holder(user=user, table=table_obj)

            # create oedb table
            otg = table_obj.get_oeb_table_group(user=user)
            otg.main_table._create(
                column_definitions=column_definitions,
                constraints_definitions=constraints_definitions,
            )

        except Exception as exc:
            logger.error(exc)
            if table_obj:
                # if anything goes wrong:
                # delete django object which will also automatically clean up
                # left over oedb tables
                table_obj.delete()
            raise APIError(f"Could not create table {table}")

        return table_obj
