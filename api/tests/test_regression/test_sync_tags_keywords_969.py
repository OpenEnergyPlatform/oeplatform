"""
changing tags in the UI and changing keywords in metadata should be synchronized
"""
from api.connection import create_oedb_session
from api.tests import APITestCase, Client
from dataedit.structures import TableTags, Tag


class Test_sync_tags_keywords_969(APITestCase):
    def test_sync_tags_keywords_969(self):
        table = "test_keyword_tags"
        structure = {"columns": [{"name": "id", "data_type": "bigserial"}]}
        post_tag_url = "/dataedit/tags/add/"
        meta_template = {"id": "id"}  # must have id

        client = Client()
        client.token = self.token
        client.force_login(self.user)

        other_client = Client()
        other_client.token = self.other_token
        other_client.force_login(self.other_user)

        # create table
        self.api_req("put", table=table, data={"query": structure})

        # get existing keywords (none)
        def get_keywords():
            meta = self.api_req("get", table=table, path="meta/")
            keywords = meta.get("keywords", [])
            names = [Tag.create_name_normalized(k) for k in keywords]
            return sorted(names)

        def set_keywords(keywords, exp_code=200, auth=self.token):
            meta_template["keywords"] = keywords
            self.api_req(
                "post",
                table=table,
                data=meta_template,
                path="meta/",
                exp_code=exp_code,
                auth=auth,
            )

        def load_tag_names_from_db():
            ses = create_oedb_session()
            tags = (
                ses.query(Tag)
                .filter(
                    Tag.id.in_(
                        [
                            tt.tag
                            for tt in ses.query(TableTags).filter(
                                TableTags.table_name == table,
                                TableTags.schema_name == self.test_schema,
                            )
                        ]
                    )
                )
                .all()
            )
            names = [t.name_normalized for t in tags]
            return sorted(names)

        def set_tag_names_in_db(names):
            ses = create_oedb_session()
            ses.query(TableTags).filter(
                TableTags.table_name == table, TableTags.schema_name == self.test_schema
            ).delete()
            ses.flush()
            added_ids = set()
            for n in names:
                n2 = Tag.create_name_normalized(n)
                tag = ses.query(Tag).filter(Tag.name_normalized == n2).first()
                if tag is None:
                    tag = Tag(name=n)
                    ses.add(tag)
                    ses.flush()
                if tag.id not in added_ids:
                    added_ids.add(tag.id)
                    ses.add(
                        TableTags(
                            table_name=table, schema_name=self.test_schema, tag=tag.id
                        )
                    )
            ses.commit()

        def set_tag_names_in_post(names, client=client):
            ses = create_oedb_session()
            added_ids = set()
            for n in names:
                n2 = Tag.create_name_normalized(n)
                tag = ses.query(Tag).filter(Tag.name_normalized == n2).first()
                if tag is None:
                    tag = Tag(name=n)
                    ses.add(tag)
                    ses.flush()
                if tag.id not in added_ids:
                    added_ids.add(tag.id)
            ses.commit()
            data = {
                "table": table,
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
            set_tag_names_in_post(["keyword_one", "new Tag"]).status_code, 302
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
