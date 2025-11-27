"""changing tags in the UI and changing keywords in metadata should be synchronized.


SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from api.tests import APITestCaseWithTable, Client
from dataedit.models import Table, Tag


class Test_sync_tags_keywords_969(APITestCaseWithTable):
    test_table = "test_keyword_tags"
    test_structure = {"columns": [{"name": "id", "data_type": "bigserial"}]}

    def test_sync_tags_keywords_969(self):
        post_tag_url = reverse("dataedit:tags-add")
        meta_template = OEMETADATA_V20_EXAMPLE  # must have id
        client = Client()
        client.force_login(self.user)

        other_client = Client()
        other_client.force_login(self.other_user)

        # get existing keywords (none)
        def get_keywords_via_api() -> set[str]:
            meta = self.api_req("get", table=self.test_table, path="meta/")
            # TODO: Dont use the fixed index when getting keywords
            # to handle mulitple resources correctly
            keywords = meta["resources"][0].get("keywords", [])
            return set(keywords)

        def set_keywords_via_api(keywords, exp_code=200, auth=self.token):
            # TODO: Dont use the fixed index when getting keywords
            # to handle mulitple resources correctly
            meta_template["resources"][0]["keywords"] = keywords
            self.api_req(
                "post",
                table=self.test_table,
                data=meta_template,
                path="meta/",
                exp_code=exp_code,
                auth=auth,
            )

        def load_tag_ids_from_db() -> set[str]:
            return set(t.pk for t in Tag.objects.filter(tables__name=self.test_table))

        def set_tag_names_in_db(names: list[str]):
            table = Table.objects.get(name=self.test_table)
            table.tags.clear()
            for n in names:
                tag, _ = Tag.objects.get_or_create(name=n)
                table.tags.add(tag)
            table.save()

        def set_tag_names_via_web_http(names: list[str], client=client):
            data = {
                "table": self.test_table,
            }
            added_ids = [Tag.get_or_create_from_name(name=n).pk for n in names]
            for i in added_ids:
                data["tag_%s" % i] = "on"

            return client.post(post_tag_url, data=data, HTTP_REFERER="/")

        # set empty twice in case test database has not been cleared properly
        # because test tables are being reused
        set_tag_names_in_db([])
        set_keywords_via_api([])
        self.assertSetEqual(get_keywords_via_api(), set())

        set_keywords_via_api(["Keyword One"])
        self.assertSetEqual(get_keywords_via_api(), {"keyword_one"})
        self.assertSetEqual(load_tag_ids_from_db(), {"keyword_one"})

        # update tags from UI -> updates metadata
        self.assertEqual(
            set_tag_names_via_web_http(["keyword_one", "new Tag"]).status_code, 302
        )  # redirect
        self.assertSetEqual(
            set(get_keywords_via_api()), {"keyword_one", "new_tag"}
        )  # key2 will be removed
        self.assertSetEqual(load_tag_ids_from_db(), {"keyword_one", "new_tag"})

        # check write permission of metadata for other user (should fail)
        set_keywords_via_api(["nope"], exp_code=403, auth=self.other_token)

        # check write permission of tags for other user: cannot really test:
        # still returns redirect, because this is not an API endpoint
        self.assertEqual(
            set_tag_names_via_web_http(["nope"], client=other_client).status_code, 302
        )
