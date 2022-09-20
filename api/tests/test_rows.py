from shapely import wkb, wkt

from . import APITestCaseWithTable


class TestPut(APITestCaseWithTable):
    def test_put_with_id(self):
        row = {"id": 1, "name": "John Doe", "address": None}
        self.api_req("put", path="rows/1", data={"query": row})

        row["geom"] = None
        self.api_req("get", path="rows/1", exp_res=row)

    def test_put_with_wrong_id(self):
        self.api_req(
            "put",
            path="rows/1",
            data={"query": {"id": 2, "name": "John Doe", "address": None}},
            exp_code=409,
        )

    def test_put_with_existing_id(self):
        self.test_put_with_id()

        another_row = {"id": 1, "name": "Mary Doe", "address": "Mary's Street"}
        # NOTE: expect 200, not 201 for PUT
        self.api_req("put", path="rows/1", data={"query": another_row}, exp_code=200)

        another_row["geom"] = None
        self.api_req("get", path="rows/1", exp_res=another_row)

    def test_put_geometry(self):
        row = {
            "id": 1,
            "name": "Mary Doe",
            "address": "Mary's Street",
            "geom": "POINT(-71.160281 42.258729)",
        }
        self.api_req("put", path="rows/1", data={"query": row})

        row["geom"] = wkb.dumps(wkt.loads(row["geom"]), hex=True)
        self.api_req("get", path="rows/1", exp_res=row)

    def test_put_geometry_wtb(self):
        row = {
            "id": 1,
            "name": "Mary Doe",
            "address": "Mary's Street",
            "geom": wkb.dumps(wkt.loads("POINT(-71.160281 42.258729)"), hex=True),
        }

        self.api_req("put", path="rows/1", data={"query": row})
        self.api_req("get", path="rows/1", exp_res=row)

    def test_anonymous(self):
        row = {"id": 1, "name": "John Doe", "address": None}
        self.api_req(
            "put", path="rows/1", data={"query": row}, auth=False, exp_code=403
        )

    def test_wrong_user(self):
        row = {"id": 1, "name": "John Doe", "address": None}
        self.api_req(
            "put",
            path="rows/1",
            data={"query": row},
            auth=self.other_token,
            exp_code=403,
        )


class TestPost(APITestCaseWithTable):
    def test_simple_post_new(self, rid=1):
        row = {
            "id": rid,
            "name": "Mary Doe",
            "address": "Mary's Street",
            "geom": "POINT(-71.160281 42.258729)",
        }
        self.api_req("post", path="rows/new", data={"query": row}, exp_code=201)

        row["geom"] = wkb.dumps(wkt.loads(row["geom"]), hex=True)
        self.api_req("get", path=f"rows/{rid}", exp_res=row)

    def test_anonymous(self, rid=1):
        row = {
            "id": rid,
            "name": "Mary Doe",
            "address": "Mary's Street",
            "geom": "POINT(-71.160281 42.258729)",
        }

        self.api_req(
            "post", path="rows/new", data={"query": row}, auth=False, exp_code=403
        )

    def test_wrong_user(self, rid=1):
        row = {
            "id": rid,
            "name": "Mary Doe",
            "address": "Mary's Street",
            "geom": "POINT(-71.160281 42.258729)",
        }

        self.api_req(
            "post",
            path="rows/new",
            data={"query": row},
            auth=self.other_token,
            exp_code=403,
        )

    def test_simple_post_existing(self):
        self.test_simple_post_new()
        self.test_simple_post_new(rid=2)
        row = {
            "id": 2,
            "name": "John Doe",
            "address": "John's Street",
            "geom": "POINT(42.258729 -71.160281)",
        }

        self.api_req("post", self.test_table, path="rows/2", data={"query": row})

        row["geom"] = wkb.dumps(wkt.loads(row["geom"]), hex=True)

        self.api_req("get", path="rows/2", exp_res=row)

        # Check whether other rows remained unchanged
        row = {
            "id": 1,
            "name": "Mary Doe",
            "address": "Mary's Street",
            "geom": "POINT(-71.160281 42.258729)",
        }
        row["geom"] = wkb.dumps(wkt.loads(row["geom"]), hex=True)
        self.api_req("get", path="rows/1", exp_res=row)

    def test_bulk_insert(self):
        rows = [
            {"id": rid, "name": "Mary Doe", "address": "Mary's Street", "geom": None}
            for rid in range(0, 23)
        ]
        self.api_req("post", path="rows/new", data={"query": rows}, exp_code=201)
        self.api_req("get", path="rows/", exp_res=rows)


class TestGet(APITestCaseWithTable):
    test_data = [
        {
            "id": i,
            "name": "Mary Doe",
            "address": "Mary's Street",
            "geom": "0101000000E44A3D0B42CA51C06EC328081E214540",
        }
        for i in range(100)
    ]

    def test_simple_get(self):
        self.api_req("get", path="rows/", exp_res=self.test_data)

    def test_simple_offset(self):
        self.api_req("get", path="rows/?offset=50", exp_res=self.test_data[50:])

    def test_simple_limit(self):
        self.api_req("get", path="rows/?limit=50")

    def test_simple_where_geq(self):
        self.api_req(
            "get",
            path="rows/?where=id>=50",
            exp_code=200,
            exp_res=[row for row in self.test_data if row["id"] >= 50],
        )

    def test_simple_order_by(self):
        self.api_req(
            "get",
            path="rows/?orderby=id",
            exp_code=200,
            exp_res=sorted([row for row in self.test_data], key=lambda x: x["id"]),
        )


class TestDelete(APITestCaseWithTable):
    test_data = [
        {
            "id": i,
            "name": "Mary Doe",
            "address": "Mary's Street",
            "geom": "0101000000E44A3D0B42CA51C06EC328081E214540",
        }
        for i in range(100)
    ]

    def test_simple(self):
        row = self.test_data.pop()
        self.api_req("delete", path=f"rows/{row['id']}")
        self.api_req("get", path=f"rows/{row['id']}", exp_code=404)
        self.api_req("get", path="rows/", exp_res=self.test_data)

    def test_where(self):
        row = self.test_data[10]
        deleted = [r for r in self.test_data if r["id"] <= row["id"]]
        self.test_data = [r for r in self.test_data if r["id"] > row["id"]]
        self.api_req("delete", path=f"rows/?where=id<={row['id']}")
        for row in deleted:
            self.api_req("get", path=f"rows/{row['id']}", exp_code=404)
        self.api_req("get", path="rows/", exp_res=self.test_data)
