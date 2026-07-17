"""Tests for the Bulk Upload endpoint (issue #2362, slice 2).

Bulk Upload is the high-throughput, append-only write path: the request body
is the CSV, rows go directly into the main table without edit-journal
records, all-or-nothing per request.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
from datetime import timedelta

from django.utils import timezone

from api.tests import APITestCaseWithTable
from dataedit.models import Embargo, Table
from oedb.connection import _get_engine


class TestBulkUpload(APITestCaseWithTable):
    def bulk_upload(
        self,
        csv_text: str,
        delimiter: str | None = "comma",
        table: str | None = None,
        auth: str | None = "default",
        exp_code: int | None = None,
    ) -> dict:
        url = f"/api/v0/tables/{table or self.test_table}/bulk-upload/"
        if delimiter is not None:
            url += f"?delimiter={delimiter}"
        kwargs = {}
        if auth == "default":
            kwargs["HTTP_AUTHORIZATION"] = f"Token {self.token}"
        elif auth == "other":
            kwargs["HTTP_AUTHORIZATION"] = f"Token {self.other_token}"
        resp = self.client.post(
            url, data=csv_text.encode("utf-8"), content_type="text/csv", **kwargs
        )
        if exp_code is not None:
            self.assertEqual(
                resp.status_code, exp_code, getattr(resp, "content", b"")[:500]
            )
        try:
            return json.loads(resp.content)
        except (ValueError, AttributeError):
            return {}

    def get_rows(self) -> list:
        res = self.api_req("get", path="rows/")
        if isinstance(res, dict):
            return res.get("data", [])
        return res

    def test_upload_csv_rows_land_in_table(self):
        csv_text = "id,name,address\n1,alice,berlin\n2,bob,hamburg\n"
        result = self.bulk_upload(csv_text, exp_code=201)
        self.assertEqual(result["rows"], 2)
        rows = self.get_rows()
        self.assertEqual(len(rows), 2)
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(by_id[1]["name"], "alice")
        self.assertEqual(by_id[2]["address"], "hamburg")

    def test_semicolon_delimiter(self):
        self.bulk_upload("id;name\n1;semi\n", delimiter="semicolon", exp_code=201)
        self.assertEqual(self.get_rows()[0]["name"], "semi")

    def test_tab_delimiter(self):
        self.bulk_upload("id\tname\n1\ttabbed\n", delimiter="tab", exp_code=201)
        self.assertEqual(self.get_rows()[0]["name"], "tabbed")

    def test_internal_journal_table_unreachable(self):
        # the physical journal tables exist in the database but are not
        # registered platform tables, so they can never be an upload target
        self.bulk_upload("id\n1\n", table="_test_table_insert", exp_code=404)

    def test_missing_delimiter_rejected(self):
        self.bulk_upload("id,name\n1,x\n", delimiter=None, exp_code=400)
        self.assertEqual(self.get_rows(), [])

    def test_invalid_delimiter_rejected(self):
        self.bulk_upload("id,name\n1,x\n", delimiter="pipe", exp_code=400)
        self.assertEqual(self.get_rows(), [])

    def test_unauthenticated_rejected(self):
        self.bulk_upload("id,name\n1,x\n", auth=None, exp_code=401)
        self.assertEqual(self.get_rows(), [])

    def test_user_without_write_permission_rejected(self):
        self.bulk_upload("id,name\n1,x\n", auth="other", exp_code=403)
        self.assertEqual(self.get_rows(), [])

    def test_embargoed_table_rejected(self):
        Embargo.objects.create(
            table=Table.objects.get(name=self.test_table),
            date_ended=timezone.now() + timedelta(days=30),
            duration="6_months",
        )
        self.bulk_upload("id,name\n1,x\n", exp_code=403)
        # note: the table cannot be read back here - the embargo blocks reads too

    def test_malformed_row_rolls_back_everything(self):
        csv_text = "id,name\n1,ok\nnot_an_int,bad\n3,also_ok\n"
        self.bulk_upload(csv_text, exp_code=400)
        self.assertEqual(self.get_rows(), [])

    def test_unknown_column_rejected(self):
        self.bulk_upload("id,no_such_column\n1,x\n", exp_code=400)
        self.assertEqual(self.get_rows(), [])

    def test_empty_body_rejected(self):
        self.bulk_upload("", exp_code=400)
        self.assertEqual(self.get_rows(), [])

    def test_nonexistent_table_rejected(self):
        self.bulk_upload("id\n1\n", table="no_such_table", exp_code=404)

    def test_no_journal_rows_written(self):
        self.bulk_upload("id,name\n1,x\n2,y\n", exp_code=201)
        engine = _get_engine()
        journal = engine.execute(
            "SELECT to_regclass('_sandbox._test_table_insert');"
        ).scalar()
        if journal is not None:
            count = engine.execute(
                'SELECT count(*) FROM "_sandbox"."_test_table_insert";'
            ).scalar()
            self.assertEqual(count, 0)
