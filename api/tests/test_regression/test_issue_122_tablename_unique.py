from api import actions
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

    def test_table_name_unique(self):
        # create table in default (test) schema
        self.create_table()

        # create same table in another (sandbox) schema
        # should fail
        self.assertRaises(AssertionError, self.create_table, schema=self.schema_sandbox)
