"""Tests for the Bulk Upload endpoint (issue #2362, slice 2).

Bulk Upload is the high-throughput, append-only write path: the request body
is the CSV, rows go directly into the main table without edit-journal
records, all-or-nothing per request.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import gzip
import json
from datetime import timedelta

from django.utils import timezone

from api.tests import APITestCaseWithTable
from dataedit.models import BulkLoadEvent, Embargo, Table
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
        event = BulkLoadEvent.objects.latest("created")
        self.assertEqual(event.status, BulkLoadEvent.STATUS_EMBARGO)
        self.assertEqual(event.table_name, self.test_table)

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

    def test_column_order_is_free(self):
        self.bulk_upload("name,id\nswapped,7\n", exp_code=201)
        rows = self.get_rows()
        self.assertEqual(rows[0]["id"], 7)
        self.assertEqual(rows[0]["name"], "swapped")

    def test_duplicate_header_columns_rejected(self):
        result = self.bulk_upload("id,name,name\n1,x,y\n", exp_code=400)
        self.assertIn("name", json.dumps(result))
        self.assertEqual(self.get_rows(), [])

    def test_missing_required_column_rejected(self):
        required_table = "test_table_required"
        self.create_table(
            structure={
                "columns": [
                    {"name": "id", "data_type": "bigserial", "is_nullable": False},
                    {
                        "name": "req_col",
                        "data_type": "character varying",
                        "is_nullable": False,
                        "character_maximum_length": 50,
                    },
                    {
                        "name": "opt_col",
                        "data_type": "character varying",
                        "is_nullable": True,
                        "character_maximum_length": 50,
                    },
                ]
            },
            table=required_table,
        )
        # without req_col: rejected before streaming, names the column
        result = self.bulk_upload(
            "id,opt_col\n1,x\n", table=required_table, exp_code=400
        )
        self.assertIn("req_col", json.dumps(result))
        # with req_col (id omitted is fine - bigserial has a default): accepted
        self.bulk_upload("req_col\nfilled\n", table=required_table, exp_code=201)
        self.drop_table(table=required_table)

    def test_bom_header_parses(self):
        self.bulk_upload("\ufeffid,name\n1,bommed\n", exp_code=201)
        self.assertEqual(self.get_rows()[0]["name"], "bommed")

    def test_empty_fields_are_null_quoted_or_not(self):
        self.bulk_upload('id,name,address\n1,,""\n', exp_code=201)
        row = self.get_rows()[0]
        self.assertIsNone(row["name"])  # unquoted empty field
        self.assertIsNone(row["address"])  # quoted empty field (FORCE_NULL)

    def test_error_names_csv_line_and_column_without_internals(self):
        result = self.bulk_upload("id,name\n1,ok\nboom,bad\n", exp_code=400)
        message = json.dumps(result)
        self.assertIn("line 3", message)  # header is line 1, bad row is line 3
        self.assertIn("id", message)
        self.assertIn("boom", message)  # the offending value helps debugging
        self.assertNotIn("Traceback", message)
        self.assertNotIn("COPY ", message)  # no raw SQL / context dump
        self.assertNotIn("STDIN", message)
        self.assertEqual(self.get_rows(), [])

    def test_upload_without_id_column_uses_sequence(self):
        self.bulk_upload("name\nfirst\nsecond\n", exp_code=201)
        ids = sorted(r["id"] for r in self.get_rows())
        self.assertEqual(len(set(ids)), 2)

    def test_explicit_ids_then_row_upload_does_not_collide(self):
        self.bulk_upload("id,name\n10,a\n11,b\n", exp_code=201)
        # a subsequent Row Upload must get a fresh id beyond the bulk ids
        self.api_req(
            "post", path="rows/new", data={"query": {"name": "after"}}, exp_code=201
        )
        rows = self.get_rows()
        self.assertEqual(len(rows), 3)
        new_id = next(r["id"] for r in rows if r["name"] == "after")
        self.assertGreater(new_id, 11)

    def test_id_above_sanity_bound_rejected(self):
        huge = 2**48 + 1
        result = self.bulk_upload(f"id,name\n{huge},x\n", exp_code=400)
        self.assertIn(str(2**48), json.dumps(result))  # error names the bound
        self.assertEqual(self.get_rows(), [])  # fully rolled back

    def test_preexisting_high_id_does_not_block_uploads(self):
        # a huge id inserted via the row API (which enforces no bound) must
        # not poison the table for id-bearing bulk uploads afterwards
        huge = 2**48 + 5
        self.api_req(
            "post",
            path="rows/new",
            data={"query": {"id": huge, "name": "old"}},
            exp_code=201,
        )
        self.bulk_upload("id,name\n1,new\n", exp_code=201)
        self.assertEqual(len(self.get_rows()), 2)

    def test_sequence_never_moves_backwards(self):
        self.bulk_upload("id,name\n50,a\n", exp_code=201)
        self.bulk_upload("id,name\n20,b\n", exp_code=201)  # lower ids afterwards
        self.api_req(
            "post", path="rows/new", data={"query": {"name": "c"}}, exp_code=201
        )
        ids = {r["name"]: r["id"] for r in self.get_rows()}
        self.assertGreater(ids["c"], 50)

    def test_successful_upload_creates_event(self):
        result = self.bulk_upload("id,name\n5,a\n7,b\n", exp_code=201)
        event = BulkLoadEvent.objects.get(id=result["event_id"])
        self.assertEqual(event.status, BulkLoadEvent.STATUS_SUCCESS)
        self.assertEqual(event.table_name, self.test_table)
        self.assertEqual(event.user_id, self.user.id)
        self.assertEqual(event.row_count, 2)
        self.assertEqual(event.id_min, 5)
        self.assertEqual(event.id_max, 7)
        self.assertGreater(event.bytes_received, 0)

    def test_sequence_assigned_upload_records_id_range(self):
        self.bulk_upload("name\na\nb\nc\n", exp_code=201)
        event = BulkLoadEvent.objects.latest("created")
        ids = sorted(r["id"] for r in self.get_rows())
        self.assertEqual(event.id_min, ids[0])
        self.assertEqual(event.id_max, ids[-1])

    def test_failed_copy_creates_failure_event(self):
        self.bulk_upload("id,name\n1,ok\nboom,bad\n", exp_code=400)
        event = BulkLoadEvent.objects.latest("created")
        self.assertEqual(event.status, BulkLoadEvent.STATUS_COPY_ERROR)
        self.assertGreater(event.bytes_received, 0)
        self.assertIn("boom", event.error_message)
        # the data transaction rolled back, but the event persists
        self.assertEqual(self.get_rows(), [])

    def test_header_validation_failure_creates_event(self):
        self.bulk_upload("id,no_such_column\n1,x\n", exp_code=400)
        event = BulkLoadEvent.objects.latest("created")
        self.assertEqual(event.status, BulkLoadEvent.STATUS_VALIDATION_ERROR)

    def test_events_registered_in_admin(self):
        from django.contrib import admin

        self.assertIn(BulkLoadEvent, admin.site._registry)
        model_admin = admin.site._registry[BulkLoadEvent]
        self.assertIn("status", model_admin.list_filter)

    def gzip_upload(self, csv_text: str, exp_code: int | None = None) -> dict:
        url = f"/api/v0/tables/{self.test_table}/bulk-upload/?delimiter=comma"
        resp = self.client.post(
            url,
            data=gzip.compress(csv_text.encode("utf-8")),
            content_type="text/csv",
            HTTP_CONTENT_ENCODING="gzip",
            HTTP_AUTHORIZATION=f"Token {self.token}",
        )
        if exp_code is not None:
            self.assertEqual(resp.status_code, exp_code, resp.content[:500])
        try:
            return json.loads(resp.content)
        except ValueError:
            return {}

    def test_gzip_upload_matches_plain(self):
        result = self.gzip_upload("id,name,address\n1,gz,ip\n2,zip,ped\n", 201)
        self.assertEqual(result["rows"], 2)
        by_id = {r["id"]: r for r in self.get_rows()}
        self.assertEqual(by_id[1]["name"], "gz")
        self.assertEqual(by_id[2]["address"], "ped")

    def test_decompressed_size_cap_rejects_with_413(self):
        rows = "".join(f"{i},{'x' * 50}\n" for i in range(1, 50))
        with self.settings(BULK_UPLOAD_MAX_BYTES=500):
            result = self.bulk_upload("id,name\n" + rows, exp_code=413)
        self.assertIn("500", json.dumps(result))  # names the cap
        self.assertEqual(self.get_rows(), [])  # rolled back
        event = BulkLoadEvent.objects.latest("created")
        self.assertEqual(event.status, BulkLoadEvent.STATUS_SIZE_CAP)

    def test_gzip_bomb_cut_off_at_cap(self):
        # several MB of repetitive CSV compress to a few KB; the cap must
        # stop the expansion, not the wire size (names stay within the
        # column's varchar(50) so the cap fires, not a data error)
        bomb_rows = "".join(f"{i},{'a' * 40}\n" for i in range(1, 200_000))
        with self.settings(BULK_UPLOAD_MAX_BYTES=10_000):
            self.gzip_upload("id,name\n" + bomb_rows, 413)
        self.assertEqual(self.get_rows(), [])

    def test_truncated_gzip_mid_body_rolls_back(self):
        # header parses fine, then the compressed stream ends prematurely
        # during COPY - must roll back like any other failure
        csv_text = "id,name\n" + "".join(f"{i},row{i}\n" for i in range(1, 20_000))
        body = gzip.compress(csv_text.encode("utf-8"))
        url = f"/api/v0/tables/{self.test_table}/bulk-upload/?delimiter=comma"
        resp = self.client.post(
            url,
            data=body[: len(body) // 2],  # cut mid-stream
            content_type="text/csv",
            HTTP_CONTENT_ENCODING="gzip",
            HTTP_AUTHORIZATION=f"Token {self.token}",
        )
        self.assertEqual(resp.status_code, 400, resp.content[:300])
        self.assertEqual(self.get_rows(), [])

    def test_invalid_gzip_rejected(self):
        url = f"/api/v0/tables/{self.test_table}/bulk-upload/?delimiter=comma"
        resp = self.client.post(
            url,
            data=b"id,name\n1,not-actually-gzip\n",
            content_type="text/csv",
            HTTP_CONTENT_ENCODING="gzip",
            HTTP_AUTHORIZATION=f"Token {self.token}",
        )
        self.assertEqual(resp.status_code, 400, resp.content[:300])
        self.assertEqual(self.get_rows(), [])

    def test_concurrent_upload_same_user_rejected_429(self):
        from api.bulk_upload_guard import guard

        guard.acquire(self.user.id)
        try:
            url = f"/api/v0/tables/{self.test_table}/bulk-upload/?delimiter=comma"
            resp = self.client.post(
                url,
                data=b"id,name\n1,x\n",
                content_type="text/csv",
                HTTP_AUTHORIZATION=f"Token {self.token}",
            )
            self.assertEqual(resp.status_code, 429, resp.content[:300])
            self.assertTrue(resp.has_header("Retry-After"))
        finally:
            guard.release(self.user.id)
        self.assertEqual(self.get_rows(), [])

    def test_global_capacity_full_rejected_429(self):
        from api.bulk_upload_guard import guard

        with self.settings(BULK_UPLOAD_MAX_CONCURRENT=1):
            guard.acquire("someone-else")
            try:
                self.bulk_upload("id,name\n1,x\n", exp_code=429)
            finally:
                guard.release("someone-else")
        self.assertEqual(self.get_rows(), [])

    def test_stalled_upload_aborted_and_rolled_back(self):
        # an impossible minimum rate with no grace makes any real upload
        # count as stalled - the wall-clock variants live in the guard's
        # unit tests
        with self.settings(
            BULK_UPLOAD_MIN_BYTES_PER_SECOND=10**15,
            BULK_UPLOAD_STALL_GRACE_SECONDS=-1,
        ):
            self.bulk_upload("id,name\n1,x\n2,y\n", exp_code=408)
        self.assertEqual(self.get_rows(), [])
        event = BulkLoadEvent.objects.latest("created")
        self.assertEqual(event.status, BulkLoadEvent.STATUS_STALL)

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
