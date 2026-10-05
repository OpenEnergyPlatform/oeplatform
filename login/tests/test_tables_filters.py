"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The tables tab's filters (#2556, spec #2551): Review, Access, Dataset, Topic
and Tags, combined with AND, their options, their chips and Reset, and a
value from an old link that no longer applies, as seen through HTTP.

Assertions are on what the page says (rows, counts, chips, options, links,
headers), never on markup details or seconds.
"""  # noqa: 501

from unittest import mock

from django.db import connection
from django.db.models import Q
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from dataedit.models import Dataset, PeerReview, Table, Tag, Topic
from login.models import (
    ADMIN_PERM,
    DELETE_PERM,
    WRITE_PERM,
    GroupPermission,
    Membership,
    UserPermission,
)
from login.tables_tab import accessible_tables, tables_listing
from login.tests.test_tables_tab import TablesTabTestCase
from oeplatform.settings import PSEUDO_TOPIC_DRAFT


class FilterTestCase(TablesTabTestCase):
    def grant(self, organization, *tables, level=WRITE_PERM):
        for table in tables:
            GroupPermission.objects.create(
                holder=organization, table=table, level=level
            )

    def dataset(self, name, creator, *tables):
        dataset = Dataset.objects.create(name=name, creator=creator)
        dataset.tables.add(*tables)
        return dataset

    def topics(self, table, *names):
        table.topics.add(*[Topic.objects.get_or_create(name=n)[0] for n in names])

    def tag(self, table, *names):
        for name in names:
            tag = Tag.objects.filter(pk=Tag.get_name_normalized(name)).first()
            if tag is None:
                tag = Tag(name=name)
                tag.save()
            table.tags.add(tag)

    def review(self, table, finished):
        PeerReview.objects.create(
            table=table.name,
            contributor=self.user,
            reviewer=self.stranger,
            is_finished=finished,
            review={"badge": "Gold"},
        )

    def options(self, param, query=None):
        controls = {c.param: c for c in self.page(query).controls}
        return [(o.value, o.label) for o in controls[param].options]

    def chips(self, query):
        return [(chip.text, chip.stale) for chip in self.page(query).chips]


class ReviewFilterTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        self.table("t_none")
        self.review(self.table("t_open"), finished=False)
        self.review(self.table("t_done"), finished=True)
        later = self.table("t_done_then_open")
        self.review(later, finished=True)
        self.review(later, finished=False)

    def test_each_state_lists_the_rows_whose_pill_reads_it(self):
        for state, expected in (
            ("reviewed", ["t_done", "t_done_then_open"]),
            ("in_review", ["t_open"]),
            ("not_reviewed", ["t_none"]),
        ):
            with self.subTest(state=state):
                rows = self.page({"review": state}).rows
                self.assertEqual([r.table.name for r in rows], expected)
                self.assertEqual({r.review_state for r in rows}, {state})

    def test_the_options_are_the_three_states(self):
        self.assertEqual(
            self.options("review"),
            [
                ("reviewed", "Reviewed"),
                ("in_review", "In review"),
                ("not_reviewed", "Not reviewed"),
            ],
        )


class AccessFilterTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        self.wind = self.organization("Org Wind")
        self.solar = self.organization("Org Solar")
        self.mine = self.table("t_direct", level=WRITE_PERM)
        self.both = self.table("t_both", level=ADMIN_PERM)
        self.org_only = self.table("t_org_only", level=None)
        self.grant(self.wind, self.both, self.org_only)
        self.grant(self.solar, self.org_only, level=DELETE_PERM)

    def test_direct_lists_every_table_with_a_grant_of_the_users_own(self):
        self.assertEqual(self.names({"access": "direct"}), ["t_both", "t_direct"])

    def test_an_organization_lists_the_tables_it_reaches(self):
        self.assertEqual(
            self.names({"access": str(self.wind.pk)}), ["t_both", "t_org_only"]
        )
        self.assertEqual(self.names({"access": str(self.solar.pk)}), ["t_org_only"])

    def test_options_are_direct_then_each_organization_reaching_a_table(self):
        self.organization("Org Empty")
        sandbox = self.table("t_sandbox", level=None, is_sandbox=True)
        self.grant(self.organization("Org Sandbox"), sandbox)
        self.grant(self.organization("Org Not Mine", member=False), self.mine)
        self.assertEqual(
            self.options("access"),
            [
                ("direct", "Direct"),
                (str(self.solar.pk), "Org Solar"),
                (str(self.wind.pk), "Org Wind"),
            ],
        )

    def test_direct_is_not_offered_without_a_grant_of_the_users_own(self):
        UserPermission.objects.filter(holder=self.user).delete()
        self.assertEqual([v for v, _ in self.options("access")][0], str(self.solar.pk))
        page = self.page({"access": "direct"})
        self.assertEqual(len(page.rows), 2)
        self.assertEqual(self.chips({"access": "direct"})[0][1], True)

    def test_an_organization_the_user_left_is_a_stale_chip_not_an_empty_list(self):
        Membership.objects.filter(user=self.user, group=self.wind).delete()
        response = self.get({"access": str(self.wind.pk)})
        page = response.context["page"]
        self.assertEqual(len(page.rows), 3)
        self.assertEqual(
            self.chips({"access": str(self.wind.pk)}),
            [(f"Filter ‹Access: {self.wind.pk}› no longer applies", True)],
        )


class DatasetFilterTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        self.alone = self.table("t_alone", title="A")
        self.in_mine = self.table("t_in_mine", title="B")
        self.in_theirs = self.table("t_in_theirs", title="C")
        self.in_both = self.table("t_in_both", title="D")
        self.dataset("mine", self.user, self.in_mine, self.in_both)
        self.dataset("theirs", self.stranger, self.in_theirs, self.in_both)

    def test_in_any_in_none_and_one_dataset(self):
        self.assertEqual(
            self.names({"dataset": "any"}), ["t_in_mine", "t_in_theirs", "t_in_both"]
        )
        self.assertEqual(self.names({"dataset": "none"}), ["t_alone"])
        self.assertEqual(
            self.names({"dataset": "theirs"}), ["t_in_theirs", "t_in_both"]
        )

    def test_in_none_is_exactly_the_rows_whose_datasets_cell_reads_a_dash(self):
        """Proven also under the rule the Dataset lifecycle will bring, under
        which ``their_draft`` is a draft the Datasets cell never counts: a
        Table only in a stranger's draft reads "–" and so is in none."""
        only_in_draft = self.table("t_only_in_draft", title="E")
        self.dataset("their_draft", self.stranger, only_in_draft)
        for published in (Q(uuid__isnull=False), ~Q(name="their_draft")):
            with self.subTest(published=published), mock.patch(
                "login.tables_tab.PUBLISHED_DATASETS", published
            ):
                dashes = {
                    row.table.name for row in self.page().rows if not row.datasets
                }
                none = self.names({"dataset": "none"})
                any_ = self.names({"dataset": "any"})
            self.assertEqual(set(none), dashes)
            self.assertEqual(len(none) + len(any_), 5)
        self.assertEqual(dashes, {"t_alone", "t_only_in_draft"})

    def test_options_are_any_none_then_own_datasets_first(self):
        self.dataset("aaa_theirs", self.stranger, self.alone)
        self.dataset("zzz_mine", self.user, self.alone)
        self.dataset("unrelated", self.stranger, self.table("t_x", level=None))
        self.assertEqual(
            self.options("dataset"),
            [
                ("any", "In any dataset"),
                ("none", "In no dataset"),
                ("mine", "mine"),
                ("zzz_mine", "zzz_mine"),
                ("aaa_theirs", "aaa_theirs (TablesTabStranger)"),
                ("theirs", "theirs (TablesTabStranger)"),
            ],
        )

    def test_a_strangers_draft_dataset_is_never_offered(self):
        self.dataset("their_draft", self.stranger, self.alone)
        with mock.patch("login.tables_tab.PUBLISHED_DATASETS", ~Q(name="their_draft")):
            offered = [value for value, _ in self.options("dataset")]
            chips = self.chips({"dataset": "their_draft"})
            rows = self.names({"dataset": "their_draft"})
        self.assertNotIn("their_draft", offered)
        self.assertEqual(
            chips, [("Filter ‹Dataset: their_draft› no longer applies", True)]
        )
        self.assertEqual(len(rows), 4)

    def test_a_deleted_dataset_is_a_stale_chip(self):
        Dataset.objects.filter(name="theirs").delete()
        self.assertEqual(len(self.names({"dataset": "theirs"})), 4)
        self.assertTrue(self.chips({"dataset": "theirs"})[0][1])

    def test_a_dataset_named_like_a_keyword_is_not_offered_as_a_second_option(self):
        self.dataset("none", self.user, self.alone)
        values = [value for value, _ in self.options("dataset")]
        self.assertEqual(values.count("none"), 1)
        self.assertEqual(self.names({"dataset": "none"}), [])


class TopicFilterTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        self.topics(self.table("t_climate"), "climate")
        self.topics(self.table("t_grid"), "grid")
        self.topics(self.table("t_climate_grid"), "climate", "grid")
        self.topics(self.table("t_draft", level=ADMIN_PERM), PSEUDO_TOPIC_DRAFT)
        self.topics(self.table("t_foreign", level=None), "society")

    def test_any_of_the_chosen_topics(self):
        self.assertEqual(
            self.names({"topics": "climate"}), ["t_climate", "t_climate_grid"]
        )
        self.assertEqual(
            self.names({"topics": "climate,grid"}),
            ["t_climate", "t_climate_grid", "t_grid"],
        )

    def test_a_table_in_two_chosen_topics_is_one_row_and_counts_once(self):
        page = self.page({"topics": "climate,grid"})
        self.assertEqual(page.total, 3)
        self.assertEqual(page.counts["all"], 3)

    def test_options_are_the_topics_on_the_users_tables_never_draft(self):
        self.assertEqual(
            self.options("topics"), [("climate", "climate"), ("grid", "grid")]
        )

    def test_the_draft_pseudo_topic_is_a_stale_chip(self):
        self.assertEqual(len(self.names({"topics": PSEUDO_TOPIC_DRAFT})), 4)
        self.assertEqual(
            self.chips({"topics": f"grid,{PSEUDO_TOPIC_DRAFT}"}),
            [
                ("Topic: grid", False),
                ("Filter ‹Topic: draft› no longer applies", True),
            ],
        )
        self.assertEqual(
            self.names({"topics": f"grid,{PSEUDO_TOPIC_DRAFT}"}),
            ["t_climate_grid", "t_grid"],
        )


class TagFilterTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        self.tag(self.table("t_wind"), "Wind Onshore")
        self.tag(self.table("t_wind_grid"), "Wind Onshore", "Grid")
        self.tag(self.table("t_grid"), "Grid")
        self.tag(self.table("t_foreign", level=None), "Society")

    def test_all_of_the_chosen_tags_by_normalised_name(self):
        self.assertEqual(
            self.names({"tags": "wind_onshore"}), ["t_wind", "t_wind_grid"]
        )
        self.assertEqual(self.names({"tags": "wind_onshore,grid"}), ["t_wind_grid"])

    def test_the_repeated_form_is_read_too(self):
        response = self.client.get(f"{self.path}?tags=wind_onshore&tags=grid")
        page = response.context["page"]
        self.assertEqual([row.table.name for row in page.rows], ["t_wind_grid"])
        self.assertEqual(page.url, f"{self.path}?tags=wind_onshore,grid")

    def test_options_are_the_tags_on_the_users_tables_by_name(self):
        self.assertEqual(
            self.options("tags"), [("grid", "Grid"), ("wind_onshore", "Wind Onshore")]
        )

    def test_a_label_is_not_a_key(self):
        """The URL carries the normalised name, as ``dataedit``'s table list
        does; a display name is an unknown value, not a second spelling."""
        self.assertTrue(self.chips({"tags": "Wind Onshore"})[0][1])
        self.assertEqual(len(self.names({"tags": "Wind Onshore"})), 3)

    def test_an_unknown_tag_is_stale_and_the_known_ones_still_apply(self):
        self.assertEqual(
            self.chips({"tags": "grid,gone"}),
            [
                ("Tag: Grid", False),
                ("Filter ‹Tag: gone› no longer applies", True),
            ],
        )
        self.assertEqual(self.names({"tags": "grid,gone"}), ["t_grid", "t_wind_grid"])


class CombinedFilterTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        self.wind = self.organization("Org Wind")
        a = self.table("t_a", published=True)
        b = self.table("t_b")
        c = self.table("t_c", level=None)
        self.grant(self.wind, a, b, c)
        self.topics(a, "climate", "grid")
        self.topics(b, "climate", "grid")
        self.tag(a, "Wind", "Grid")
        self.tag(b, "Wind", "Grid")
        self.dataset("one", self.user, a, b)
        self.dataset("two", self.stranger, a, b, c)

    def test_filters_combine_with_and(self):
        query = {"access": "direct", "topics": "climate", "dataset": "any"}
        self.assertEqual(self.names(query), ["t_a", "t_b"])
        self.assertEqual(self.names({**query, "review": "reviewed"}), [])

    def test_joins_never_multiply_rows_or_facet_counts(self):
        """Two topics, two tags, two Datasets, two grants each: every clause
        is a primary-key subquery, so each Table is one row and one count."""
        query = {
            "topics": "climate,grid",
            "tags": "wind,grid",
            "dataset": "any",
            "access": str(self.wind.pk),
        }
        page = self.page(query)
        self.assertEqual([row.table.name for row in page.rows], ["t_a", "t_b"])
        self.assertEqual(
            {link.id: link.count for link in page.segment_links},
            {"seg-all": 2, "seg-draft": 1, "seg-published": 1},
        )

    def test_counts_follow_every_filter_but_status(self):
        expected = {"seg-all": 2, "seg-draft": 1, "seg-published": 1}
        self.assertEqual(self.counts({"tags": "wind"}), expected)
        self.assertEqual(self.counts({"tags": "wind", "status": "draft"}), expected)

    def test_options_do_not_narrow_as_other_filters_change(self):
        for param in ("access", "dataset", "topics", "tags"):
            with self.subTest(param=param):
                self.assertEqual(
                    self.options(param, {"dataset": "none", "review": "reviewed"}),
                    self.options(param),
                )

    def test_the_list_and_its_matching_set_share_one_parsing(self):
        """``Listing.matching`` is what "select all matching" will read: the
        same declarations, parsed the same way, as the rows shown."""
        query = {"tags": "wind", "status": "draft", "topics": "climate,gone"}
        listing = tables_listing(self.user)
        matching = listing.matching(accessible_tables(self.user), query)
        self.assertEqual(
            sorted(matching.values_list("name", flat=True)), self.names(query)
        )


class ChipTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        self.wind = self.organization("Org Wind")
        table = self.table("t_one", title="One")
        self.grant(self.wind, table)
        self.topics(table, "climate", "grid")
        self.tag(table, "Wind")
        self.dataset("mine", self.user, table)
        self.table("t_two")

    def test_every_active_filter_is_a_chip(self):
        query = {
            "search": "one",
            "review": "not_reviewed",
            "access": str(self.wind.pk),
            "dataset": "mine",
            "topics": "climate,grid",
            "tags": "wind",
        }
        self.assertEqual(
            self.chips(query),
            [
                ("Search: “one”", False),
                ("Review: Not reviewed", False),
                ("Access: Org Wind", False),
                ("Dataset: mine", False),
                ("Topic: climate", False),
                ("Topic: grid", False),
                ("Tag: Wind", False),
            ],
        )

    def test_the_dataset_keywords_read_as_sentences(self):
        self.assertEqual(self.chips({"dataset": "none"}), [("In no dataset", False)])
        self.assertEqual(self.chips({"access": "direct"}), [("Access: direct", False)])

    def test_a_chip_removes_its_value_only_and_returns_to_page_one(self):
        page = self.page({"topics": "climate,grid", "sort": "-table", "page": "2"})
        climate, grid = page.chips
        self.assertEqual(climate.url, f"{self.path}?topics=grid&sort=-table")
        self.assertEqual(grid.url, f"{self.path}?topics=climate&sort=-table")

    def test_reset_all_clears_filters_search_status_and_stale_values_keeps_sort(self):
        page = self.page(
            {
                "search": "one",
                "review": "reviewed",
                "tags": "gone",
                "status": "draft",
                "sort": "-status",
                "page": "2",
            }
        )
        self.assertEqual(page.reset_url, f"{self.path}?sort=-status")
        response = self.get({"review": "reviewed"})
        self.assertContains(response, 'id="chips-reset"')

    def test_no_filter_no_chips_and_no_reset(self):
        response = self.get({"status": "draft"})
        self.assertEqual(response.context["page"].chips, [])
        self.assertNotContains(response, 'id="chips-reset"')

    def test_a_stale_value_stays_in_every_link_until_dismissed(self):
        page = self.page({"tags": "gone", "review": "reviewed"})
        stale = page.chips[-1]
        self.assertTrue(stale.stale)
        self.assertEqual(stale.url, f"{self.path}?review=reviewed")
        draft = next(link for link in page.segment_links if link.id == "seg-draft")
        self.assertEqual(
            draft.url, f"{self.path}?review=reviewed&tags=gone&status=draft"
        )
        response = self.get({"tags": "gone"}, htmx=True)
        self.assertEqual(response["HX-Push-Url"], f"{self.path}?tags=gone")

    def test_a_stale_value_is_never_a_400_nor_an_empty_list(self):
        for query in (
            {"access": "999999"},
            {"access": "not-a-number"},
            {"dataset": "gone"},
            {"review": "excellent"},
            {"topics": "gone"},
            {"tags": ",,,"},
        ):
            with self.subTest(query=query):
                page = self.page(query)
                self.assertEqual(len(page.rows), 2)
        self.assertEqual(self.chips({"tags": ",,,"}), [])

    def test_the_announcement_says_match_only_when_a_filter_applies(self):
        self.assertEqual(
            self.page({"tags": "gone"}).announcement, "2 tables, showing 1 to 2"
        )
        self.assertEqual(
            self.page({"tags": "wind"}).announcement, "1 table matches, showing 1 to 1"
        )


