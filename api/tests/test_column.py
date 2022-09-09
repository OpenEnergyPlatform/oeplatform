from api import actions

from . import APITestCase


class TestPut(APITestCase):
    def setUp(self):
        self.test_table = "test_table_column"
        self.test_schema = "test"
        self.structure_data = {
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
                {"name": "geom", "data_type": "Geometry (Point)", "is_nullable": True},
            ],
        }

        self.api_req("put", data={"query": self.structure_data})

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

    def test_simple(self):
        structure_data = {"data_type": "varchar", "character_maximum_length": 30}
        self.api_req(
            "put",
            path="columns/new_column",
            data={"query": structure_data},
            exp_code=201,
        )

        res = self.api_req("get")
        self.assertEqualJson(
            res["columns"]["new_column"],
            {
                "character_maximum_length": 30,
                "numeric_scale": None,
                "dtd_identifier": "5",
                "is_nullable": True,
                "datetime_precision": None,
                "ordinal_position": 5,
                "data_type": "character varying",
                "maximum_cardinality": None,
                "is_updatable": True,
                "numeric_precision_radix": None,
                "interval_precision": None,
                "character_octet_length": 120,
                "numeric_precision": None,
                "column_default": None,
                "interval_type": None,
            },
        )

    def test_anonymous(self):
        structure_data = {"data_type": "varchar", "character_maximum_length": 30}
        self.api_req("put", data={"query": structure_data}, auth=False, exp_code=403)

    def test_wrong_user(self):
        structure_data = {"data_type": "varchar", "character_maximum_length": 30}
        self.api_req(
            "put",
            path="columns/new_column",
            data={"query": structure_data},
            auth=self.other_token,
            exp_code=403,
        )


class TestPost(APITestCase):
    def setUp(self):
        self.test_table = "test_table_column"
        self.test_schema = "test"
        self.structure_data = {
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
                {"name": "geom", "data_type": "Geometry (Point)", "is_nullable": True},
            ],
        }

        self.api_req(
            "put",
            data={"query": self.structure_data},
            exp_code=201,
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

    def test_rename(self):
        self.structure_data = {"name": "name2"}
        self.api_req(
            "post",
            path="columns/name",
            data={"query": self.structure_data},
            exp_code=200,
        )
        self.api_req(
            "get",
            path="columns/name2",
            exp_code=200,
            exp_res={
                "character_octet_length": 200,
                "ordinal_position": 2,
                "character_maximum_length": 50,
                "interval_type": None,
                "data_type": "character varying",
                "column_default": None,
                "numeric_precision_radix": None,
                "is_updatable": True,
                "numeric_scale": None,
                "is_nullable": True,
                "maximum_cardinality": None,
                "numeric_precision": None,
                "datetime_precision": None,
                "dtd_identifier": "2",
                "interval_precision": None,
            },
        )

    def test_type_change(self):
        self.structure_data = {"data_type": "text"}

        self.api_req(
            "post",
            path="columns/name",
            data={"query": self.structure_data},
            exp_code=200,
        )

        self.api_req(
            "get",
            path="columns/name",
            exp_code=200,
            exp_res={
                "character_octet_length": 1073741824,
                "ordinal_position": 2,
                "character_maximum_length": None,
                "interval_type": None,
                "data_type": "text",
                "column_default": None,
                "numeric_precision_radix": None,
                "is_updatable": True,
                "numeric_scale": None,
                "is_nullable": True,
                "maximum_cardinality": None,
                "numeric_precision": None,
                "datetime_precision": None,
                "dtd_identifier": "2",
                "interval_precision": None,
            },
        )
