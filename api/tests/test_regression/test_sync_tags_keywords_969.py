"""changing tags in the UI and changing keywords in metadata should be synchronized.


SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from api.tests import APITestCase, Client
from dataedit.models import Table, Tag


class Test_sync_tags_keywords_969(APITestCase):
    def test_sync_tags_keywords_969(self):
        table_name = "test_keyword_tags"
        structure = {"columns": [{"name": "id", "data_type": "bigserial"}]}
        post_tag_url = "/dataedit/tags/add/"
        meta_template = OEMETADATA_V20_EXAMPLE  # must have id
        client = Client()
        client.token = self.token
        client.force_login(self.user)

        other_client = Client()
        other_client.token = self.other_token
        other_client.force_login(self.other_user)

        # create table
        self.api_req("put", table=table_name, data={"query": structure})

        # get existing keywords (none)
        def get_keywords() -> list[str]:
            meta = self.api_req("get", table=table_name, path="meta/")
            # TODO: Dont use the fixed index when getting keywords
            # to handle mulitple resources correctly
            keywords = meta["resources"][0].get("keywords", [])
            names = [Tag.get_name_normalized(k) for k in keywords]
            return sorted(names)

        def set_keywords(keywords, exp_code=200, auth=self.token):
            # TODO: Dont use the fixed index when getting keywords
            # to handle mulitple resources correctly
            meta_template["resources"][0]["keywords"] = keywords
            self.api_req(
                "post",
                table=table_name,
                data=meta_template,
                path="meta/",
                exp_code=exp_code,
                auth=auth,
            )

        def load_tag_names_from_db() -> list[str]:
            names = [
                t.name_normalized for t in Tag.objects.filter(tables__name=table_name)
            ]
            return sorted(names)

        def set_tag_names_in_db(names):
            table = Table.objects.get(name=table_name)
            table.tags.clear()
            for n in names:
                tag = Tag(name=n)
                tag.save()
                table.tags.add(tag)
            table.save()

        def set_tag_names_in_post(names, client=client):
            added_ids = set()
            for n in names:
                tag, _ = Tag.objects.get_or_create(name=n)
                added_ids.add(tag.pk)
            data = {
                "table": table_name,
                "schema": self.test_schema,
            }
            for i in added_ids:
                data["tag_%d" % i] = "on"

            return client.post(post_tag_url, data=data, HTTP_REFERER="/")

        # set empty twice in case test database has not been cleared properly
        # because test tables are being reused
        set_tag_names_in_db([])
        set_keywords([])
        self.assertListEqual(get_keywords(), [])

        set_keywords(["Keyword One"])
        self.assertListEqual(get_keywords(), ["keyword_one"])
        self.assertListEqual(load_tag_names_from_db(), ["keyword_one"])

        # change tags in db so they are no longer synchronized with metadata
        set_tag_names_in_db(["Keyword One", "key2", " Key2"])
        self.assertListEqual(load_tag_names_from_db(), ["key2", "keyword_one"])

        # update tags from UI -> updates metadata
        self.assertEqual(
            set_tag_names_in_post(["keyword_one", "new TagOEDB"]).status_code, 302
        )  # redirect
        self.assertListEqual(
            get_keywords(), ["keyword_one", "new_tag"]
        )  # key2 will be removed
        self.assertListEqual(load_tag_names_from_db(), ["keyword_one", "new_tag"])

        # check write permission of metadata for other user (should fail)
        set_keywords(["nope"], exp_code=403, auth=self.other_token)

        # check write permission of tags for other user (should fail)
        self.assertEqual(
            set_tag_names_in_post(["nope"], client=other_client).status_code, 403
        )
