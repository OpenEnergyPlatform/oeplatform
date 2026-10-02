"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The Modified column of the tables tab (#2557, spec #2551): the greater of a
Table's two stamps, the default sort it becomes, and the Modified date range
filter, as seen through HTTP. The stamps themselves are written by the write
paths (``api/tests/test_modification_stamps.py``); here they are set
directly, so that each test knows them to the second.

Assertions are on what the page says (rows, order, counts, chips, links,
headers), never on markup details or seconds.
"""  # noqa: 501

from datetime import date, datetime, time
from urllib.parse import parse_qs, urlsplit

from django.utils import timezone

from dataedit.models import Table
from login.tables_tab import MODIFIED_RECORDED_SINCE
from login.tests.test_table_actions import ActionTestCase
from login.tests.test_tables_tab import TablesTabTestCase


def at(day, hour=12, minute=0):
    """A moment on ``day`` in the platform's own time zone."""
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


OCT_1, OCT_2, OCT_3 = date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3)


class ModifiedTestCase(TablesTabTestCase):
    def modified(self, name, data=None, metadata=None, **extra):
        return self.table(name, data_modified=data, metadata_modified=metadata, **extra)

    def row(self, name, query=None):
        return next(row for row in self.page(query).rows if row.table.name == name)


class ModifiedColumnTests(ModifiedTestCase):
    def test_the_later_of_the_two_halves_is_shown(self):
        self.modified("t_meta_later", data=at(OCT_1), metadata=at(OCT_3))
        self.modified("t_data_later", data=at(OCT_3), metadata=at(OCT_1))
        self.assertEqual(self.row("t_meta_later").modified, at(OCT_3))
        self.assertEqual(self.row("t_data_later").modified, at(OCT_3))
        for name in ("t_meta_later", "t_data_later"):
            self.assertEqual(self.row(name).modified_note, "")

    def test_only_the_data_half_known_is_marked(self):
        self.modified("t_data_only", data=at(OCT_2))
        row = self.row("t_data_only")
        self.assertEqual(row.modified, at(OCT_2))
        self.assertTrue(row.data_only)
        self.assertEqual(
            row.modified_note,
            "Last data change. Metadata edits are recorded since "
            f"{MODIFIED_RECORDED_SINCE}.",
        )

    def test_only_the_metadata_half_known_is_not_marked(self):
        """A data half that is unknown means no data change was recorded, not
        that the date shown is incomplete: metadata is recorded throughout."""
        self.modified("t_meta_only", metadata=at(OCT_2))
        row = self.row("t_meta_only")
        self.assertEqual(row.modified, at(OCT_2))
        self.assertFalse(row.data_only)
        self.assertEqual(row.modified_note, "")

    def test_neither_known_reads_unknown(self):
        self.modified("t_never")
        row = self.row("t_never")
        self.assertIsNone(row.modified)
        self.assertEqual(
            row.modified_note, f"No change recorded since {MODIFIED_RECORDED_SINCE}."
        )

    def test_screen_readers_get_the_note_as_text(self):
        """The marker and the dash explain themselves on hover; a screen
        reader gets the same sentence as text."""
        self.modified("t_data_only", data=at(OCT_2))
        self.modified("t_never")
        response = self.get()
        self.assertContains(response, "Last data change.", count=2)
        self.assertContains(response, "No change recorded since", count=2)


