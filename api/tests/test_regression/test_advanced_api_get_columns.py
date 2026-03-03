"""
SPDX-FileCopyrightText: 2025 Christisn Winger

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from api.tests import APITestCaseWithTable


class TestAdvancedApiGetColumns(APITestCaseWithTable):

    def test_advanced_api_get_columns(self):
        url = reverse("api:advanced-columns")
        resp = self.api_req(
            "post",
            url=url,
            data={"query": {"table": self.test_table}},
            exp_code=200,
        )
        assert resp  # this will always return json data
        self.assertTrue("columns" in resp["content"])
