"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The stored Publish gate verdict on the tables tab (#2560, spec #2551): the
Publishable cell against the stored flag, the Publishable filter and sort,
and what a Table whose flag is still NULL does in each, as seen through HTTP.

Assertions are on what the page says (rows, counts, chips, options, links)
and what is logged, never on markup details or seconds.
"""  # noqa: 501

from login.tests.test_tables_columns import NO_LICENSE, OPEN_LICENSE
from login.tests.test_tables_tab import TablesTabTestCase

LOGGER = "oeplatform.publish_gate"


class StoredGateTestCase(TablesTabTestCase):
    def gated(self, name, stored, passing, **extra):
        """A Table whose stored verdict is ``stored`` (None: never computed)
        and whose metadata passes the live gate if ``passing``."""
        return self.table(
            name,
            publishable=stored,
            oemetadata=OPEN_LICENSE if passing else NO_LICENSE,
            **extra,
        )

    def row(self, name, query=None):
        return next(row for row in self.page(query).rows if row.table.name == name)


class PublishableCellTests(StoredGateTestCase):
    def test_a_stored_verdict_that_agrees_is_shown_and_nothing_is_logged(self):
        self.gated("t_yes", stored=True, passing=True)
        self.gated("t_no", stored=False, passing=False)
        with self.assertNoLogs(LOGGER):
            self.assertTrue(self.row("t_yes").publishable)
            self.assertFalse(self.row("t_no").publishable)

    def test_a_stale_pass_shows_the_live_failure_and_warns(self):
        self.gated("t_stale", stored=True, passing=False)
        with self.assertLogs(LOGGER, level="WARNING") as logs:
            row = self.row("t_stale")
        self.assertFalse(row.publishable)
        self.assertEqual(row.failed_label, "License")
        self.assertEqual(
            logs.output,
            [
                f"WARNING:{LOGGER}:publish_gate_disagreement "
                "table=t_stale stored=true live=false"
            ],
        )

    def test_a_stale_failure_shows_the_live_pass_and_warns(self):
        self.gated("t_fixed", stored=False, passing=True)
        with self.assertLogs(LOGGER, level="WARNING") as logs:
            self.assertTrue(self.row("t_fixed").publishable)
        self.assertIn("table=t_fixed stored=false live=true", logs.output[0])

    def test_no_stored_verdict_shows_the_live_result_and_logs_nothing(self):
        self.gated("t_new_ok", stored=None, passing=True)
        self.gated("t_new_bad", stored=None, passing=False)
        with self.assertNoLogs(LOGGER):
            self.assertTrue(self.row("t_new_ok").publishable)
            self.assertFalse(self.row("t_new_bad").publishable)


class PublishableFilterTests(StoredGateTestCase):
    def setUp(self):
        super().setUp()
        self.gated("t_yes", stored=True, passing=True)
        self.gated("t_no", stored=False, passing=False, published=True)
        self.gated("t_unknown", stored=None, passing=True)

    def test_yes_and_no_list_the_stored_verdicts(self):
        self.assertEqual(self.names({"publishable": "yes"}), ["t_yes"])
        self.assertEqual(self.names({"publishable": "no"}), ["t_no"])

    def test_a_table_never_computed_matches_neither_value(self):
        """Nothing is known about it until the recompute ran, so neither
        value can claim it; unfiltered, it is listed as usual."""
        listed = self.names({"publishable": "yes"}) + self.names({"publishable": "no"})
        self.assertNotIn("t_unknown", listed)
        self.assertIn("t_unknown", self.names())

    def test_the_stored_verdict_decides_even_when_the_live_one_disagrees(self):
        self.gated("t_stale", stored=True, passing=False)
        with self.assertLogs(LOGGER, level="WARNING"):
            rows = self.page({"publishable": "yes"}).rows
        self.assertEqual([r.table.name for r in rows], ["t_stale", "t_yes"])
        # listed by the stored verdict, shown by the live one
        self.assertFalse(rows[0].publishable)

    def test_the_options_are_yes_and_no_in_the_primary_row(self):
        controls = {c.param: c for c in self.page().controls}
        control = controls["publishable"]
        self.assertFalse(control.more)
        self.assertEqual(control.blank, "Publishable: any")
        self.assertEqual(
            [(o.value, o.label) for o in control.options],
            [("yes", "Publishable"), ("no", "Not publishable")],
        )

    def test_the_chip_reads_as_a_word(self):
        chips = self.page({"publishable": "no"}).chips
        self.assertEqual(
            [(c.text, c.stale) for c in chips], [("Not publishable", False)]
        )

    def test_an_unknown_value_is_a_stale_chip_and_filters_nothing(self):
        page = self.page({"publishable": "maybe"})
        self.assertEqual(len(page.rows), 3)
        self.assertEqual(
            [(c.text, c.stale) for c in page.chips],
            [("Filter ‹Publishable: maybe› no longer applies", True)],
        )

    def test_the_status_counts_follow_it(self):
        self.assertEqual(
            self.counts({"publishable": "no"}),
            {"seg-all": 1, "seg-draft": 0, "seg-published": 1},
        )

    def test_it_combines_with_the_other_filters(self):
        self.assertEqual(self.names({"publishable": "yes", "search": "no"}), [])
        self.assertEqual(
            self.names({"publishable": "no", "status": "published"}), ["t_no"]
        )

    def test_the_url_keeps_it(self):
        response = self.get({"publishable": "yes", "sort": "-status"}, htmx=True)
        self.assertEqual(
            response["HX-Push-Url"], f"{self.path}?publishable=yes&sort=-status"
        )


class PublishableSortTests(StoredGateTestCase):
    def setUp(self):
        super().setUp()
        self.gated("b_yes", stored=True, passing=True)
        self.gated("a_yes", stored=True, passing=True)
        self.gated("c_no", stored=False, passing=False)
        self.gated("a_unknown", stored=None, passing=True)

    def test_ascending_puts_not_publishable_first_and_unknown_last(self):
        self.assertEqual(
            self.names({"sort": "publishable"}),
            ["c_no", "a_yes", "b_yes", "a_unknown"],
        )

    def test_descending_puts_publishable_first_and_unknown_still_last(self):
        self.assertEqual(
            self.names({"sort": "-publishable"}),
            ["a_yes", "b_yes", "c_no", "a_unknown"],
        )

    def test_the_publishable_header_sorts_then_toggles(self):
        link = self.page().sort_links["publishable"]
        self.assertEqual((link.id, link.active), ("sort-publishable", False))
        self.assertEqual(link.url, f"{self.path}?sort=publishable")
        link = self.page({"sort": "publishable"}).sort_links["publishable"]
        self.assertEqual((link.active, link.aria_sort), (True, "ascending"))
        self.assertEqual(link.url, f"{self.path}?sort=-publishable")
