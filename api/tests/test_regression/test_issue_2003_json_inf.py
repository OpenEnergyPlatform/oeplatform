"""
SPDX-FileCopyrightText: 2025 Christisn Winger

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from api.tests import APITestCaseWithTable
from api.tests.utils import load_content


class TestIssue2003JsonInf(APITestCaseWithTable):
    test_table = "test_issue_2003_json_inf"
    test_structure = {
        "columns": [
            {
                "name": "value",
                "data_type": "float",
            }
        ]
    }
    # insert some json string data
    test_data = [
        {"value": 10},
        {"value": "+inf"},
        #    {"value": "-inf"},
        #    {"value": "nan"},
        #    {"value": "+Infinity"},
        #    {"value": "-Infinity"},
        #    {"value": "NaN"},
    ]

    def test_issue_2003_json_inf(self):
        data = {
            "query": {
                "from": {
                    "type": "table",
                    "table": self.test_table,
                },
                "fields": [
                    {"type": "column", "column": "value"},
                ],
            }
        }

        # url = reverse("api:advenced-search")
        ## don't use self.api_req so we can get raw response
        # resp = self.client.post(
        #    url, data=json.dumps(data), content_type="application/json"
        # )
        # print(resp.content)
        # print(json.loads(resp.content))
        # print(resp.json())

        # NOTE: cannot use regular client.get, because it automatically correctly converts
        # +Infinity etc.

        path = reverse(
            "api:api_rows",
            kwargs={"table": self.test_table, "schema": self.test_schema},
        )

        resp = self.client.get(path)
        print(load_content(resp))
