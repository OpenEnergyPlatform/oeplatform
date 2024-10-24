from api import actions
from api.actions import has_table
from api.tests import APITestCase


class TestTableNameUnique(APITestCase):
    schema_sandbox = "sandbox"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        actions.perform_sql(f"DROP SCHEMA IF EXISTS {cls.schema_sandbox} CASCADE")
        actions.perform_sql(f"CREATE SCHEMA {cls.schema_sandbox}")
        actions.perform_sql(f"DROP SCHEMA IF EXISTS _{cls.schema_sandbox} CASCADE")
        actions.perform_sql(f"CREATE SCHEMA _{cls.schema_sandbox}")

    def test_tables_should_not_exists_on_error(self):
        test_duplicate_column_table_name = "table_column_duplicate"
        # create table with duplicated column names will should an error
        duplicate_field_error_data_struct = {
            "columns": [
                {"name": "id", "data_type": "bigint"},
                {"name": "id", "data_type": "bigint"},
            ]
        }
        # create table in default (test) schema (django_db)
        self.assertRaises(
            AssertionError,
            self.create_table,
            table=test_duplicate_column_table_name,
            structure=duplicate_field_error_data_struct,
            schema=self.schema_sandbox,
        )

        # also check: table should not have been created in oedb
        self.assertFalse(
            has_table(
                {
                    "table": test_duplicate_column_table_name,
                    "schema": self.schema_sandbox,
                }
            )
        )
