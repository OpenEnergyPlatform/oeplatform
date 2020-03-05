import json

from api import actions
from api.tests import APITestCase

_TYPES = [
    "bigint",
    "bit",
    "boolean",
    "char",
    "date",
    "decimal",
    "float",
    "integer",
    "interval",
    "json",
    "nchar",
    "numeric",
    "real",
    "smallint",
    "timestamp",
    "text",
    "time",
    "varchar",
    "character varying",
    "geometry"
]


_TYPEMAP = {
    "char": "character",
    "decimal": "numeric",
    "float": "double precision",
    "int": "integer",
    "nchar": "character",
    "timestamp": "timestamp without time zone",
    "time": "time without time zone",
    "varchar": "character varying",
    "character varying": "character varying",
    "bigserial": "bigint",
    "bit": "bytea",
    "double precision": "numeric",
}


class TestPut(APITestCase):
    def checkStructure(self):
        response = self.__class__.client.get(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            )
        )
        body = response.json()

        self.assertEqual(body["schema"], self.test_schema, "Schema does not match.")
        self.assertEqual(body["name"], self.test_table, "Table does not match.")

        for column in self._structure_data["columns"]:
            for key in column:
                # name is a programmer-introduced key.
                # We are able to use a list instead of a dictonary to get better iteration possibilities.
                if key != "name":
                    value = column[key]
                    name = column["name"]
                    covalue = body["columns"][name][key]
                    if key == "data_type":
                        value = _TYPEMAP.get(value, value)

                    self.assertEqual(
                        value,
                        covalue,
                        "Key '{key}' does not match for column {name}.".format(
                            key=key, name=name
                        ),
                    )

        self.assertEqual(response.status_code, 200, "Status Code is not 200.")

    def test_create_table(self):
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
                    "name": "col_varchar123",
                    "data_type": "character varying",
                    "is_nullable": True,
                    "character_maximum_length": 123,
                },
                {"name": "col_intarr", "data_type": "integer[]", "is_nullable": True},
            ]
            + [
                {
                    "name": "col_{type}_{null}".format(
                        type=ctype.lower().replace(" ", "_"),
                        null="true" if null else "false",
                    ),
                    "data_type": ctype.lower(),
                    "is_nullable": null,
                }
                for ctype in _TYPES
                for null in [True, False]
            ],
        }
        self.test_table = "table_all_columns"
        c_basic_resp = self.__class__.client.put(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": self._structure_data}),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            c_basic_resp.status_code,
            201,
            c_basic_resp.json().get("reason", "No reason returned"),
        )
        self.checkStructure()

    def test_create_table_defaults(self):
        self._structure_data = {
            "constraints": [
                {"constraint_type": "PRIMARY KEY", "constraint_parameter": "id"}
            ],
            "columns": [
                {"name": "id", "data_type": "bigserial"},
                {"name": "id2", "data_type": "integer"},
                {"name": "text", "data_type": "varchar"},
            ],
        }
        self.test_table = "table_defaults"
        response = self.__class__.client.put(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": self._structure_data}),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.json().get("reason", "No reason returned"),
        )

        response = self.__class__.client.get(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            )
        )
        body = response.json()

        self.assertEqual(body["schema"], self.test_schema, "Schema does not match.")
        self.assertEqual(body["name"], self.test_table, "Table does not match.")

        self.assertDictEqualKeywise(
            body["columns"]["id"],
            {
                "character_maximum_length": None,
                "character_octet_length": None,
                "data_type": "bigint",
                "datetime_precision": None,
                "dtd_identifier": "1",
                "interval_precision": None,
                "interval_type": None,
                "is_nullable": False,
                "is_updatable": True,
                "maximum_cardinality": None,
                "numeric_precision": 64,
                "numeric_precision_radix": 2,
                "numeric_scale": 0,
            },
            ["ordinal_position", "column_default"],
        )
        self.assertDictEqualKeywise(
            body["columns"]["id2"],
            {
                "character_maximum_length": None,
                "character_octet_length": None,
                "column_default": None,
                "data_type": "integer",
                "datetime_precision": None,
                "dtd_identifier": "2",
                "interval_precision": None,
                "interval_type": None,
                "is_nullable": True,
                "is_updatable": True,
                "maximum_cardinality": None,
                "numeric_precision": 32,
                "numeric_precision_radix": 2,
                "numeric_scale": 0,
            },
            ["ordinal_position"],
        )
        self.assertDictEqualKeywise(
            body["columns"]["text"],
            {
                "character_maximum_length": None,
                "character_octet_length": 1073741824,
                "column_default": None,
                "data_type": "character varying",
                "datetime_precision": None,
                "dtd_identifier": "3",
                "interval_precision": None,
                "interval_type": None,
                "is_nullable": True,
                "is_updatable": True,
                "maximum_cardinality": None,
                "numeric_precision": None,
                "numeric_precision_radix": None,
                "numeric_scale": None,
            },
            ["ordinal_position"],
        )

    def test_create_table_anonymous(self):
        self._structure_data = {
            "constraints": [
                {"constraint_type": "PRIMARY KEY", "constraint_parameter": "bigserial"}
            ],
            "columns": [{"name": "id", "data_type": "bigserial"}],
        }

        self.test_table = "table_anonymous"
        response = self.__class__.client.put(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": self._structure_data}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

        response = self.__class__.client.get(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            )
        )

        self.assertEqual(response.status_code, 404, response.json())

    def test_anonymous(self):
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
                    "name": "col_varchar123",
                    "data_type": "character varying",
                    "is_nullable": True,
                    "character_maximum_length": 123,
                },
                {"name": "col_intarr", "data_type": "integer[]", "is_nullable": True},
            ]
            + [
                {
                    "name": "col_{type}_{null}".format(
                        type=ctype.lower().replace(" ", "_"),
                        null="true" if null else "false",
                    ),
                    "data_type": ctype.lower(),
                    "is_nullable": null,
                }
                for ctype in _TYPES
                for null in [True, False]
            ],
        }
        self.test_table = "table_all_columns"
        c_basic_resp = self.__class__.client.put(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": self._structure_data}),
            content_type="application/json",
        )

        self.assertEqual(
            c_basic_resp.status_code,
            403,
            c_basic_resp.json().get("reason", "No reason returned"),
        )


