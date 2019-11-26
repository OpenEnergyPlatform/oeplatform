import json

import requests

from api.tests import APITestCase

from ..util import load_content_as_json


class TestAliasesTracking(APITestCase):
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

        # Check HTTP-response (201 = Successful create)
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

        # Check HTTP-response (201 = Successful create)
        self.assertEqual(
            resp.status_code,
            201,
            load_content_as_json(resp).get("reason", "No reason returned"),
        )

    def test_aliases_in_form_clauses(self):
        data = {
            "query": {
                "fields": [dict(type="column", column="id", table="a")],
                "where": [
                    {
                        "type": "operator",
                        "operator": "=",
                        "operands": [
                            {"type": "column", "column": "name", "table": "a"},
                            {"type": "value", "value": "Hans"},
                        ],
                    }
                ],
                "from": {
                    "type": "join",
                    "left": {
                        "type": "table",
                        "table": self.test_table,
                        "schema": self.test_schema,
                        "alias": "a"
                    },
                    "right": {
                        "type": "table",
                        "table": self.test_table,
                        "schema": self.test_schema,
                        "alias": "b"
                    },
                    "on":[
                        {
                            "type": "operator",
                            "operator": "=",
                            "operands": [
                                {"type": "column", "column": "id", "table": "a"},
                                {"type": "column", "column": "id", "table": "b"},
                            ],
                        }
                    ]
                }
            }
        }

        resp = self.__class__.client.post(
            "/api/v0/advanced/search",
            data=json.dumps(data),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.check_api_post(
            "/api/v0/advanced/search", data=data, expected_result=[[1]]
        )

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
