# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Eike Broda <https://github.com/ebroda>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from api.tests import APITestCase, APITestCaseWithTable

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
    "geometry",
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
        body = self.api_req("get")

        self.assertEqual(body["schema"], self.test_schema, "Schema does not match.")
        self.assertEqual(body["name"], self.test_table, "Table does not match.")

        for column in self._structure_data["columns"]:
            for key in column:
                # name is a programmer-introduced key.
                # We are able to use a list instead of a dictonary to get better
                # iteration possibilities.
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
        self.api_req("put", data={"query": self._structure_data})
        self.checkStructure()

    def test_create_and_drop_uppercase_table(self):
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
            ],
        }
        self.test_table = "Table_all_columns"
        self.api_req("put", data={"query": self._structure_data}, exp_code=400)

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
        self.api_req("put", data={"query": self._structure_data})
        body = self.api_req("get")

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
        self.api_req(
            "put", data={"query": self._structure_data}, auth=False, exp_code=401
        )
        self.api_req("get", exp_code=404)

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
        self.api_req(
            "put", data={"query": self._structure_data}, auth=False, exp_code=401
        )


class TestDelete(APITestCaseWithTable):
    def test_anonymous(self):
        self.api_req("delete", auth=False, exp_code=401)

    def test_wrong_user(self):
        self.api_req("delete", auth=self.other_token, exp_code=403)

    def test_simple(self):
        self.api_req("delete")
        self.api_req("get", exp_code=404)
        # create table again so that teardown works
        self.create_table(self.test_structure)


class TestMove(APITestCaseWithTable):
    test_table = "test_table_move"
    test_schema = "model_draft"  # cannot move from "test" schema
    target_schema = "scenario"

    def test_move(self):
        self.api_req(
            "post",
            path=f"move/{self.target_schema}/",
            exp_code=200,
        )

        # check that target table exists, and source does not exist anymore
        self.api_req("get", exp_code=404)
        self.api_req("get", schema=self.target_schema, exp_code=200)

        # move back
        self.api_req(
            "post",
            schema=self.target_schema,
            path=f"move/{self.test_schema}/",
            exp_code=200,
        )


class TestMovePublish(APITestCaseWithTable):
    test_table = "test_table_move_publish"
    test_schema = "model_draft"  # cannot move from "test" schema
    target_schema = "scenario"

    def test_move_publish(self):
        # this will fail, because the licenses check fails
        self.api_req(
            "post", path=f"move_publish/{self.target_schema}/", exp_code=400, exp_res={}
        )

        # so we set the metadata ...
        self.api_req(
            "post",
            path="meta/",
            data=OEMETADATA_V20_EXAMPLE,
            exp_code=200,
        )

        # .. now we do it
        embargo_duration = "6_months"
        self.api_req(
            "post",
            path=f"move_publish/{self.target_schema}/",
            data={"embargo": {"duration": embargo_duration}},
            exp_code=200,
        )

        # check that target table exists, and source does not exist anymore
        self.api_req("get", exp_code=404)
        self.api_req("get", schema=self.target_schema, exp_code=200)

        # move back so we can publish again
        self.api_req(
            "post",
            schema=self.target_schema,
            path=f"move/{self.test_schema}/",
            exp_code=200,
        )

        # publish again with valid embargo
        # .. now we do it, but without (valid) setting embargo
        embargo_duration = "none"
        self.api_req(
            "post",
            path=f"move_publish/{self.target_schema}/",
            data={"embargo": {"duration": embargo_duration}},
            exp_code=200,
        )

        # move back so cleanup works
        self.api_req(
            "post",
            schema=self.target_schema,
            path=f"move/{self.test_schema}/",
            exp_code=200,
        )