class TestDelete(APITestCase):
    def setUp(self):
        super(TestDelete, self).setUp()
        self.rows = [
            {
                "id": 1,
                "name": "John Doe",
                "address": None,
                "geom": "Point(-71.160281 42.258729)",
            }
        ]
        self.test_table = "test_table_rows"
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
                {"name": "geom", "data_type": "geometry (point)", "is_nullable": True},
            ],
        }

        c_basic_resp = self.client.put(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": structure_data}),
            HTTP_AUTHORIZATION="Token %s" % self.token,
            content_type="application/json",
        )

        assert c_basic_resp.status_code == 201, c_basic_resp.json()

        self.rows = [
            {
                "id": i,
                "name": "Mary Doe",
                "address": "Mary's Street",
                "geom": "0101000000E44A3D0B42CA51C06EC328081E214540",
            }
            for i in range(10)
        ]

        response = self.client.post(
            "/api/v0/schema/{schema}/tables/{table}/rows/new".format(
                schema=self.test_schema, table=self.test_table
            ),
            data=json.dumps({"query": self.rows}),
            HTTP_AUTHORIZATION="Token %s" % self.token,
            content_type="application/json",
        )

        assert response.status_code == 201, response.json().get(
            "reason", "No reason returned"
        )

    def tearDown(self):
        super(TestDelete, self).tearDown()
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

    def test_simple(self):
        response = self.__class__.client.delete(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.__class__.client.get(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_anonymous(self):
        response = self.__class__.client.delete(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_wrong_user(self):
        response = self.__class__.client.delete(
            "/api/v0/schema/{schema}/tables/{table}/".format(
                schema=self.test_schema, table=self.test_table
            ),
            HTTP_AUTHORIZATION="Token %s" % self.__class__.other_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
