"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The Created column of the tables tab (#2559, spec #2551): a real creation
date or "before Nov 2025", its sort (unknowns count as the oldest) and the
Created date range filter (an unknown matches only a range that certainly
holds it), as seen through HTTP. ``created`` is set directly here, after the
Table is made, because ``auto_now_add`` overrides any value given on create.
What migration dataedit.0057 writes is ``dataedit/tests/test_created_migration.py``.

Assertions are on what the page says (rows, order, counts, chips, links,
headers), never on markup details or seconds.
"""  # noqa: 501

from datetime import date, datetime, time

from django.utils import timezone

from dataedit.models import Table
from login.tables_tab import CREATED_UNKNOWN_NOTE
from login.tests.test_tables_tab import TablesTabTestCase


def at(day, hour=12, minute=0):
    """A moment on ``day`` in the platform's own time zone."""
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


NOV_5_2025, MAR_14_2026, OCT_3_2026 = (
    date(2025, 11, 5),
    date(2026, 3, 14),
    date(2026, 10, 3),
)


class CreatedTestCase(TablesTabTestCase):
    def created(self, name, created=None, **extra):
        table = self.table(name, **extra)
        Table.objects.filter(pk=table.pk).update(created=created)
        return table

    def row(self, name, query=None):
        return next(row for row in self.page(query).rows if row.table.name == name)


class CreatedColumnTests(CreatedTestCase):
    def test_a_recorded_creation_is_shown(self):
        self.created("t_new", at(MAR_14_2026))
        row = self.row("t_new")
        self.assertEqual(row.created, at(MAR_14_2026))
        self.assertEqual(row.created_note, "")

    def test_an_unrecorded_creation_reads_before_nov_2025(self):
        self.created("t_old")
        row = self.row("t_old")
        self.assertIsNone(row.created)
        self.assertEqual(
            row.created_note,
            "Created before the platform began recording creation dates, "
            "on 30 Oct 2025.",
        )
        self.assertContains(self.get(), "before Nov 2025")

    def test_it_never_shows_the_date_updated_of_an_old_table(self):
        """For an old Table ``date_updated`` holds a date its metadata
        declared (migration 0044). The column must not present it."""
        table = self.created("t_old")
        Table.objects.filter(pk=table.pk).update(date_updated=at(date(2019, 5, 1)))
        response = self.get()
        self.assertIsNone(self.row("t_old").created)
        self.assertContains(response, CREATED_UNKNOWN_NOTE)
        self.assertNotContains(response, "1 May 2019")

    def test_screen_readers_get_the_note_as_text(self):
        self.created("t_old")
        self.created("t_new", at(MAR_14_2026))
        # once on hover, once as text, for the one unknown row only
        self.assertContains(self.get(), CREATED_UNKNOWN_NOTE, count=2)

    def test_a_new_table_has_a_creation_date(self):
        before = timezone.now()
        self.table("t_made_now")
        self.assertTrue(before <= self.row("t_made_now").created <= timezone.now())


class CreatedSortTests(CreatedTestCase):
    def setUp(self):
        super().setUp()
        self.created("t_nov", at(NOV_5_2025))
        self.created("t_unknown")
        self.created("t_oct", at(OCT_3_2026))
        self.created("t_mar", at(MAR_14_2026))

    def test_oldest_first_puts_unknowns_first(self):
        self.assertEqual(
            self.names({"sort": "created"}), ["t_unknown", "t_nov", "t_mar", "t_oct"]
        )

    def test_newest_first_puts_unknowns_last(self):
        self.assertEqual(
            self.names({"sort": "-created"}), ["t_oct", "t_mar", "t_nov", "t_unknown"]
        )

    def test_unknowns_among_themselves_break_by_title(self):
        self.created("t_also_unknown", title="Aardvark")
        self.assertEqual(
            self.names({"sort": "created"})[:2], ["t_also_unknown", "t_unknown"]
        )
        self.assertEqual(
            self.names({"sort": "-created"})[-2:], ["t_also_unknown", "t_unknown"]
        )

    def test_the_header_offers_it_and_turns_it_round(self):
        link = self.page().sort_links["created"]
        self.assertFalse(link.active)
        self.assertEqual(link.url, f"{self.path}?sort=created")
        link = self.page({"sort": "created"}).sort_links["created"]
        self.assertTrue(link.active)
        self.assertFalse(link.descending)
        self.assertEqual(link.url, f"{self.path}?sort=-created")

    def test_the_sort_is_written_into_the_url(self):
        response = self.get({"sort": "-created"}, htmx=True)
        self.assertEqual(response["HX-Push-Url"], f"{self.path}?sort=-created")

    def test_sort_by_names_both_directions(self):
        options = {o.value: o.label for o in self.page().sort_options}
        self.assertEqual(options["created"], "Created: oldest first")
        self.assertEqual(options["-created"], "Created: newest first")

    def test_the_default_sort_is_still_modified(self):
        self.assertEqual(self.page().state.sort, "-modified")