class DefaultSortTests(ModifiedTestCase):
    def setUp(self):
        super().setUp()
        self.modified("t_oct1", data=at(OCT_1))
        self.modified("t_unknown")
        self.modified("t_oct3", metadata=at(OCT_3))
        self.modified("t_oct2", data=at(OCT_2), metadata=at(OCT_1))

    def test_the_bare_url_is_newest_first_with_unknowns_last(self):
        self.assertEqual(self.names(), ["t_oct3", "t_oct2", "t_oct1", "t_unknown"])

    def test_oldest_first_keeps_unknowns_last(self):
        self.assertEqual(
            self.names({"sort": "modified"}),
            ["t_oct1", "t_oct2", "t_oct3", "t_unknown"],
        )

    def test_equal_dates_break_by_title_then_key(self):
        self.modified("t_same_b", title="Beta", data=at(OCT_2), metadata=at(OCT_1))
        self.modified("t_same_a", title="alpha", data=at(OCT_2))
        self.assertEqual(self.names()[1:4], ["t_same_a", "t_same_b", "t_oct2"])

    def test_unknowns_among_themselves_break_by_title(self):
        self.modified("t_also_unknown", title="Aardvark")
        self.assertEqual(self.names()[-2:], ["t_also_unknown", "t_unknown"])

    def test_the_default_is_never_written_into_the_url(self):
        page = self.page()
        self.assertEqual(page.state.sort, "-modified")
        self.assertEqual(page.url, self.path)
        response = self.get(htmx=True)
        self.assertEqual(response["HX-Push-Url"], self.path)

    def test_the_title_sort_is_now_written(self):
        response = self.get({"sort": "table"}, htmx=True)
        self.assertEqual(response["HX-Push-Url"], f"{self.path}?sort=table")

    def test_the_header_shows_the_default_and_turns_it_round(self):
        link = self.page().sort_links["modified"]
        self.assertTrue(link.active)
        self.assertTrue(link.descending)
        self.assertEqual(link.url, f"{self.path}?sort=modified")
        self.assertEqual(
            self.page({"sort": "modified"}).sort_links["modified"].url, self.path
        )

    def test_sort_by_names_both_directions(self):
        options = {o.value: o.label for o in self.page().sort_options}
        self.assertEqual(options["modified"], "Modified: oldest first")
        self.assertEqual(options["-modified"], "Modified: newest first")
        selected = [o.value for o in self.page().sort_options if o.selected]
        self.assertEqual(selected, ["-modified"])


