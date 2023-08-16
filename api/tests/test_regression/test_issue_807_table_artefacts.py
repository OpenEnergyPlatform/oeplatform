"""Some api actions run `assert_permission`, which calls
DBTable.load(schema, table), which used get_or_create().

This caused the creation of an artefact entry in django tables.

"""
from api.actions import assert_permission
from api.connection import table_exists_in_django, table_exists_in_oedb
from api.tests import APITestCase
from oeplatform.settings import TEST_DRAFT_SCHEMA


class Test_issue_807_table_artefacts(APITestCase):
    schema = TEST_DRAFT_SCHEMA  # created in APITestCase
    table = "nonexisting_table"

    def test_issue_807_table_artefacts(self):
        try:
            assert_permission(
                user=self.user,  # created in APITestCase
                schema=self.schema,
                table=self.table,
                permission=0,  # any value will do
            )
        except Exception:
            pass

        self.assertFalse(table_exists_in_oedb(self.table, self.schema))
        # this failed before the bugfix
        self.assertFalse(table_exists_in_django(self.table, self.schema))
