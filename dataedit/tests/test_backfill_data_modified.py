"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The ``backfill_data_modified`` command (#2558): it dates a Table's data half
from the later of its latest applied Edit Journal change and its latest
successful Bulk Load Event, writes nothing without ``--apply``, fills only a
NULL, never touches the metadata half, and never creates a journal it reads.
"""  # noqa: 501

from datetime import datetime, timezone
from io import StringIO
from unittest import mock

from django.core.management import call_command
from sqlalchemy import text

from api.tests import APITestCase
from dataedit.management.commands import backfill_data_modified
from dataedit.models import BulkLoadEvent, Table
from login.permissions import DELETE_PERM
from oedb.connection import _get_engine
from oedb.utils import OedbTableProxy, _OedbTable
from oeplatform.settings import SCHEMA_DEFAULT_TEST_SANDBOX

SANDBOX = SCHEMA_DEFAULT_TEST_SANDBOX
JOURNALS = f"_{SANDBOX}"

# Two names that differ only past the point where a journal name is clipped.
LONG = "bf_" + "x" * 60
SHARED_JOURNAL = f"_{LONG}_insert"[:63]


def at(month):
    return datetime(2025, month, 1, 12, tzinfo=timezone.utc)


AFTER_RELEASE = datetime(2026, 10, 3, 9, tzinfo=timezone.utc)


def oedb(sql, **params):
    return _get_engine().execute(text(sql).execution_options(autocommit=True), **params)


def journal_exists(name):
    return oedb(
        "SELECT to_regclass(:name) IS NOT NULL", name=f'"{JOURNALS}"."{name}"'
    ).scalar()


def journal_row(table, action, when, applied):
    """A change in one of ``table``'s Journal Tables, dated ``when``."""
    oedb(
        f'INSERT INTO "{JOURNALS}"."_{table}_{action}" '
        "(_user, _type, _submitted, _applied) VALUES "
        "('MrTest', :type, (:when)::timestamptz AT TIME ZONE "
        "current_setting('TimeZone'), :applied)",
        type=action,
        when=when,
        applied=applied,
    )


def redate_journal(table, action, when):
    oedb(
        f'UPDATE "{JOURNALS}"."_{table}_{action}" SET _submitted = '
        "(:when)::timestamptz AT TIME ZONE current_setting('TimeZone')",
        when=when,
    )


def bulk_load(table, when, status=BulkLoadEvent.STATUS_SUCCESS):
    event = BulkLoadEvent.objects.create(table_name=table, status=status)
    BulkLoadEvent.objects.filter(pk=event.pk).update(created=when)


