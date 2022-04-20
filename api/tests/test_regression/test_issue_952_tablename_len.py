from functools import partial
from api.tests import APITestCase
from api.actions import MAX_TABLE_NAME_LENGTH


class TestTableNameLength(APITestCase):
    def test_table_name_length(self):
        structure = {"columns": [{"name": "id", "data_type": "bigint"}]}
        data = [{"id": 1}]
        self.table_ok = "t" + "_" * (MAX_TABLE_NAME_LENGTH - 1)
        self.table_too_long = "t" + "_" * (MAX_TABLE_NAME_LENGTH)

        # this works
        self.create_table(structure, table=self.table_ok, data=data)

        # this should fail
        self.assertRaises(
            AssertionError,
            partial(self.create_table, structure, table=self.table_too_long, data=data),
        )
