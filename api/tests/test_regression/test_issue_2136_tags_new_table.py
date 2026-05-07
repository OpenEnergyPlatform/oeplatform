"""
SPDX-FileCopyrightText: 2025 Christisn Winger

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from api.tests import APITestCaseWithTable
from dataedit.models import Table, Tag


class TestIssue2136TagsNewTable(APITestCaseWithTable):
    def test_issue_2136_tags_new_table(self):
        # table already created, now create tag
        tag = Tag.objects.create(name="testtag")
        # add view dataedit
        self.client.force_login(self.user)
        url = reverse("dataedit:tags-add")
        resp = self.client.post(
            url,
            data={
                "table": self.test_table,
                # NOTE: weirdly, adding tags is done by adding tag_<pk> field
                f"tag_{tag.pk}": "",
            },
        )
        self.assertTrue(resp.status_code < 400)
        table = Table.objects.get(name=self.test_table)
        self.assertTrue(table.tags.contains(tag))
        self.assertTrue(tag.tables.contains(table))
        self.assertTrue(
            tag.name_normalized in table.oemetadata["resources"][0]["keywords"]
        )
