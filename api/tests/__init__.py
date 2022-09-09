import json

from django.test import Client, TestCase
from rest_framework.authtoken.models import Token

from api import actions
from login.models import myuser

from .util import load_content_as_json

# Create your tests here.


def assertEqualJson(o1, o2, msg=None):
    o1 = json.dumps(o1, sort_keys=True, indent=2)
    o2 = json.dumps(o2, sort_keys=True, indent=2)
    msg = msg or f"{o1} != {o2}"
    assert o1 == o2, msg


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
            name="MrTest",
            email="mrtest@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.user.save()
        cls.token = Token.objects.get(user=cls.user)

        cls.other_user, _ = myuser.objects.get_or_create(
            name="NotMrTest",
            email="notmrtest@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.other_user.save()
        cls.other_token = Token.objects.get(user=cls.other_user)

        cls.client = Client()

    def assertEqualJson(self, o1, o2, msg=None):
        return assertEqualJson(o1, o2, msg)

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

    def api_req(
        self,
        method,
        table=None,
        schema=None,
        path=None,
        data=None,
        auth=None,
        exp_code=None,
        exp_res=None,
    ):
        path = path or ""
        if path.startswith("/"):
            assert not table and not schema
            url = f"/api/v0{path}"
        else:
            table = table or self.test_table
            schema = schema or self.test_schema
            url = f"/api/v0/schema/{schema}/tables/{table}/{path}"

        data = json.dumps(data) if data else ""  # IMPORTANT: keep empty string

        method = method.lower()
        if auth is None:
            auth = method != "get"
        if auth is True:  # default token
            auth = self.token
        if auth:
            auth = "Token %s" % auth
        else:
            auth = ""
        request = getattr(self.client, method)

        resp = request(
            path=url,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=auth,
        )

        try:
            json_resp = load_content_as_json(resp)
        except Exception:
            json_resp = None

        print(
            f"{resp.status_code} {method} {url} auth={bool(auth)} data={bool(data)} resp={bool(json_resp)}"  # noqa
        )

        if not exp_code:
            if method == "put":
                exp_code = 201
            else:
                exp_code = 200
        assertEqualJson(resp.status_code, exp_code)

        if exp_res:
            if json_resp and "data" in json_resp:
                json_resp = json_resp["data"]
            assertEqualJson(exp_res, json_resp)

        return json_resp

    def create_table(self, structure, data=None, schema=None, table=None):
        self.api_req("put", table, schema, data={"query": structure})
        if data:
            self.api_req(
                "post",
                table,
                schema,
                "rows/new",
                data={"query": data},
                exp_code=201,
            )

    def drop_table(self, schema=None, table=None):
        self.api_req("delete", table, schema)
