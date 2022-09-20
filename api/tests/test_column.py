from . import APITestCaseWithTable


class TestPut(APITestCaseWithTable):
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
                "dtd_identifier": "5",  # default table has 4 columns
                "is_nullable": True,
                "datetime_precision": None,
                "ordinal_position": 5,  # default table has 4 columns
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


class TestPost(APITestCaseWithTable):
    def test_rename(self):
        structure_data = {"name": "name2"}
        self.api_req(
            "post",
            path="columns/name",
            data={"query": structure_data},
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
        structure_data = {"data_type": "text"}

        self.api_req(
            "post",
            path="columns/name",
            data={"query": structure_data},
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
