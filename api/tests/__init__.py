import json

from django.test import Client, TestCase
from rest_framework.authtoken.models import Token

from api import actions
from login.models import myuser

from .utils import load_content_as_json


class APITestCase(TestCase):
    test_schema = "test"
    test_table = "test_table"

    @classmethod
    def setUpClass(cls):
        actions.perform_sql(f"DROP SCHEMA IF EXISTS {cls.test_schema} CASCADE")
        actions.perform_sql(f"CREATE SCHEMA {cls.test_schema}")
        actions.perform_sql(f"DROP SCHEMA IF EXISTS _{cls.test_schema} CASCADE")
        actions.perform_sql(f"CREATE SCHEMA _{cls.test_schema}")

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
            name="NotMrTest", email="notmrtest@test.com", did_agree=True
        )
        cls.other_user.save()
        cls.other_token = Token.objects.get(user=cls.other_user)

        cls.client = Client()

    def assertEqualJson(self, o1, o2, msg=None):
        """test equality of nested objects by comparing json string"""
        o1 = json.dumps(o1, sort_keys=True, indent=2)
        o2 = json.dumps(o2, sort_keys=True, indent=2)
        msg = msg or f"{o1} != {o2}"
        self.assertEqual(o1, o2, msg=msg)

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
        method: str,
        table: str = None,
        schema: str = None,
        path: str = None,
        data: dict = None,
        auth=None,
        exp_code: int = None,
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

        if not exp_code:
            if method == "put":
                exp_code = 201
            else:
                exp_code = 200

        if not isinstance(exp_code, (list, tuple)):
            exp_code = [exp_code]

        self.assertTrue(
            resp.status_code in exp_code,
            f"Status {resp.status_code} not in {exp_code}: {json_resp}",
        )

        if exp_res:
            if json_resp and "data" in json_resp:
                json_resp = json_resp["data"]
            self.assertEqualJson(exp_res, json_resp)

        return json_resp

    def create_table(
        self, structure=None, data=None, schema=None, table=None, exp_code=201
    ):
        # default structure
        structure = structure or {"columns": [{"name": "id", "data_type": "bigint"}]}
        self.api_req("put", table, schema, data={"query": structure})
        if data:
            self.api_req(
                "post",
                table,
                schema,
                "rows/new",
                data={"query": data},
                exp_code=exp_code,
            )

    def drop_table(self, schema=None, table=None, exp_code=200):
        self.api_req("delete", table, schema, exp_code=exp_code)


class APITestCaseWithTable(APITestCase):
    """Test class with that creates/deletes the table already on setup/teardown"""

    test_structure = {
        "constraints": [
            {
                "constraint_type": "PRIMARY KEY",
                "constraint_parameter": "id",
                "reference_table": None,
                "reference_column": None,
            }
        ],
        "columns": [
            {
                "name": "id",
                "data_type": "bigserial",
                "is_nullable": False,
            },
            {
                "name": "name",
                "data_type": "character varying",
                "is_nullable": True,
                "character_maximum_length": 50,
            },
            {
                "name": "address",
                "data_type": "character varying",
                "is_nullable": True,
                "character_maximum_length": 150,
            },
            {"name": "geom", "data_type": "Geometry (Point)", "is_nullable": True},
        ],
    }
    test_data = None

    def setUp(self) -> None:
        super().setUp()
        self.create_table(structure=self.test_structure, data=self.test_data)

    def tearDown(self) -> None:
        super().tearDown()
        self.drop_table()
