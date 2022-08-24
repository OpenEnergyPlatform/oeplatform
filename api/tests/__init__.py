import json

from django.test import Client, TestCase
from rest_framework.authtoken.models import Token

from api import actions
from login.models import myuser

from .util import content2json, load_content, load_content_as_json

# Create your tests here.


class APITestCase(TestCase):
    test_schema = "test"
    test_table = "population2"

    @classmethod
    def setUpClass(cls):

        actions.perform_sql("DROP SCHEMA IF EXISTS test CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS schema2 CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS schema3 CASCADE")

        actions.perform_sql("CREATE SCHEMA test")
        actions.perform_sql("CREATE SCHEMA schema2")
        actions.perform_sql("CREATE SCHEMA schema3")

        actions.perform_sql("DROP SCHEMA IF EXISTS _test CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS _schema2 CASCADE")
        actions.perform_sql("DROP SCHEMA IF EXISTS _schema3 CASCADE")

        actions.perform_sql("CREATE SCHEMA _test")
        actions.perform_sql("CREATE SCHEMA _schema2")
        actions.perform_sql("CREATE SCHEMA _schema3")

        super(APITestCase, cls).setUpClass()
        cls.user, _ = myuser.objects.get_or_create(
            name="MrTest", email="mrtest@test.com", did_agree=True, is_mail_verified=True
        )
        cls.user.save()
        cls.token = Token.objects.get(user=cls.user)

        cls.other_user, _ = myuser.objects.get_or_create(
            name="NotMrTest", email="notmrtest@test.com", did_agree=True, is_mail_verified=True
        )
        cls.other_user.save()
        cls.other_token = Token.objects.get(user=cls.other_user)

        cls.client = Client()
        

    def assertDictEqualKeywise(self, d1, d2, excluded=None):
        if not excluded:
            excluded = []

        self.assertEqual(
            set(d1.keys()).union(excluded),
            set(d2.keys()).union(excluded),
            "Key sets do not match",
        )

        for key in d1:
            if key not in excluded:
                value = d1[key]
                covalue = d2[key]
                self.assertEqual(
                    value, covalue, "Key '{key}' does not match.".format(key=key)
                )

    def create_table(self, structure, data=None, schema=None, table=None):

        if not schema:
            schema = self.test_schema
        if not table:
            table = self.test_table

        resp = self.__class__.client.put(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=schema, table=table
            ),
            data=json.dumps({"query": structure}),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            resp.status_code, 201, resp.json().get("reason", "No reason returned")
        )

        if data:
            resp = self.__class__.client.post(
                "/api/v0/schema/{schema}/tables/{table}/rows/new".format(
                    schema=schema, table=table
                ),
                data=json.dumps({"query": data}),
                HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
                content_type="application/json",
            )

            self.assertEqual(
                resp.status_code,
                201,
                load_content_as_json(resp).get("reason", "No reason returned"),
            )

    def check_api_send(
        self, request, url, data=None, expected_result=None, expected_code=200
    ):

        params = dict(
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )
        if data:
            params["data"] = json.dumps(data)

        resp = request(url, **params)

        content = load_content(resp)

        self.assertEqual(
            resp.status_code,
            expected_code,
            content.get("reason", "No reason returned")
            if isinstance(content, dict)
            else content,
        )

        json_resp = content2json(content)

        if "data" in json_resp or expected_result:
            if isinstance(json_resp, dict):
                if "data" in json_resp:
                    self.assertTrue(
                        "data" in json_resp,
                        '%s does not contain a "data"-entry' % str(json_resp),
                    )
                    json_resp = json_resp["data"]

            if expected_result:
                if isinstance(expected_result, list):
                    self.assertListEqual(json_resp, expected_result)
                elif isinstance(expected_result, dict):
                    self.assertDictEqual(json_resp, expected_result)
                else:
                    self.assertEqual(json_resp, expected_result)

    def check_api_post(self, *args, **kwargs):
        self.check_api_send(self.__class__.client.post, *args, **kwargs)

    def check_api_get(self, *args, **kwargs):
        self.check_api_send(self.__class__.client.get, *args, **kwargs)

    def drop_table(self, schema=None, table=None):
        if not schema:
            schema = self.test_schema
        if not table:
            table = self.test_table

        resp = self.__class__.client.delete(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=schema, table=table
            ),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            resp.status_code, 200, resp.json().get("reason", "No reason returned")
        )

