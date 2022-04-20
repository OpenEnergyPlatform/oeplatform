from api.tests import APITestCase


class TestTableNameLength(APITestCase):
    def test_table_name_length(self):
        structure = {"columns": [{"name": "id", "data_type": "bigint"}]}
        data = [{"id": 1}]
        self.table60 = "t60" + "_" * 57
        self.table61 = "t61" + "_" * 58

        # this always works
        self.create_table(structure, table=self.table60, data=data)
        # insertion fails (before fix)
        self.create_table(structure, table=self.table61, data=data)
