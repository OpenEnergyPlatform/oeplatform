from api.tests import APITestCase


class TestAliasesTracking(APITestCase):
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

    def test_aliases_in_form_clauses(self):
        data = {
            "query": {
                "fields": [dict(type="column", column="id", table="a")],
                "where": [
                    {
                        "type": "operator",
                        "operator": "=",
                        "operands": [
                            {"type": "column", "column": "name", "table": "a"},
                            {"type": "value", "value": "Hans"},
                        ],
                    }
                ],
                "from": {
                    "type": "join",
                    "left": {
                        "type": "table",
                        "table": self.test_table,
                        "schema": self.test_schema,
                        "alias": "a",
                    },
                    "right": {
                        "type": "table",
                        "table": self.test_table,
                        "schema": self.test_schema,
                        "alias": "b",
                    },
                    "on": [
                        {
                            "type": "operator",
                            "operator": "=",
                            "operands": [
                                {"type": "column", "column": "id", "table": "a"},
                                {"type": "column", "column": "id", "table": "b"},
                            ],
                        }
                    ],
                },
            }
        }

        self.api_req("post", path="/advanced/search", data=data, exp_res=[[1]])

    def tearDown(self):
        self.api_req("delete")
