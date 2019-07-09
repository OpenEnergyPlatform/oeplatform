import requests
import json
from api.tests import APITestCase
from ..util import load_content_as_json


class Test271(APITestCase):
    def setUp(self):
        self._structure_data = {
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
                    "character_maximum_length": None,
                },
                {
                    "name": "name",
                    "data_type": "character varying",
                    "is_nullable": True,
                    "character_maximum_length": 123,
                },
            ],
        }

        resp = self.__class__.client.put(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": self._structure_data}),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            resp.status_code, 201, resp.json().get("reason", "No reason returned")
        )

        resp = self.__class__.client.post(
            "/api/v0/schema/{schema}/tables/{table}/rows/new".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": [{"name": "Hans"}, {"name": "Petra"}]}),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            resp.status_code,
            201,
            load_content_as_json(resp).get("reason", "No reason returned"),
        )

    def test_271(self):
        data = {
            "query": {
                "fields": [dict(type="column", column="name")],
                "where": [
                    {
                        "type": "operator",
                        "operator": "=",
                        "operands": [
                            {"type": "column", "column": "name"},
                            {"type": "value", "value": "Hans"},
                        ],
                    }
                ],
                "from": {
                    "type": "table",
                    "table": self.test_table,
                    "schema": self.test_schema,
                },
            }
        }

        resp = self.__class__.client.post(
            "/api/v0/advanced/search",
            data=json.dumps(data),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.check_api_post(
            "/api/v0/advanced/search", data=data, expected_result=[["Hans"]]
        )

    def test_271_column_does_not_exist(self):
        data = {
            "query": {
                "fields": [dict(type="column", column="does_not_exist")],
                "from": {
                    "type": "table",
                    "table": self.test_table,
                    "schema": self.test_schema,
                },
            }
        }
        resp = self.__class__.client.post(
            "/api/v0/advanced/search",
            data=json.dumps(data),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            resp.status_code, 400, resp.json().get("reason", "No reason returned")
        )

        json_resp = resp.json()

        self.assertEqual(json_resp["reason"], 'column "does_not_exist" does not exist')

    def tearDown(self):
        resp = self.__class__.client.delete(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            resp.status_code, 200, resp.json().get("reason", "No reason returned")
        )
