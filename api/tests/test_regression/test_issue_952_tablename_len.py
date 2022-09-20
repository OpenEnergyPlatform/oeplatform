from functools import partial

from api.actions import MAX_IDENTIFIER_LENGTH
from api.tests import APITestCase


class TestTableNameLength(APITestCase):
    def test_table_name_length(self):
        structure = {"columns": [{"name": "id", "data_type": "bigint"}]}
        structure_bad = {
            "columns": [
                {"name": "id", "data_type": "bigint"},
                {"name": "BadName", "data_type": "bigint"},
            ]
        }
        table_ok = "t" + "_" * (MAX_IDENTIFIER_LENGTH - 1)
        table_too_long = "t" + "_" * (MAX_IDENTIFIER_LENGTH)
        table_bad_name = "table_Bad"

        # this should fail (too long table name)
        self.assertRaises(
            AssertionError,
            partial(self.create_table, structure, table=table_too_long),
        )

        # this should fail  (bad table name)
        self.assertRaises(
            AssertionError,
            partial(self.create_table, structure, table=table_bad_name),
        )

        # this should fail (bad column name)
        self.assertRaises(
            AssertionError,
            partial(self.create_table, structure_bad, table=table_ok),
        )

        # this works
        self.create_table(structure, table=table_ok)
