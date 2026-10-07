"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The list mechanics (``login.listing``) on their own, against a model that is
not Table: Dataset, whose key is a uuid. The tables tab tests the same
mechanics through HTTP; these pin what a second tab relies on, so a change to
the mechanics fails here rather than only in one tab's columns.

Assertions are on rows, counts and addresses, never on markup.
"""  # noqa: 501

from unittest import mock

from django.db.models import DateTimeField, F, IntegerField, Q
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from django.http import QueryDict
from django.test import TestCase

from dataedit.models import Dataset
from login.listing import (
    NULLS_LAST,
    NULLS_LOWEST,
    Choice,
    ChoiceFilter,
    Filter,
    Listing,
    Option,
    RangeFilter,
    Segment,
    Sort,
    dates_within,
)

PATH = "/list"

# Dates and ranks kept in the metadata, so a test can leave them unknown.
PUBLISHED = Cast(KeyTextTransform("published", "metadata"), DateTimeField())
RANK = Cast(KeyTextTransform("rank", "metadata"), IntegerField())

KINDS = (
    Option("wind", "Wind"),
    Option("solar", "Solar"),
    Option("grid", "Grid", group="Networks"),
)


def _search(queryset, text):
    return queryset.filter(name__icontains=text)


def _kinds(queryset, values):
    return queryset.filter(metadata__kind__in=values)


def _region(queryset, value):
    return queryset.filter(metadata__region=value)


def listing(regions=("north", "south")):
    """A listing over Datasets with every kind of filter, a segment, sorts
    with each way of placing unknowns, and a page of three."""
    return Listing(
        singular="dataset",
        plural="datasets",
        filters=(
            Filter("search", lambda raw: raw.strip() or None, _search, label="Search"),
            ChoiceFilter("kind", "Kind", KINDS, _kinds, multiple=True),
            ChoiceFilter(
                "region",
                "Region",
                lambda: [Option(r, r.title()) for r in regions],
                _region,
            ),
            RangeFilter(
                "published",
                "Published",
                dates_within(PUBLISHED, "published_range"),
                more=True,
            ),
        ),
        segment=Segment(
            "state",
            "All",
            (
                Choice("open", "Open", Q(metadata__open=True)),
                Choice("closed", "Closed", Q(metadata__open=False)),
            ),
        ),
        sorts=(
            Sort("name", "Name", F("name"), "A to Z", "Z to A"),
            Sort("published", "Published", PUBLISHED, nulls=NULLS_LAST),
            Sort("rank", "Rank", RANK, nulls=NULLS_LOWEST),
        ),
        default_sort="name",
        tiebreak=("pk",),
        page_size=3,
    )


def query(text=""):
    return QueryDict(text)


class ListingTestCase(TestCase):
    def dataset(self, name, **metadata):
        return Dataset.objects.create(name=name, metadata=metadata)

    def page(self, text="", listing_=None):
        return (listing_ or listing()).page(Dataset.objects.all(), query(text), PATH)

    def names(self, text="", listing_=None):
        return [d.name for d in self.page(text, listing_).rows]


class FilterTests(ListingTestCase):
    def test_free_text_narrows_and_is_kept_in_the_url(self):
        self.dataset("wind_atlas")
        self.dataset("grid_map")
        page = self.page("search=atlas")
        self.assertEqual([d.name for d in page.rows], ["wind_atlas"])
        self.assertEqual(page.url, f"{PATH}?search=atlas")
        self.assertEqual([chip.text for chip in page.chips], ["Search: “atlas”"])

    def test_blank_text_is_not_filtering_and_is_not_written(self):
        self.dataset("wind_atlas")
        page = self.page("search=++")
        self.assertEqual(page.total, 1)
        self.assertEqual(page.url, PATH)
        self.assertFalse(page.state.filtered)


class ChoiceFilterTests(ListingTestCase):
    def setUp(self):
        self.dataset("a_wind", kind="wind", region="north")
        self.dataset("b_solar", kind="solar", region="south")
        self.dataset("c_grid", kind="grid", region="north")

    def test_several_values_are_comma_joined_or_repeated(self):
        self.assertEqual(self.names("kind=wind,grid"), ["a_wind", "c_grid"])
        self.assertEqual(self.names("kind=wind&kind=grid"), ["a_wind", "c_grid"])
        self.assertEqual(self.page("kind=wind&kind=grid").url, f"{PATH}?kind=wind,grid")

    def test_a_stale_value_narrows_nothing_and_stays_in_every_link(self):
        page = self.page("kind=wind,gone&sort=-name")
        self.assertEqual([d.name for d in page.rows], ["a_wind"])
        self.assertEqual(page.state.stale, [("kind", "gone")])
        links = (
            [page.url]
            + [link.url for link in page.sort_links.values()]
            + [link.url for link in page.segment_links]
        )
        for url in links:
            self.assertIn("kind=wind,gone", url)
        stale = [chip for chip in page.chips if chip.stale]
        self.assertEqual(len(stale), 1)
        self.assertIn("gone", stale[0].text)
        # removing the stale chip keeps the value that still applies
        self.assertEqual(stale[0].url, f"{PATH}?kind=wind&sort=-name")

    def test_only_stale_values_filter_nothing(self):
        page = self.page("region=east")
        self.assertEqual(page.total, 3)
        self.assertEqual(page.state.stale, [("region", "east")])
        self.assertIn("region=east", page.url)

    def test_a_single_valued_filter_takes_its_first_value(self):
        self.assertEqual(self.names("region=south"), ["b_solar"])

    def test_the_option_source_is_called_only_when_named_or_rendered(self):
        source = mock.Mock(return_value=[Option("north", "North")])
        lazy = Listing(
            singular="dataset",
            plural="datasets",
            filters=(ChoiceFilter("region", "Region", source, _region),),
            segment=Segment("state", "All", ()),
            sorts=(Sort("name", "Name", F("name")),),
            default_sort="name",
            tiebreak=("pk",),
        )
        page = self.page("", lazy)
        source.assert_not_called()
        page.controls
        self.assertTrue(source.called)
        source.reset_mock()
        self.assertEqual(self.names("region=north", lazy), ["a_wind", "c_grid"])
        self.assertTrue(source.called)


class RangeFilterTests(ListingTestCase):
    def setUp(self):
        self.dataset("a_jan", published="2026-01-10T12:00:00+00:00")
        self.dataset("b_mar", published="2026-03-10T12:00:00+00:00")
        self.dataset("c_unknown")

    def test_either_end_is_enough(self):
        self.assertEqual(self.names("published_from=2026-02-01"), ["b_mar"])
        self.assertEqual(self.names("published_to=2026-02-01"), ["a_jan"])
        self.assertEqual(
            self.names("published_from=2026-01-10&published_to=2026-03-10"),
            ["a_jan", "b_mar"],
        )

    def test_an_unknown_date_matches_no_range(self):
        self.assertNotIn("c_unknown", self.names("published_to=2099-01-01"))
        self.assertNotIn("c_unknown", self.names("published_from=1900-01-01"))

    def test_one_chip_removes_both_ends(self):
        page = self.page("published_from=2026-01-01&published_to=2026-12-31")
        (chip,) = page.chips
        self.assertEqual(chip.text, "Published: 1 Jan 2026 – 31 Dec 2026")
        self.assertEqual(chip.url, PATH)
        self.assertEqual(page.folded_count, 1)
        self.assertEqual(page.more_count, 1)

    def test_an_unreadable_date_is_dropped(self):
        page = self.page("published_from=yesterday")
        self.assertEqual(page.total, 3)
        self.assertEqual(page.url, PATH)

    def test_a_first_day_after_the_last_selects_nothing(self):
        page = self.page("published_from=2026-04-01&published_to=2026-01-01")
        self.assertEqual(page.total, 0)
        self.assertTrue(page.has_any)


class SegmentTests(ListingTestCase):
    def setUp(self):
        self.dataset("a_open_wind", open=True, kind="wind")
        self.dataset("b_open_solar", open=True, kind="solar")
        self.dataset("c_closed_wind", open=False, kind="wind")

    def counts(self, text):
        page = self.page(text)
        return {link.id: link.count for link in page.segment_links}

    def test_counts_are_faceted_over_every_filter_but_the_segment(self):
        expected = {"seg-all": 2, "seg-open": 1, "seg-closed": 1}
        self.assertEqual(self.counts("kind=wind"), expected)
        self.assertEqual(self.counts("kind=wind&state=open"), expected)

    def test_the_total_is_the_selected_buttons_count(self):
        page = self.page("state=open")
        self.assertEqual(page.total, 2)
        self.assertEqual([d.name for d in page.rows], ["a_open_wind", "b_open_solar"])

    def test_an_unknown_segment_value_is_the_all_button(self):
        page = self.page("state=archived")
        self.assertEqual(page.total, 3)
        self.assertEqual(page.url, PATH)

    def test_the_segment_is_not_a_filter(self):
        page = self.page("state=closed")
        self.assertFalse(page.state.filtered)
        self.assertEqual(page.filters_json, "{}")


class SortTests(ListingTestCase):
    def test_nulls_last_puts_unknowns_at_the_end_both_ways(self):
        self.dataset("a", published="2026-01-01T00:00:00+00:00")
        self.dataset("b")
        self.dataset("c", published="2026-02-01T00:00:00+00:00")
        self.assertEqual(self.names("sort=published"), ["a", "c", "b"])
        self.assertEqual(self.names("sort=-published"), ["c", "a", "b"])

    def test_nulls_lowest_counts_an_unknown_below_every_value(self):
        self.dataset("a", rank=2)
        self.dataset("b")
        self.dataset("c", rank=1)
        self.assertEqual(self.names("sort=rank"), ["b", "c", "a"])
        self.assertEqual(self.names("sort=-rank"), ["a", "c", "b"])

    def test_the_tiebreak_pages_deterministically_on_a_uuid_key(self):
        datasets = [self.dataset(f"d{n}", rank=1) for n in range(7)]
        pages = [self.page(f"sort=rank&page={n}").rows for n in (1, 2, 3)]
        seen = [d.pk for rows in pages for d in rows]
        self.assertEqual(seen, sorted(d.pk for d in datasets))

    def test_an_unknown_sort_is_the_default_and_is_not_written(self):
        self.dataset("b")
        self.dataset("a")
        page = self.page("sort=colour")
        self.assertEqual([d.name for d in page.rows], ["a", "b"])
        self.assertEqual(page.url, PATH)

    def test_the_sort_select_offers_both_directions(self):
        options = self.page("sort=-name").sort_options
        self.assertEqual(
            [(o.value, o.label, o.selected) for o in options[:2]],
            [("name", "Name: A to Z", False), ("-name", "Name: Z to A", True)],
        )

    def test_a_header_link_flips_the_direction_and_returns_to_page_one(self):
        for n in range(4):
            self.dataset(f"d{n}")
        page = self.page("page=2")
        self.assertEqual(page.sort_links["name"].url, f"{PATH}?sort=-name")
        self.assertEqual(page.sort_links["rank"].url, f"{PATH}?sort=rank")


class ListStateUrlTests(ListingTestCase):
    def state(self, text):
        return listing().state(query(text))

    def test_defaults_are_never_written(self):
        self.assertEqual(self.state("sort=name&page=1").url(PATH), PATH)

    def test_a_filter_change_returns_to_page_one(self):
        state = self.state("kind=wind&page=4&sort=-name")
        self.assertEqual(state.url(PATH, kind="solar"), f"{PATH}?kind=solar&sort=-name")

    def test_a_cleared_filter_is_left_out(self):
        state = self.state("kind=wind&search=x")
        self.assertEqual(state.url(PATH, kind=None), f"{PATH}?search=x")

    def test_parameters_follow_the_declaration_order(self):
        state = self.state("state=open&region=north&search=x")
        self.assertEqual(state.url(PATH), f"{PATH}?search=x&region=north&state=open")

    def test_paging_and_sorting_keep_the_filters(self):
        state = self.state("kind=wind,grid")
        self.assertEqual(
            state.url(PATH, page=3, sort="-rank"),
            f"{PATH}?kind=wind,grid&sort=-rank&page=3",
        )


class PagingTests(ListingTestCase):
    def setUp(self):
        for n in range(7):
            self.dataset(f"d{n}")

    def test_a_page_past_the_end_is_clamped(self):
        page = self.page("page=99")
        self.assertEqual((page.number, page.num_pages), (3, 3))
        self.assertEqual([d.name for d in page.rows], ["d6"])
        self.assertEqual(page.url, f"{PATH}?page=3")

    def test_an_unreadable_page_is_the_first(self):
        for text in ("page=abc", "page=0", "page=-2"):
            with self.subTest(text=text):
                self.assertEqual(self.page(text).number, 1)

    def test_the_summary_counts_the_page(self):
        page = self.page("page=2")
        self.assertEqual(page.summary, "4–6 of 7 datasets")
        self.assertEqual(page.scope, "")

    def test_an_empty_account_and_an_empty_match_differ(self):
        self.assertTrue(self.page("search=zzz").has_any)
        Dataset.objects.all().delete()
        self.assertFalse(self.page().has_any)


class MatchingTests(ListingTestCase):
    def test_matching_is_the_lists_selection_across_pages(self):
        for n in range(5):
            self.dataset(f"w{n}", kind="wind", open=n % 2 == 0)
        self.dataset("s", kind="solar", open=True)
        text = "kind=wind&state=open&sort=-name&page=2"
        matching = listing().matching(Dataset.objects.all(), query(text))
        self.assertEqual(
            sorted(matching.values_list("name", flat=True)), ["w0", "w2", "w4"]
        )
        self.assertEqual(self.page(text).total, 3)

    def test_a_stale_value_matches_as_it_lists(self):
        self.dataset("n", region="north")
        self.dataset("s", region="south")
        matching = listing().matching(Dataset.objects.all(), query("region=gone"))
        self.assertEqual(matching.count(), 2)

    def test_the_scope_is_the_filter_state_without_sort_and_page(self):
        self.dataset("a", kind="wind")
        page = self.page("kind=wind&state=open&sort=-name&page=2")
        self.assertEqual(page.scope, "?kind=wind&state=open")
