"""
An "as" alias on a field in an advanced search request was parsed and then
discarded, so the response named the column after the expression instead of
after the alias.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api.tests import APITestCaseWithTable


class TestAdvancedApiFieldAlias(APITestCaseWithTable):
    test_data = [{"name": "Hans"}, {"name": "Petra"}]

    def _search(self, fields, exp_code=200):
        return self.api_req(
            "post",
            path="/advanced/search",
            data={
                "query": {
                    "fields": fields,
                    "from": {"type": "table", "table": self.test_table},
                }
            },
            exp_code=exp_code,
        )

    def _column_names(self, json_resp):
        return [col[0] for col in json_resp["description"]]

    def test_alias_on_function_field_names_the_column(self):
        json_resp = self._search(
            [
                {
                    "type": "function",
                    "function": "upper",
                    "operands": [{"type": "column", "column": "name"}],
                    "as": "shouted",
                }
            ]
        )

        self.assertEqual(["shouted"], self._column_names(json_resp))

    def test_alias_on_plain_column_field_names_the_column(self):
        json_resp = self._search([{"type": "column", "column": "name", "as": "who"}])

        self.assertEqual(["who"], self._column_names(json_resp))

    def test_explicit_label_expression_still_names_the_column(self):
        json_resp = self._search(
            [
                {
                    "type": "label",
                    "label": "shouted",
                    "element": {
                        "type": "function",
                        "function": "upper",
                        "operands": [{"type": "column", "column": "name"}],
                    },
                }
            ]
        )

        self.assertEqual(["shouted"], self._column_names(json_resp))

    def test_invalid_alias_is_rejected(self):
        json_resp = self._search(
            [{"type": "column", "column": "name", "as": 'not a "valid" id'}],
            exp_code=400,
        )

        self.assertIn("Invalid identifier", json_resp["reason"])
