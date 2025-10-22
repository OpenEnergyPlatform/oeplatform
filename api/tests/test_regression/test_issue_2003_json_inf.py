"""
SPDX-FileCopyrightText: 2025 Christisn Winger

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from api.tests import APITestCaseWithTable


class TestIssue2003JsonInf(APITestCaseWithTable):
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
        {"value": float("+inf")},
        {"value": float("-inf")},
        {"value": float("nan")},
    ]

    def test_issue_2003_json_inf(self):
        data = self.api_req(
            "get",
            path="rows/",
            exp_code=200,
        )
        raise Exception(data)
