"""
SPDX-FileCopyrightText: 2025 Christisn Winger

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import unittest

from django.urls import reverse

from api.tests import APITestCaseWithTable


class TestIssue2041SortJson(APITestCaseWithTable):
    "ordering by json column in advanced search fails"

    column_json = "column_json"
    test_structure = {
        "columns": [
            {
                "name": column_json,
                "data_type": "json",
            }
        ]
    }
    # insert some json string data
    test_data = [{column_json: {"x": 1}}, {column_json: {"x": "xyz"}}]

    @unittest.skip("we leave it unfixed for now and display error message in frontend")
    def test_issue_2041_sort_json(self):
        url = reverse("api:advanced-search")
        # {'reason': 'could not identify an ordering operator for type json'}
        self.api_req(
            "post",
            url=url,
            data={
                "query": {
                    "from": {
                        "type": "table",
                        "table": self.test_table,
                    },
                    "order_by": [
                        {
                            "type": "column",
                            "column": self.column_json,
                            "ordering": "asc",
                        }
                    ],
                    "fields": [
                        {"type": "column", "column": self.column_json},
                    ],
                    "offset": 0,
                    "limit": 10,
                }
            },
            # NOTE: we leave it infixed for now
            exp_code=200,
        )
