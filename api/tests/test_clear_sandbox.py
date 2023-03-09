from dataedit.management.commands.clear_sandbox import (
    SANDBOX_SCHEMA,
    clear_sandbox,
    get_sandbox_table_names_oedb,
    get_sandbox_tables_django,
)

from . import APITestCase


class TestCommandClearSandbox(APITestCase):
    test_schema = SANDBOX_SCHEMA

    def test_clear_sandbox(self):

        # create a test table with data
        # so that sandbox is not empty
        self.create_table(
            table="test_sandbox_table",
            schema=SANDBOX_SCHEMA,
            structure={"columns": [{"name": "id", "data_type": "bigint"}]},
            data=[{"id": 1}],
        )

        # check that sandbox is not empty
        self.assertTrue(len(get_sandbox_tables_django()) > 0)
        self.assertTrue(len(get_sandbox_table_names_oedb()) > 0)

        # run the management command
        clear_sandbox()

        # check that sandbox is empty
        self.assertTrue(len(get_sandbox_tables_django()) == 0)
        self.assertTrue(len(get_sandbox_table_names_oedb()) == 0)
