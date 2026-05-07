"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

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
                        "alias": "a",
                    },
                    "right": {
                        "type": "table",
                        "table": self.test_table,
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
