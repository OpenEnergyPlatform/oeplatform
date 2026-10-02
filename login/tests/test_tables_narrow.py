"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

What the tables tab offers a narrow list (#2555, spec #2551): where the rows
stack they lose their column headers, so the region carries a "Sort by"
select, and where the filter bar does not fit on one line everything in it
but Search folds behind "Filters (n)". Which of them shows at which width is CSS (container queries
in ``tables_tab.css``); happy-dom has no layout, so the thresholds are
measured in a real browser and written beside the queries, not tested here.

Assertions are on what the page says (options, counts, order of controls),
never on markup details or seconds.
"""  # noqa: 501

from login.tests.test_tables_filters import FilterTestCase


class SortSelectTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        self.table("t_one")

    def options(self, query=None):
        return [(o.value, o.label, o.selected) for o in self.page(query).sort_options]

    def test_every_sort_in_both_directions_least_done_first(self):
        self.assertEqual(
            [(value, label) for value, label, _ in self.options()],
            [
                ("table", "Table: A to Z"),
                ("-table", "Table: Z to A"),
                ("status", "Status: drafts first"),
                ("-status", "Status: published first"),
                ("publishable", "Publishable: not publishable first"),
                ("-publishable", "Publishable: publishable first"),
                ("review", "Review: not reviewed first"),
                ("-review", "Review: reviewed first"),
                ("datasets", "Datasets: fewest first"),
                ("-datasets", "Datasets: most first"),
            ],
        )

    def test_the_current_sort_is_selected(self):
        selected = [value for value, _, chosen in self.options() if chosen]
        self.assertEqual(selected, ["table"])
        selected = [
            value for value, _, chosen in self.options({"sort": "-review"}) if chosen
        ]
        self.assertEqual(selected, ["-review"])

    def test_an_unknown_sort_selects_the_default(self):
        selected = [
            value for value, _, chosen in self.options({"sort": "rows"}) if chosen
        ]
        self.assertEqual(selected, ["table"])

    def test_the_region_carries_it_so_it_follows_every_swap(self):
        response = self.get({"sort": "-status"}, htmx=True)
        self.assertContains(response, 'id="sort-select"')
        self.assertRegex(response.content.decode(), r'value="-status"\s+selected')

    def test_no_list_no_sort_select(self):
        response = self.get({"search": "nothing like it"}, htmx=True)
        self.assertNotContains(response, 'id="sort-select"')


class FilterFoldTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        organization = self.organization("Org Wind")
        table = self.table("t_one")
        self.grant(organization, table)
        self.topics(table, "climate")
        self.tag(table, "Wind")
        self.organization_pk = organization.pk

    def test_everything_but_search_sits_behind_the_toggle(self):
        body = self.get().content.decode()
        order = [
            'id="tables-search"',
            'id="tables-fold"',
            'id="tables-fold-panel"',
            'id="f-publishable"',
            'id="f-review"',
            'id="f-access"',
            'id="f-dataset"',
            'id="tables-more"',
            'id="tables-more-panel"',
            'id="f-topics"',
            'id="f-tags"',
            'id="tables-results"',
        ]
        positions = [body.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        panel = body[body.index('id="tables-fold-panel"') :]
        self.assertNotIn('id="tables-search"', panel)

    def test_the_toggle_counts_every_filter_behind_it_that_applies(self):
        self.assertEqual(self.page().folded_count, 0)
        query = {
            "search": "one",
            "publishable": "no",
            "review": "not_reviewed",
            "access": str(self.organization_pk),
            "topics": "climate",
            "tags": "wind",
        }
        self.assertEqual(self.page(query).folded_count, 5)

    def test_search_and_status_are_not_behind_the_toggle(self):
        self.assertEqual(
            self.page({"search": "one", "status": "draft"}).folded_count, 0
        )

    def test_a_stale_value_alone_does_not_count(self):
        self.assertEqual(self.page({"tags": "gone"}).folded_count, 0)

    def test_the_count_is_in_the_toggle_and_in_the_region(self):
        response = self.get({"review": "not_reviewed", "topics": "climate"})
        self.assertContains(response, 'data-folded="2"')
        self.assertContains(response, '<span id="tables-fold-count"> (2)</span>')

    def test_an_htmx_swap_tells_the_bar_the_new_count(self):
        response = self.get({"review": "reviewed"}, htmx=True)
        self.assertContains(response, 'data-folded="1"')
