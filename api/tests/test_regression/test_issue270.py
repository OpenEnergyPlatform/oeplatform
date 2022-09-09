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
        self.api_req(
            "get",
            path="rows/?where=name<>Hans&where=name<>Dieter",
            exp_res=[{"name": "Petra", "id": 2}],
        )

    def tearDown(self):
        self.drop_table()