class BackfillDataModifiedTests(APITestCase):
    """Five Tables, one per source:

    - ``bf_journal``: rows written and applied through the API, plus an applied
      edit (April) and a change still waiting for Apply (September);
    - ``bf_bulk``: successful Bulk Uploads in February and May, a failed one in
      August, and no OEDB table at all;
    - ``bf_both``: an applied journal change in June, a Bulk Upload in July;
    - ``bf_pending``: only a change still waiting for Apply;
    - ``bf_neither``: no journal and no Bulk Load Event.
    """

    API_TABLES = ("bf_journal", "bf_both", "bf_pending")

    def setUp(self):
        super().setUp()
        self.drop_oedb_tables()
        for name in self.API_TABLES:
            self.create_table(
                table=name, data=[{"id": 1}] if name != "bf_pending" else None
            )

        proxy = Table.objects.get(name="bf_journal").get_oedb_table_proxy()
        proxy._edit_table.get_sa_table()
        proxy._delete_table.get_sa_table()
        redate_journal("bf_journal", "insert", at(3))
        journal_row("bf_journal", "edit", at(4), applied=True)
        journal_row("bf_journal", "delete", at(9), applied=False)

        redate_journal("bf_both", "insert", at(6))
        bulk_load("bf_both", at(7))

        Table.objects.get(
            name="bf_pending"
        ).get_oedb_table_proxy()._insert_table.get_sa_table()
        journal_row("bf_pending", "insert", at(9), applied=False)

        Table.objects.bulk_create(
            [
                Table(name="bf_bulk", is_sandbox=True),
                Table(name="bf_neither", is_sandbox=True),
            ]
        )
        bulk_load("bf_bulk", at(2))
        bulk_load("bf_bulk", at(5))
        bulk_load("bf_bulk", at(8), status=BulkLoadEvent.STATUS_COPY_ERROR)

        # As before the release: the API's writes above stamped the field.
        Table.objects.update(data_modified=None)

    def tearDown(self):
        self.drop_oedb_tables()
        super().tearDown()

    def drop_oedb_tables(self):
        for name in self.API_TABLES:
            OedbTableProxy(
                name, schema_name=SANDBOX, permission_level=DELETE_PERM
            ).drop_if_exists()
        _OedbTable(SHARED_JOURNAL, JOURNALS, DELETE_PERM).drop_if_exists()

    def run_command(self, *args):
        out = StringIO()
        call_command("backfill_data_modified", *args, stdout=out)
        return out.getvalue()

    def dates(self):
        return dict(Table.objects.values_list("name", "data_modified"))

    def test_a_dry_run_reports_the_sources_and_writes_nothing(self):
        output = self.run_command()
        self.assertEqual(set(self.dates().values()), {None})
        self.assertIn("for 5 table(s)", output)
        self.assertIn("applied journal changes only: 1", output)
        self.assertIn("successful bulk loads only: 1", output)
        self.assertIn("both: 1", output)
        self.assertIn("neither, left unknown: 2", output)
        self.assertIn("already dated, left alone: 0", output)
        self.assertIn("Would date 3 table(s).", output)
        self.assertIn("Dry run, nothing was written.", output)

    def test_apply_dates_each_table_from_its_later_source(self):
        output = self.run_command("--apply")
        self.assertEqual(
            self.dates(),
            {
                "bf_journal": at(4),
                "bf_bulk": at(5),
                "bf_both": at(7),
                "bf_pending": None,
                "bf_neither": None,
            },
        )
        self.assertIn("Dated 3 table(s).", output)

    def test_a_change_waiting_for_apply_is_not_a_modification(self):
        self.run_command("--apply")
        dates = self.dates()
        # Both have a pending change dated September.
        self.assertEqual(dates["bf_journal"], at(4))
        self.assertIsNone(dates["bf_pending"])

    def test_the_metadata_half_and_date_updated_are_untouched(self):
        Table.objects.filter(name="bf_bulk").update(metadata_modified=at(1))
        before = list(
            Table.objects.order_by("name").values_list(
                "name", "metadata_modified", "date_updated"
            )
        )
        self.run_command("--apply")
        self.assertEqual(
            list(
                Table.objects.order_by("name").values_list(
                    "name", "metadata_modified", "date_updated"
                )
            ),
            before,
        )

    def test_a_table_that_already_has_a_date_keeps_it(self):
        # One stamped after the release, and one older than what the
        # journal would give: neither is overwritten.
        Table.objects.filter(name="bf_bulk").update(data_modified=AFTER_RELEASE)
        Table.objects.filter(name="bf_journal").update(data_modified=at(1))
        output = self.run_command("--apply")
        dates = self.dates()
        self.assertEqual(dates["bf_bulk"], AFTER_RELEASE)
        self.assertEqual(dates["bf_journal"], at(1))
        self.assertEqual(dates["bf_both"], at(7))
        self.assertIn("already dated, left alone: 2", output)
        self.assertIn("Dated 1 table(s).", output)

    def test_a_second_run_finds_nothing_to_date(self):
        self.run_command("--apply")
        first = self.dates()
        output = self.run_command("--apply")
        self.assertEqual(self.dates(), first)
        self.assertIn("already dated, left alone: 3", output)
        self.assertIn("Dated 0 table(s).", output)

    def test_a_stamp_during_the_run_wins(self):
        read = backfill_data_modified.latest_bulk_loads

        def stamped_meanwhile():
            Table.objects.get(name="bf_bulk").stamp_data_modified()
            return read()

        started = datetime.now(timezone.utc)
        with mock.patch.object(
            backfill_data_modified, "latest_bulk_loads", stamped_meanwhile
        ):
            output = self.run_command("--apply")
        self.assertGreaterEqual(self.dates()["bf_bulk"], started)
        self.assertIn("Dated 2 table(s).", output)
        self.assertIn("1 were stamped during the run, left alone", output)

    def test_no_missing_journal_is_created_by_reading(self):
        self.run_command()
        self.run_command("--apply")
        for name in ("bf_neither", "bf_bulk"):
            for action in ("insert", "edit", "delete"):
                self.assertFalse(journal_exists(f"_{name}_{action}"))

    def test_a_journal_two_tables_clip_to_is_skipped(self):
        Table.objects.bulk_create(
            [
                Table(name=LONG + "_a", is_sandbox=True),
                Table(name=LONG + "_b", is_sandbox=True),
            ]
        )
        oedb(
            f'CREATE TABLE "{JOURNALS}"."{SHARED_JOURNAL}" () '
            "INHERITS (public._edit_base)"
        )
        oedb(
            f'INSERT INTO "{JOURNALS}"."{SHARED_JOURNAL}" '
            "(_user, _type, _applied) VALUES ('MrTest', 'insert', true)"
        )
        output = self.run_command("--apply")
        dates = self.dates()
        self.assertIsNone(dates[LONG + "_a"])
        self.assertIsNone(dates[LONG + "_b"])
        self.assertIn(
            "skipped 1 journal(s) more than one table's name clips to", output
        )
