"""
Two paths dropped the database's own reason for a failure:

- a failed table create answered "Could not create table <name>" and nothing
  else, so an unusable column definition was undebuggable
- a spatial query whose reference system arrived as a JSON string answered
  "Invalid request", hiding PostGIS' "could not parse proj string '4326'"
  (openego/ding0#405)

Both now report the cause when it is safe to disclose, through the single
policy in api.error.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api.tests import APITestCase


class TestTableCreateReportsCause(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.empty_test_schema()

    def tearDown(self) -> None:
        self.empty_test_schema()
        super().tearDown()

    def test_invalid_column_precision_reports_the_database_reason(self):
        # numeric(1001) passes the parser and is rejected by postgres, so this
        # exercises the DDL failure path rather than payload validation
        json_resp = self.api_req(
            "put",
            "create_invalid_precision",
            data={
                "query": {
                    "columns": [
                        {"name": "id", "data_type": "bigint"},
                        {"name": "value", "data_type": "numeric(1001)"},
                    ]
                }
            },
            params={"is_sandbox": True},
            exp_code=400,
        )

        self.assertIn("Could not create table", json_resp["reason"])
        self.assertIn("1001", json_resp["reason"])

    def test_unusable_reason_still_reports_the_generic_message(self):
        # a duplicate table name fails before any DDL runs, so there is no
        # database cause to add and the message must stay as it was
        self.create_table(table="create_duplicate_name")
        json_resp = self.api_req(
            "put",
            "create_duplicate_name",
            data={"query": {"columns": [{"name": "id", "data_type": "bigint"}]}},
            params={"is_sandbox": True},
            exp_code=409,
        )

        self.assertEqual("Table already exists", json_resp["reason"])


class TestSpatialQueryReportsCause(APITestCase):
    """The table needs a known SRID and at least one row, otherwise the
    reprojection is never evaluated and no error surfaces."""

    spatial_table = "transform_srid_arg"

    def setUp(self) -> None:
        super().setUp()
        self.empty_test_schema()
        self.create_table(
            table=self.spatial_table,
            structure={
                "columns": [
                    {"name": "id", "data_type": "bigint"},
                    {"name": "geom", "data_type": "geometry(Point,3035)"},
                ]
            },
            data=[{"geom": "SRID=3035;POINT(4038631 3111190)"}],
        )

    def tearDown(self) -> None:
        self.empty_test_schema()
        super().tearDown()

    def _transform_with(self, srid, exp_code):
        return self.api_req(
            "post",
            path="/advanced/search",
            data={
                "query": {
                    "fields": [
                        {
                            "type": "label",
                            "label": "wkt",
                            "element": {
                                "type": "function",
                                "function": "ST_AsText",
                                "operands": [
                                    {
                                        "type": "function",
                                        "function": "ST_Transform",
                                        "operands": [
                                            {"type": "column", "column": "geom"},
                                            {"type": "value", "value": srid},
                                        ],
                                    }
                                ],
                            },
                        }
                    ],
                    "from": {"type": "table", "table": self.spatial_table},
                }
            },
            exp_code=exp_code,
        )

    def test_reference_system_as_string_reports_the_proj_error(self):
        # a string picks PostGIS' (geometry, to_proj text) overload, which tries
        # to read "4326" as a projection definition
        json_resp = self._transform_with("4326", exp_code=400)

        self.assertIn("could not parse proj string", json_resp["reason"])
        self.assertIn("4326", json_resp["reason"])

    def test_reference_system_as_integer_succeeds(self):
        json_resp = self._transform_with(4326, exp_code=200)

        self.assertNotIn("reason", json_resp)
        self.assertEqual(
            ["wkt"], [col[0] for col in json_resp["content"]["description"]]
        )
        self.assertIn("POINT(5.97", json_resp["data"][0][0])