class CreatedRangeFilterTests(CreatedTestCase):
    def setUp(self):
        super().setUp()
        self.created("t_nov", at(NOV_5_2025, 10))
        self.created("t_mar", at(MAR_14_2026, 0, 30), published=True)
        self.created("t_oct", at(OCT_3_2026))
        self.created("t_unknown")

    def test_from_a_day_on(self):
        self.assertEqual(
            self.names({"created_from": "2026-03-14", "sort": "created"}),
            ["t_mar", "t_oct"],
        )

    def test_up_to_a_day_includes_that_day(self):
        self.assertIn("t_mar", self.names({"created_to": "2026-03-14"}))
        self.assertNotIn("t_oct", self.names({"created_to": "2026-03-14"}))

    def test_between_two_days(self):
        self.assertEqual(
            self.names({"created_from": "2025-11-01", "created_to": "2026-03-31"}),
            ["t_mar", "t_nov"],
        )

    def test_a_day_is_the_platforms_local_day(self):
        """00:30 on 14 Mar in Berlin is 23:30 on 13 Mar in UTC; the list
        shows 14 Mar, so that is the day it filters on."""
        self.assertNotIn("t_mar", self.names({"created_to": "2026-03-13"}))
        self.assertIn("t_mar", self.names({"created_from": "2026-03-14"}))

    def test_an_unknown_matches_an_open_start_ending_on_or_after_the_rollout(self):
        """Every Table without a creation date existed when recording began,
        on 30 Oct 2025, so a range up to that day or later certainly holds
        it."""
        for last in ("2025-10-30", "2025-10-31", "2026-03-14", "9999-12-31"):
            with self.subTest(created_to=last):
                self.assertIn("t_unknown", self.names({"created_to": last}))

    def test_an_unknown_does_not_match_a_range_ending_before_the_rollout(self):
        """Created by 30 Oct 2025 (recording began that afternoon) is not
        certainly by 29 Oct."""
        self.assertEqual(self.names({"created_to": "2025-10-29"}), [])

    def test_an_unknown_does_not_match_a_range_with_a_lower_end(self):
        for query in (
            {"created_from": "1900-01-01"},
            {"created_from": "1900-01-01", "created_to": "2999-12-31"},
            {"created_from": "0001-01-01", "created_to": "2026-03-14"},
        ):
            with self.subTest(query=query):
                self.assertNotIn("t_unknown", self.names(query))

    def test_one_chip_for_the_range(self):
        for query, text in (
            (
                {"created_from": "2025-11-01", "created_to": "2026-03-31"},
                "Created: 1 Nov 2025 – 31 Mar 2026",
            ),
            ({"created_from": "2025-11-01"}, "Created: from 1 Nov 2025"),
            ({"created_to": "2026-03-31"}, "Created: until 31 Mar 2026"),
        ):
            with self.subTest(query=query):
                chips = self.page(query).chips
                self.assertEqual([(c.text, c.stale) for c in chips], [(text, False)])

    def test_removing_the_chip_clears_both_ends_and_keeps_the_rest(self):
        page = self.page(
            {
                "created_from": "2025-11-01",
                "created_to": "2026-03-31",
                "modified_to": "2026-10-01",
            }
        )
        [chip] = [c for c in page.chips if c.text.startswith("Created")]
        self.assertEqual(chip.url, f"{self.path}?modified_to=2026-10-01")

    def test_it_counts_once_behind_more_filters_and_filters(self):
        page = self.page({"created_from": "2025-11-01", "created_to": "2026-03-31"})
        self.assertEqual(page.more_count, 1)
        self.assertEqual(page.folded_count, 1)

    def test_the_url_keeps_both_ends_in_order(self):
        response = self.get(
            {"created_to": "2026-03-31", "created_from": "2025-11-01"}, htmx=True
        )
        self.assertEqual(
            response["HX-Push-Url"],
            f"{self.path}?created_from=2025-11-01&created_to=2026-03-31",
        )

    def test_the_status_counts_follow_it(self):
        self.assertEqual(
            self.counts({"created_to": "2026-03-31"}),
            {"seg-all": 3, "seg-draft": 2, "seg-published": 1},
        )

    def test_it_combines_with_modified(self):
        Table.objects.filter(name="t_unknown").update(data_modified=at(OCT_3_2026))
        self.assertEqual(
            self.names({"created_to": "2026-03-31", "modified_from": "2026-10-01"}),
            ["t_unknown"],
        )

    def test_the_control_sits_behind_more_filters_before_modified(self):
        controls = [c for c in self.page({"created_to": "2026-03-31"}).controls]
        params = [c.param for c in controls if c.kind == "range"]
        self.assertEqual(params, ["created", "modified"])
        control = controls[[c.param for c in controls].index("created")]
        self.assertTrue(control.more)
        self.assertEqual(
            [(end.param, end.value) for end in control.ends],
            [("created_from", ""), ("created_to", "2026-03-31")],
        )
