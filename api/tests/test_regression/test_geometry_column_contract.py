"""
The contract for a geometry column, asserted through the HTTP surface:

- it gets a GiST index automatically, which comes from GeoAlchemy2's
  spatial_index default rather than from any code of ours - so a dependency
  upgrade that changes that default must fail a test, not silently degrade
  every new geo table
- an SRID declared in the column type is the SRID registered on the Main Table

Needs PostGIS; these tests fail against a plain postgres.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api.tests import APITestCase


class TestGeometryColumnContract(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.empty_test_schema()

    def tearDown(self) -> None:
        self.empty_test_schema()
        super().tearDown()

    def _create_with_geom(self, table, data_type):
        self.create_table(
            table=table,
            structure={
                "columns": [
                    {"name": "id", "data_type": "bigint"},
                    {"name": "geom", "data_type": data_type},
                ]
            },
        )

    def _geom_type(self, table):
        json_resp = self.api_req(
            "post", path="/advanced/get_columns", data={"query": {"table": table}}
        )
        columns = dict((col[0], col[1]) for col in json_resp["content"]["columns"])
        return columns["geom"]

    def _index_definitions(self, table):
        described = self.api_req("get", table, auth=False)
        return [index["indexdef"] for index in described["indexed"].values()]

    def test_geometry_column_gets_a_gist_index(self):
        self._create_with_geom("geom_indexed", "geometry(Point,4326)")

        gist_indexes = [
            definition
            for definition in self._index_definitions("geom_indexed")
            if "USING gist" in definition and "geom" in definition
        ]
        self.assertEqual(1, len(gist_indexes), self._index_definitions("geom_indexed"))

    def test_declared_srid_is_registered_on_the_table(self):
        self._create_with_geom("geom_with_srid", "geometry(Point,4326)")

        self.assertEqual("geometry(Point,4326)", self._geom_type("geom_with_srid"))

    def test_declared_subtype_is_registered_on_the_table(self):
        self._create_with_geom("geom_multipolygon", "geometry(MultiPolygon,3035)")

        self.assertEqual(
            "geometry(MultiPolygon,3035)", self._geom_type("geom_multipolygon")
        )

    def test_geometry_without_srid_registers_as_unknown(self):
        self._create_with_geom("geom_without_srid", "geometry(Point)")

        self.assertEqual("geometry(Point)", self._geom_type("geom_without_srid"))

    def test_invalid_srid_is_rejected(self):
        json_resp = self.api_req(
            "put",
            "geom_bad_srid",
            data={
                "query": {
                    "columns": [
                        {"name": "id", "data_type": "bigint"},
                        {"name": "geom", "data_type": "geometry(Point,not_a_srid)"},
                    ]
                }
            },
            params={"is_sandbox": True},
            exp_code=400,
        )

        self.assertIn("Invalid SRID", json_resp["reason"])
