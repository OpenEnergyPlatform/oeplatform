from api.tests import APITestCase


class Test271(APITestCase):
    def setUp(self):
        self._structure_data = {
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

        self.api_req("put", data={"query": self._structure_data})
        self.api_req(
            "post",
            path="rows/new",
            data={"query": [{"name": "Hans"}, {"name": "Petra"}]},
            exp_code=201,
        )

    def test_271(self):
        data = {
            "query": {
                "fields": [dict(type="column", column="name")],
                "where": [
                    {
                        "type": "operator",
                        "operator": "=",
                        "operands": [
                            {"type": "column", "column": "name"},
                            {"type": "value", "value": "Hans"},
                        ],
                    }
                ],
                "from": {
                    "type": "table",
                    "table": self.test_table,
                    "schema": self.test_schema,
                },
            }
        }

        self.api_req("post", path="/advanced/search", data=data, exp_res=[["Hans"]])

    def test_271_column_does_not_exist(self):
        data = {
            "query": {
                "fields": [dict(type="column", column="does_not_exist")],
                "from": {
                    "type": "table",
                    "table": self.test_table,
                    "schema": self.test_schema,
                },
            }
        }

        json_resp = self.api_req(
            "post", path="/advanced/search", data=data, exp_code=400
        )
        self.assertEqual(json_resp["reason"], 'column "does_not_exist" does not exist')

    def tearDown(self):
        self.api_req("delete")
