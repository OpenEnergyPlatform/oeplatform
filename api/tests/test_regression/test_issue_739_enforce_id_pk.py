"""
inserting the string "1000" in a varchar column 
that has unique constraint  leads to an error.
"""
import json

from api.tests import APITestCase
from django.urls import reverse
from rest_framework.test import APIClient


class Test_issue_739_enforce_id_pk(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cli = APIClient()
        cls.cli.credentials(HTTP_AUTHORIZATION="Token %s" % cls.token)

    def create_table(self, table_definition, table=None):
        table = table or "test_id_pk_table"
        table_url = reverse(
            "api_table", kwargs={"schema": self.test_schema, "table": table}
        )
        return self.cli.put(table_url, {"query": table_definition}, format="json")

    def test_check_insert_issue_739(self):
        table = "test_id_data"

        res = self.create_table(
            {"columns": [{"name": "not_id", "data_type": "int"}]}, table
        )
        self.assertEqual(res.status_code, 201, msg=res.json())

        # insert record via normal api
        # this fails if there is no column named `id`
        # which should be auto generated, if missing
        url = reverse(
            "api_rows_new", kwargs={"schema": self.test_schema, "table": table}
        )
        res = self.cli.post(url, {"query": [{"not_id": 99}]}, format="json")
        self.assertEqual(res.status_code, 201)

        # retrieve data
        url = reverse("api_rows", kwargs={"schema": self.test_schema, "table": table})
        res = json.loads(self.cli.get(url).getvalue().decode())
        self.assertEqual(len(res), 1)
        self.assertGreaterEqual(res[0]["id"], 0)  # auto generated id

    def test_id_type_and_pk(self):

        res = self.create_table(
            {"columns": [{"name": "id", "data_type": "int", "primary_key": True}]},
            "test_id_ok",
        )
        self.assertEqual(res.status_code, 201)

        res = self.create_table(
            {"columns": [{"name": "id", "data_type": "int"}]}, "test_id_auto_create_pk"
        )
        self.assertEqual(res.status_code, 201)

        res = self.create_table(
            {"columns": [{"name": "id", "data_type": "float"}]}, "test_id_wrong_type"
        )
        self.assertEqual(res.status_code, 400)

        res = self.create_table(
            {
                "columns": [
                    {"name": "id", "data_type": "int"},
                    {"name": "id2", "data_type": "int", "primary_key": True},
                ]
            },
            "test_id_wrong_pk2",
        )
        self.assertEqual(res.status_code, 400)

    def test_err_on_col_duplicate(self):
        res = self.create_table(
            {
                "columns": [
                    {"name": "id", "data_type": "float"},
                    {"name": "id", "data_type": "int"},
                ]
            }
        )
        self.assertEqual(res.status_code, 400)

    def test_err_on_multiple_pk(self):
        res = self.create_table(
            {
                "columns": [
                    {"name": "id1", "data_type": "float", "primary_key": True},
                    {"name": "id2", "data_type": "int", "primary_key": True},
                ]
            }
        )
        self.assertEqual(res.status_code, 400)

        res = self.create_table(
            {
                "columns": [
                    {"name": "id1", "data_type": "float", "primary_key": True},
                    {"name": "id2", "data_type": "int"},
                ],
                "constraints": [{"type": "primary_key", "columns": ["id2"]}],
            }
        )
        self.assertEqual(res.status_code, 400)
