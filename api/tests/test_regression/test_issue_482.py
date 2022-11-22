from api.tests import APITestCaseWithTable


class TestAliasesTracking(APITestCaseWithTable):
    test_data = [{"name": "Hans"}, {"name": "Petra"}]

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
