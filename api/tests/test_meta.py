import json

from shapely import wkb, wkt

from api import actions

from . import APITestCase
from .util import content2json, load_content, load_content_as_json


class TestPut(APITestCase):
    def setUp(self):
        structure_data = {
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
            ],
        }

        c_basic_resp = self.__class__.client.put(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": structure_data}),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        assert c_basic_resp.status_code == 201, c_basic_resp.json().get(
            "reason", "No reason returned"
        )

    def tearDown(self):
        meta_schema = actions.get_meta_schema_name(self.test_schema)
        if actions.has_table(dict(table=self.test_table, schema=self.test_schema)):
            actions.perform_sql(
                "DROP TABLE IF EXISTS {schema}.{table} CASCADE".format(
                    schema=meta_schema,
                    table=actions.get_insert_table_name(
                        self.test_schema, self.test_table
                    ),
                )
            )
            actions.perform_sql(
                "DROP TABLE IF EXISTS {schema}.{table} CASCADE".format(
                    schema=meta_schema,
                    table=actions.get_edit_table_name(
                        self.test_schema, self.test_table
                    ),
                )
            )
            actions.perform_sql(
                "DROP TABLE IF EXISTS {schema}.{table} CASCADE".format(
                    schema=meta_schema,
                    table=actions.get_delete_table_name(
                        self.test_schema, self.test_table
                    ),
                )
            )
            actions.perform_sql(
                "DROP TABLE IF EXISTS {schema}.{table} CASCADE".format(
                    schema=self.test_schema, table=self.test_table
                )
            )

    def test_set_meta(self):
        meta = {"id": self.test_table}
        response = self.__class__.client.post(
            "/api/v0/schema/{schema}/tables/{table}/meta/".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": meta}),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.content,
        )
        response = self.__class__.client.get(
            "/api/v0/schema/{schema}/tables/{table}/meta/".format(
                schema=self.test_schema, table=self.test_table
            )
        )

        self.assertEqual(response.status_code, 200, response.json())

        self.assertDictEqualKeywise(response.json(), meta)
