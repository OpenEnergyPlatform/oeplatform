"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api.tests import APITestCaseWithTable


class Test271(APITestCaseWithTable):
    test_data = [{"name": "Hans"}, {"name": "Petra"}]

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
                },
            }
        }

        json_resp = self.api_req(
            "post", path="/advanced/search", data=data, exp_code=400
        )
        self.assertEqual(json_resp["reason"], 'column "does_not_exist" does not exist')