class RangeFilterTests(ModifiedTestCase):
    def setUp(self):
        super().setUp()
        self.modified("t_oct1", data=at(OCT_1, 10))
        # the metadata half is the later one, and decides
        self.modified(
            "t_meta_late", data=at(date(2026, 9, 1)), metadata=at(OCT_2, 23, 30)
        )
        self.modified("t_data_only", data=at(OCT_2, 0, 30))
        self.modified("t_oct3", data=at(OCT_3, 0, 30), published=True)
        self.modified("t_unknown")

    def test_from_a_day_on(self):
        self.assertEqual(
            self.names({"modified_from": "2026-10-02"}),
            ["t_oct3", "t_meta_late", "t_data_only"],
        )

    def test_up_to_a_day_includes_that_day(self):
        self.assertEqual(
            self.names({"modified_to": "2026-10-02"}),
            ["t_meta_late", "t_data_only", "t_oct1"],
        )

    def test_between_two_days(self):
        self.assertEqual(
            self.names({"modified_from": "2026-10-02", "modified_to": "2026-10-02"}),
            ["t_meta_late", "t_data_only"],
        )

    def test_a_day_is_the_platforms_local_day(self):
        """00:30 on 3 Oct in Berlin is 22:30 on 2 Oct in UTC; the list shows
        3 Oct, so that is the day it filters on."""
        self.assertNotIn("t_oct3", self.names({"modified_to": "2026-10-02"}))
        self.assertIn("t_oct3", self.names({"modified_from": "2026-10-03"}))

    def test_an_unknown_date_matches_no_range(self):
        for query in (
            {"modified_from": "1900-01-01"},
            {"modified_to": "2999-12-31"},
            {"modified_from": "1900-01-01", "modified_to": "2999-12-31"},
        ):
            with self.subTest(query=query):
                self.assertNotIn("t_unknown", self.names(query))

    def test_a_data_only_date_is_filtered_on_the_date_shown(self):
        self.assertIn("t_data_only", self.names({"modified_from": "2026-10-02"}))

    def test_the_earlier_half_does_not_count(self):
        self.assertEqual(
            self.names({"modified_from": "2026-09-01", "modified_to": "2026-09-01"}),
            [],
        )

    def test_one_chip_for_the_range(self):
        for query, text in (
            (
                {"modified_from": "2026-10-02", "modified_to": "2026-10-03"},
                "Modified: 2 Oct 2026 – 3 Oct 2026",
            ),
            ({"modified_from": "2026-10-02"}, "Modified: from 2 Oct 2026"),
            ({"modified_to": "2026-10-02"}, "Modified: until 2 Oct 2026"),
        ):
            with self.subTest(query=query):
                chips = self.page(query).chips
                self.assertEqual([(c.text, c.stale) for c in chips], [(text, False)])

    def test_removing_the_chip_clears_both_ends_and_keeps_the_rest(self):
        page = self.page(
            {"modified_from": "2026-10-02", "modified_to": "2026-10-03", "search": "t_"}
        )
        [chip] = [c for c in page.chips if c.text.startswith("Modified")]
        self.assertEqual(chip.url, f"{self.path}?search=t_")

    def test_reset_clears_both_ends(self):
        page = self.page({"modified_from": "2026-10-02", "modified_to": "2026-10-03"})
        self.assertEqual(page.reset_url, self.path)

    def test_it_counts_once_behind_more_filters_and_filters(self):
        page = self.page({"modified_from": "2026-10-02", "modified_to": "2026-10-03"})
        self.assertEqual(page.more_count, 1)
        self.assertEqual(page.folded_count, 1)
        self.assertEqual(self.page({"modified_to": "2026-10-03"}).more_count, 1)

    def test_the_url_keeps_both_ends_in_order(self):
        response = self.get(
            {"modified_to": "2026-10-03", "modified_from": "2026-10-02"}, htmx=True
        )
        self.assertEqual(
            response["HX-Push-Url"],
            f"{self.path}?modified_from=2026-10-02&modified_to=2026-10-03",
        )

    def test_a_filter_change_returns_to_page_one(self):
        page = self.page({"page": "2"})
        url = page.state.url(self.path, modified_from="2026-10-02")
        self.assertEqual(
            parse_qs(urlsplit(url).query), {"modified_from": ["2026-10-02"]}
        )

    def test_an_unreadable_date_is_ignored_and_dropped(self):
        """Only a hand-edited address carries one: a date input sends ISO
        dates or nothing. Like an unreadable page number, it is dropped."""
        page = self.page({"modified_from": "yesterday", "modified_to": "2026-10-02"})
        self.assertEqual(
            [r.table.name for r in page.rows], ["t_meta_late", "t_data_only", "t_oct1"]
        )
        self.assertEqual(page.url, f"{self.path}?modified_to=2026-10-02")
        self.assertEqual([c.text for c in page.chips], ["Modified: until 2 Oct 2026"])

    def test_nothing_readable_is_no_filter(self):
        page = self.page({"modified_from": "soon", "modified_to": ""})
        self.assertEqual(len(page.rows), 5)
        self.assertEqual(page.chips, [])
        self.assertEqual(page.folded_count, 0)

    def test_the_status_counts_follow_it(self):
        self.assertEqual(
            self.counts({"modified_from": "2026-10-02"}),
            {"seg-all": 3, "seg-draft": 2, "seg-published": 1},
        )

    def test_the_control_sits_behind_more_filters_holding_both_ends(self):
        controls = {
            c.param: c for c in self.page({"modified_from": "2026-10-02"}).controls
        }
        control = controls["modified"]
        self.assertTrue(control.more)
        self.assertEqual(control.kind, "range")
        self.assertEqual(
            [(end.param, end.value) for end in control.ends],
            [("modified_from", "2026-10-02"), ("modified_to", "")],
        )

    def test_the_bar_is_told_both_ends(self):
        """The bar outside the region follows ``data-filters`` after a swap,
        so a removed chip empties both date inputs."""
        page = self.page({"modified_from": "2026-10-02", "search": "t"})
        self.assertIn('"modified_from": "2026-10-02"', page.filters_json)


class StatusActionsDoNotStampTests(ActionTestCase):
    """Publishing from the row is status, not content."""

    def test_publishing_and_unpublishing_from_the_row(self):
        self.draft("t_row")
        response = self.run_action("publish", "t_row", topic="climate", embargo="none")
        self.assertEqual(response.status_code, 204)
        response = self.run_action("unpublish", "t_row")
        self.assertEqual(response.status_code, 204)
        table = Table.objects.get(name="t_row")
        self.assertEqual((table.data_modified, table.metadata_modified), (None, None))
