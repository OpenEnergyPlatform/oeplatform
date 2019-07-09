import json
from api.tests import APITestCase


class Test270(APITestCase):
    def setUp(self):
        structure = {
            "constraints": [
                {
                    "constraint_type": "PRIMARY KEY",
                    "constraint_parameter": "id",
                    "reference_table": None,
                    "reference_column": None,
                }
            ],
            "columns": [
                {
                    "name": "id",
                    "data_type": "bigserial",
                    "is_nullable": False,
                    "character_maximum_length": None,
                },
                {
                    "name": "name",
                    "data_type": "character varying",
                    "is_nullable": True,
                    "character_maximum_length": 123,
                },
            ],
        }

        data = [{"name": "Hans"}, {"name": "Petra"}, {"name": "Dieter"}]

        self.create_table(structure, data=data)

    def test_270(self):
        self.check_api_get(
            "/api/v0/schema/{schema}/tables/{table}/rows/?where={where_1}&where={where_2}".format(
                where_1="name<>Hans",
                where_2="name<>Dieter",
                schema=self.test_schema,
                table=self.test_table,
            ),
            expected_result=[{"name": "Petra", "id": 2}],
        )

    def tearDown(self):
        self.drop_table()