class FilterBarTests(FilterTestCase):
    def setUp(self):
        super().setUp()
        table = self.table("t_one")
        self.topics(table, "climate")
        self.tag(table, "Wind")

    def test_the_primary_row_then_more_filters(self):
        body = self.get().content.decode()
        order = [
            'id="tables-search"',
            'id="f-publishable"',
            'id="f-review"',
            'id="f-access"',
            'id="f-dataset"',
            'id="tables-more"',
            'id="f-topics"',
            'id="f-tags"',
            'id="tables-results"',
        ]
        positions = [body.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))

    def test_more_filters_counts_the_ones_behind_it(self):
        self.assertEqual(self.page().more_count, 0)
        self.assertEqual(
            self.page({"topics": "climate", "tags": "wind,gone"}).more_count, 2
        )
        self.assertEqual(
            self.page({"tags": "gone", "review": "reviewed"}).more_count, 0
        )

    def test_the_region_tells_the_bar_what_the_url_holds(self):
        response = self.get({"review": "reviewed", "tags": "gone", "status": "draft"})
        page = response.context["page"]
        self.assertEqual(page.filters_json, '{"review": "reviewed", "tags": "gone"}')
        self.assertContains(response, 'data-more="0"')

    def test_the_chosen_values_are_selected_in_the_bar(self):
        page = self.page({"topics": "climate", "review": "in_review"})
        selected = {
            c.param: [o.value for o in c.options if o.selected]
            for c in page.controls
            if c.kind == "choice"
        }
        self.assertEqual(selected["topics"], ["climate"])
        self.assertEqual(selected["review"], ["in_review"])
        self.assertEqual(selected["tags"], [])


class FilterQueryCountTests(FilterTestCase):
    """Filters keep a page's cost independent of the account size. A filter
    the request names costs the one query that tells its known values from
    stale ones and labels its chips (Access two: whether a direct grant
    exists, and the Organizations); Publishable's and Review's options are
    fixed and cost none."""

    ALL_FILTERS = {
        "publishable": "no",
        "review": "not_reviewed",
        "topics": "a",
        "tags": "t1",
        "dataset": "any",
        "modified_from": "2000-01-01",
        # created on insert, so the range leaves rows
        "created_to": "2999-12-31",
    }

    def fill(self, count, organization):
        tables = Table.objects.bulk_create(
            # without metadata none passes the gate, and storing that lets
            # the Publishable filter in ALL_FILTERS leave rows on the page
            Table(
                name=f"q_{index:04d}",
                is_publish=index % 3 == 0,
                publishable=False,
                # stamped, so the Modified range in ALL_FILTERS leaves rows
                data_modified=timezone.now(),
            )
            for index in range(count)
        )
        UserPermission.objects.bulk_create(
            UserPermission(holder=self.user, table=table, level=WRITE_PERM)
            for table in tables[::2]
        )
        GroupPermission.objects.bulk_create(
            GroupPermission(holder=organization, table=table, level=DELETE_PERM)
            for table in tables[1::2]
        )
        topic = Topic.objects.get_or_create(name="a")[0]
        tag = Tag.objects.filter(pk="t1").first() or Tag(name="t1")
        tag.save()
        own = Dataset.objects.create(name=f"own_{count}", creator=self.user)
        for index, table in enumerate(tables):
            table.topics.add(topic)
            table.tags.add(tag)
            if index % 2:
                own.tables.add(table)

    def empty(self):
        Table.objects.filter(name__startswith="q_").delete()
        Dataset.objects.all().delete()

    def queries(self, query, htmx=True):
        with CaptureQueriesContext(connection) as captured:
            self.get(query, htmx=htmx)
        return len(captured)

    def test_filtered_requests_cost_the_same_at_every_account_size(self):
        organization = self.organization("Org Count")
        self.get(htmx=True)
        everything = {**self.ALL_FILTERS, "access": str(organization.pk)}
        counts = {}
        for size in (4, 130, 300):
            self.empty()
            self.fill(size, organization)
            counts[size] = [
                self.queries({}),
                self.queries(
                    {"publishable": "no", "review": "not_reviewed", "search": "q_"}
                ),
                self.queries(everything),
                self.queries({}, htmx=False),
            ]
        sizes = list(counts)
        # 7 unfiltered (pinned in QueryCountTests); 7 with Publishable and
        # Review; 7 + 2 (Access) + 1 (Topics) + 1 (Tags) + 1 (Dataset) with
        # all of them. The Modified range has no options and costs none.
        self.assertEqual(counts[sizes[0]][:3], [7, 7, 12])
        for size in sizes[1:]:
            self.assertEqual(counts[size], counts[sizes[0]], size)
