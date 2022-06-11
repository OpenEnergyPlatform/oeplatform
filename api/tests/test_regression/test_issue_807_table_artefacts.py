"""Some api actions run `assert_permission`, which calls 
DBTable.load(schema, table), which used get_or_create().

This caused the creation of an artefact entry in django tables.

"""
from api.tests import APITestCase
from api.connection import table_exists_in_oedb
from api.actions import assert_permission

class Test_issue_807_table_artefacts(APITestCase):
    schema = "test" # created in APITestCase
    table = "nonexisting_table"

    def test_issue_807_table_artefacts(self):
        try:
            assert_permission(
                user=self.user, # created in APITestCase
                schema=self.schema,
                table=self.table,
                permission=0 # any value will do
            )
        except Exception:
            pass
        self.assertTrue(table_exists_in_oedb(self.table, self.schema))