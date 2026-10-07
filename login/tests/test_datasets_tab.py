"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The datasets tab of the profile dashboard (#2622, spec #2613): one list of the
user's own Datasets, with a status segment, search, Topic, Tag and date
filters, sorting, paging and the URL state, as seen through HTTP.

Assertions are on what the page says (rows, counts, links, chips, headers,
the templates that rendered), never on markup details or seconds.
"""  # noqa: 501

from datetime import datetime, timedelta

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from dataedit.models import Dataset, Embargo, Table, Tag, Topic
from login.datasets_tab import MEMBERS_SHOWN
from login.listing import PAGE_SIZE
from login.tests.helpers import HTMX, make_user
from modelview.tests.html import element_markup, text
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

REGION = "login/partials/datasets_region.html"
PAGE = "login/user_datasets.html"


def moment(day, hour=12):
    """Noon on ``day`` (an ISO date) in the current time zone."""
    return timezone.make_aware(
        datetime.combine(datetime.fromisoformat(day).date(), datetime.min.time())
    ) + timedelta(hours=hour)


class DatasetsTabTestCase(TestCase):
    """A logged-in owner and helpers to give them Datasets."""

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("DatasetsTabOwner")
        cls.stranger = make_user("DatasetsTabStranger")

    def setUp(self):
        self.client.force_login(self.user)

    @property
    def path(self):
        return reverse("login:datasets", kwargs={"user_id": self.user.pk})

    def dataset(
        self,
        name,
        title=None,
        creator=None,
        published=None,
        modified=None,
        created=None,
        description="",
        tables=(),
        topics=(),
    ):
        """A Dataset of ``creator`` (the owner by default), a draft unless
        ``published`` gives its publication moment."""
        dataset = Dataset.objects.create(
            name=name,
            metadata={
                "name": name,
                "title": name if title is None else title,
                "description": description,
            },
            creator=creator or self.user,
            published_at=published,
            modified_at=modified,
        )
        if created is not None:
            # auto_now_add overrides a value given at creation
            Dataset.objects.filter(pk=dataset.pk).update(created_at=created)
            dataset.refresh_from_db()
        dataset.tables.add(*tables)
        for topic in topics:
            dataset.topics.add(Topic.objects.get_or_create(name=topic)[0])
        return dataset

    def table(self, name, title=None, published=True, embargoed=False, tags=()):
        table = Table.objects.create(
            name=name, human_readable_name=title, is_publish=published
        )
        if embargoed:
            Embargo.objects.create(table=table, duration="1_year")
        for tag in tags:
            table.tags.add(Tag.objects.get_or_create(name_normalized=tag, name=tag)[0])
        return table

    def get(self, query=None, htmx=False, **headers):
        if htmx:
            headers.update(HTMX)
        response = self.client.get(self.path, query or {}, **headers)
        self.assertEqual(response.status_code, 200)
        return response

    def page(self, query=None, **kwargs):
        return self.get(query, **kwargs).context["page"]

    def names(self, query=None, **kwargs):
        return [row.name for row in self.page(query, **kwargs).rows]

    def counts(self, query=None):
        return {link.id: link.count for link in self.page(query).segment_links}

    def cell(self, response, element_id):
        return text(element_markup(response.content.decode(), element_id))


class WhichDatasetsAreListedTests(DatasetsTabTestCase):
    def test_drafts_and_published_of_the_user_are_listed(self):
        self.dataset("ds_draft")
        self.dataset("ds_published", published=timezone.now())
        self.assertEqual(sorted(self.names()), ["ds_draft", "ds_published"])

    def test_a_strangers_dataset_is_never_listed_even_published(self):
        self.dataset("ds_theirs", creator=self.stranger, published=timezone.now())
        self.dataset("ds_their_draft", creator=self.stranger)
        self.assertEqual(self.names(), [])

    def test_an_ownerless_dataset_is_nobodys(self):
        Dataset.objects.create(name="ds_orphan", metadata={"title": "x"})
        self.assertEqual(self.names(), [])

    def test_a_dataset_with_many_members_is_one_row_and_counts_once(self):
        tables = [self.table(f"t_many_{n}") for n in range(3)]
        self.dataset("ds_many", tables=tables, topics=("a", "b"))
        page = self.page({"sort": "tables"})
        self.assertEqual([row.name for row in page.rows], ["ds_many"])
        self.assertEqual(page.total, 1)

    def test_the_profile_opens_on_this_tab(self):
        self.dataset("ds_landing")
        response = self.client.get(reverse("login:profile", args=[self.user.pk]))
        self.assertTemplateUsed(response, PAGE)
        self.assertEqual(
            [row.name for row in response.context["page"].rows], ["ds_landing"]
        )

    def test_the_tabs_run_datasets_then_tables(self):
        body = self.get().content.decode()
        self.assertLess(
            body.index(self.path),
            body.index(reverse("login:tables", args=[self.user.pk])),
        )


class ColumnTests(DatasetsTabTestCase):
    def test_the_title_links_to_the_detail_page_in_the_same_tab(self):
        dataset = self.dataset("ds_link", title="Wind atlas")
        response = self.get()
        title = element_markup(response.content.decode(), f"title-{dataset.pk}")
        self.assertIn(
            reverse("dataedit:dataset-detail", kwargs={"dataset_name": "ds_link"}),
            title,
        )
        self.assertNotIn("_blank", title)
        self.assertEqual(text(title), "Wind atlas")
        self.assertIn(
            '<div class="dash-tname">ds_link</div>', response.content.decode()
        )

    def test_a_dataset_without_a_title_shows_its_name_once(self):
        self.dataset("ds_untitled", title="")
        body = self.get().content.decode()
        self.assertEqual(body.count("ds_untitled</a>"), 1)
        self.assertNotIn('<div class="dash-tname">ds_untitled</div>', body)

    def test_status_reads_draft_or_published_since(self):
        self.dataset("ds_d")
        self.dataset("ds_p", published=moment("2026-03-04"))
        rows = {row.name: row for row in self.page().rows}
        self.assertEqual(rows["ds_d"].status, "draft")
        self.assertEqual(rows["ds_p"].status, "published")
        body = self.get().content.decode()
        self.assertIn("since 4 Mar 2026", text(body))

    def test_the_tables_count_opens_the_mix_and_the_members(self):
        dataset = self.dataset(
            "ds_mix",
            published=timezone.now(),
            tables=(
                self.table("t_b_draft", "B draft", published=False),
                self.table("t_a_pub", "A published"),
                self.table("t_c_emb", "C embargoed", embargoed=True),
                self.table("t_d_draft", "D draft", published=False),
            ),
        )
        response = self.get()
        button = self.cell(response, f"mb-{dataset.pk}")
        self.assertEqual(button, "4 tables")
        popover = element_markup(response.content.decode(), f"mb-{dataset.pk}-pop")
        self.assertIn("2 drafts · 1 embargoed", text(popover))
        self.assertLess(text(popover).index("A published"), text(popover).index("B"))
        self.assertIn(reverse("dataedit:view", kwargs={"table": "t_a_pub"}), popover)
        self.assertEqual(popover.count("dash-badge--draft"), 2)
        self.assertEqual(popover.count("dash-badge--embargoed"), 1)
        self.assertNotIn("more", text(popover))

    def test_the_mix_names_only_the_parts_there_are(self):
        dataset = self.dataset(
            "ds_one_draft",
            tables=(self.table("t_x", published=False), self.table("t_y")),
        )
        popover = self.cell(self.get(), f"mb-{dataset.pk}-pop")
        self.assertIn("1 draft", popover)
        self.assertNotIn("drafts", popover)
        self.assertNotIn("embargoed", popover)

    def test_a_draft_with_an_embargo_counts_as_a_draft(self):
        dataset = self.dataset(
            "ds_draft_emb",
            tables=(self.table("t_de", published=False, embargoed=True),),
        )
        row = next(r for r in self.page().rows if r.dataset == dataset)
        self.assertEqual(row.mix, "1 draft")
        self.assertEqual(row.members[0].status, "draft")

    def test_the_popover_names_ten_members_then_how_many_more(self):
        tables = [self.table(f"t_m_{n:02d}", f"Member {n:02d}") for n in range(13)]
        dataset = self.dataset("ds_thirteen", tables=tables)
        popover = self.cell(self.get(), f"mb-{dataset.pk}-pop")
        self.assertIn("Member 09", popover)
        self.assertNotIn("Member 10", popover)
        self.assertIn("and 3 more", popover)

    def test_a_strangers_draft_member_is_named_too(self):
        dataset = self.dataset(
            "ds_foreign_member",
            tables=(self.table("t_their_draft", "Their draft", published=False),),
        )
        self.assertIn("Their draft", self.cell(self.get(), f"mb-{dataset.pk}-pop"))

    def test_the_gate_hint_shows_on_an_empty_draft_only(self):
        draft = self.dataset("ds_empty_draft")
        published = self.dataset("ds_empty_published", published=timezone.now())
        body = self.get().content.decode()
        rows = {
            name: text(element_markup(body, f"row-{dataset.pk}"))
            for name, dataset in (("draft", draft), ("published", published))
        }
        # Tables and Topics both
        self.assertEqual(rows["draft"].count("– needed to publish"), 2)
        self.assertIn("No tables. At least one is needed to publish.", rows["draft"])
        self.assertIn("No topics. At least one is needed to publish.", rows["draft"])
        self.assertNotIn("needed to publish", rows["published"])
        self.assertIn("No tables", rows["published"])

    def test_topics_show_two_chips_then_the_rest_behind_plus_n(self):
        dataset = self.dataset("ds_topics", topics=("c_topic", "a_topic", "b_topic"))
        response = self.get()
        row = self.page().rows[0]
        self.assertEqual(row.topics, ["a_topic", "b_topic", "c_topic"])
        self.assertEqual(self.cell(response, f"tp-{dataset.pk}"), "+1")
        self.assertIn("c_topic", self.cell(response, f"tp-{dataset.pk}-pop"))

    def test_modified_reads_a_dash_with_a_reason_when_unknown(self):
        known = self.dataset("ds_known", modified=moment("2026-05-06"))
        unknown = self.dataset("ds_unknown")
        body = self.get().content.decode()
        self.assertIn("6 May 2026", text(element_markup(body, f"row-{known.pk}")))
        self.assertIn(
            "Not changed since the platform began recording",
            text(element_markup(body, f"row-{unknown.pk}")),
        )

    def test_created_reads_the_creation_date(self):
        dataset = self.dataset("ds_created", created=moment("2026-01-02"))
        body = self.get().content.decode()
        self.assertIn("2 Jan 2026", text(element_markup(body, f"row-{dataset.pk}")))

    def test_no_selection_and_no_menu_until_the_tab_offers_actions(self):
        self.dataset("ds_slots")
        body = self.get().content.decode()
        self.assertNotIn("data-select-row", body)
        self.assertNotIn("data-select-page", body)
        self.assertNotIn('id="datasets-bulk"', body)
        self.assertNotIn("datasets-select-all", body)
        # the slots are there, so the columns keep their measured widths
        self.assertIn('<td class="c-select">', body)
        self.assertIn('<td class="c-menu"></td>', body)


class SegmentAndSearchTests(DatasetsTabTestCase):
    def setUp(self):
        super().setUp()
        self.dataset("ds_wind", title="Wind farms", description="onshore")
        self.dataset("ds_solar", title="Solar parks", published=timezone.now())
        self.dataset("ds_grid", title="Grid", description="Wind and transmission")

    def test_the_segment_counts_are_faceted(self):
        self.assertEqual(
            self.counts({"search": "wind"}),
            {"seg-all": 2, "seg-draft": 2, "seg-published": 0},
        )

    def test_each_segment_lists_its_state(self):
        self.assertEqual(self.names({"status": "published"}), ["ds_solar"])
        self.assertEqual(
            sorted(self.names({"status": "draft"})), ["ds_grid", "ds_wind"]
        )

    def test_an_empty_segment_is_greyed_but_still_a_link(self):
        body = self.get({"search": "wind"}).content.decode()
        segment = element_markup(body, "seg-published")
        self.assertIn("dash-seg--zero", segment)
        self.assertIn("href=", segment)

    def test_search_reads_name_title_and_description(self):
        for query, expected in (
            ("ds_sol", ["ds_solar"]),
            ("PARKS", ["ds_solar"]),
            ("transmission", ["ds_grid"]),
        ):
            with self.subTest(query=query):
                self.assertEqual(self.names({"search": query}), expected)


class FilterTestCase(DatasetsTabTestCase):
    def setUp(self):
        super().setUp()
        wind = self.table("t_wind", tags=("wind",))
        solar = self.table("t_solar", tags=("solar",))
        both = self.table("t_both", tags=("wind", "solar"))
        theirs = self.table("t_theirs_draft", published=False, tags=("hidden",))
        self.wind = self.dataset("ds_wind", tables=(wind,), topics=("energy",))
        self.split = self.dataset(
            "ds_split", tables=(wind, solar), topics=("energy", "climate")
        )
        self.both = self.dataset("ds_both", tables=(both,), topics=("climate",))
        self.theirs = self.dataset("ds_strangers_member", tables=(theirs,))
        self.dataset("ds_none")
        # a stranger's Dataset's Topics and tags are never offered
        self.dataset(
            "ds_stranger",
            creator=self.stranger,
            tables=(self.table("t_elsewhere", tags=("elsewhere",)),),
            topics=("elsewhere",),
            published=timezone.now(),
        )


class TopicFilterTests(FilterTestCase):
    def test_any_of_the_chosen_topics(self):
        self.assertEqual(
            sorted(self.names({"topics": "energy"})), ["ds_split", "ds_wind"]
        )
        self.assertEqual(
            sorted(self.names({"topics": "energy,climate"})),
            ["ds_both", "ds_split", "ds_wind"],
        )

    def test_options_are_the_topics_on_the_users_datasets(self):
        page = self.page()
        options = {
            c.param: [o.value for o in c.options]
            for c in page.controls
            if c.kind == "choice"
        }
        self.assertEqual(options["topics"], ["climate", "energy"])

    def test_the_draft_pseudo_topic_is_never_offered_and_is_a_stale_chip(self):
        Topic.objects.get_or_create(name=PSEUDO_TOPIC_DRAFT)
        self.wind.topics.add(PSEUDO_TOPIC_DRAFT)
        page = self.page({"topics": PSEUDO_TOPIC_DRAFT})
        topic_control = next(c for c in page.controls if c.param == "topics")
        self.assertNotIn(PSEUDO_TOPIC_DRAFT, [o.value for o in topic_control.options])
        self.assertEqual(page.total, 5)
        self.assertEqual([chip.stale for chip in page.chips], [True])


class TagFilterTests(FilterTestCase):
    def test_a_dataset_matches_a_tag_when_some_member_carries_it(self):
        self.assertEqual(
            sorted(self.names({"tags": "wind"})), ["ds_both", "ds_split", "ds_wind"]
        )

    def test_several_tags_and_even_on_different_members(self):
        self.assertEqual(
            sorted(self.names({"tags": "wind,solar"})), ["ds_both", "ds_split"]
        )

    def test_a_strangers_draft_member_contributes(self):
        self.assertEqual(self.names({"tags": "hidden"}), ["ds_strangers_member"])

    def test_options_are_the_tags_on_members_of_the_users_datasets(self):
        page = self.page()
        options = {
            c.param: [o.value for o in c.options]
            for c in page.controls
            if c.kind == "choice"
        }
        self.assertEqual(options["tags"], ["hidden", "solar", "wind"])

    def test_no_dataset_gains_a_tag(self):
        before = {
            name: sorted(Table.objects.get(name=name).tags.values_list("pk", flat=True))
            for name in ("t_wind", "t_solar", "t_both")
        }
        self.get({"tags": "wind,solar"})
        after = {
            name: sorted(Table.objects.get(name=name).tags.values_list("pk", flat=True))
            for name in before
        }
        self.assertEqual(before, after)
        self.assertFalse(hasattr(Dataset, "tags"))

    def test_counts_are_not_multiplied_by_members(self):
        page = self.page({"tags": "wind", "sort": "tables"})
        self.assertEqual(page.total, 3)
        self.assertEqual(len(page.rows), 3)
        self.assertEqual(
            {link.id: link.count for link in page.segment_links}["seg-all"], 3
        )

    def test_an_unknown_tag_is_a_stale_chip_and_narrows_nothing(self):
        page = self.page({"tags": "wind,gone"})
        self.assertEqual(page.total, 3)
        self.assertEqual([chip.stale for chip in page.chips], [False, True])
        self.assertIn("no longer applies", page.chips[1].text)


class FilterBarTests(FilterTestCase):
    def test_search_topic_and_tag_then_more_filters(self):
        body = self.get().content.decode()
        bar = element_markup(body, "datasets-filters")
        more = element_markup(body, "datasets-more-panel")
        for control in ("datasets-search", "f-topics-button", "f-tags-button"):
            with self.subTest(control=control):
                self.assertIn(f'id="{control}"', bar)
                self.assertNotIn(f'id="{control}"', more)
        for control in ("f-created_from", "f-modified_to"):
            with self.subTest(control=control):
                self.assertIn(f'id="{control}"', more)
        self.assertLess(bar.index("f-topics-button"), bar.index("f-tags-button"))

    def test_a_dropdown_counts_what_is_ticked(self):
        page = self.page({"topics": "energy", "tags": "hidden,solar,wind"})
        summaries = {c.param: c.summary for c in page.controls if c.kind == "choice"}
        self.assertEqual(summaries, {"topics": "Topic (1)", "tags": "Tag (3)"})
        body = self.get().content.decode()
        self.assertEqual(text(element_markup(body, "f-topics-button")), "Topic: any")


class DateFilterTests(DatasetsTabTestCase):
    def setUp(self):
        super().setUp()
        self.dataset(
            "ds_old", created=moment("2026-01-10"), modified=moment("2026-02-01")
        )
        self.dataset(
            "ds_new", created=moment("2026-06-10"), modified=moment("2026-07-01")
        )
        self.dataset("ds_unknown", created=moment("2026-06-11"))

    def test_created_range_either_end_optional(self):
        self.assertEqual(
            sorted(self.names({"created_from": "2026-06-01"})),
            ["ds_new", "ds_unknown"],
        )
        self.assertEqual(self.names({"created_to": "2026-01-31"}), ["ds_old"])

    def test_an_unknown_modified_matches_no_range(self):
        self.assertEqual(
            self.names({"modified_from": "2026-01-01"}),
            [
                "ds_new",
                "ds_old",
            ],
        )
        self.assertEqual(
            self.names({"modified_to": "2030-01-01"}),
            [
                "ds_new",
                "ds_old",
            ],
        )

    def test_the_ranges_sit_behind_more_filters(self):
        page = self.page({"created_from": "2026-06-01"})
        more = {c.param for c in page.controls if c.more}
        self.assertEqual(more, {"created", "modified"})
        self.assertEqual(page.more_count, 1)


class ChipAndResetTests(DatasetsTabTestCase):
    def test_reset_clears_filters_and_status_and_keeps_the_sort(self):
        self.dataset("ds_x", topics=("energy",))
        page = self.page(
            {
                "search": "x",
                "topics": "energy,gone",
                "status": "draft",
                "sort": "created",
            }
        )
        self.assertEqual(page.reset_url, f"{self.path}?sort=created")
        self.assertEqual(len(page.chips), 3)

    def test_no_match_keeps_the_header_and_offers_reset(self):
        self.dataset("ds_x")
        response = self.get({"search": "nothing"})
        body = text(response.content.decode())
        self.assertIn("No datasets match these filters", body)
        self.assertIn('id="nomatch-reset"', response.content.decode())
        self.assertIn('id="datasets-filters"', response.content.decode())


class EmptyAccountTests(DatasetsTabTestCase):
    def test_no_datasets_explains_with_no_bar_segment_or_header(self):
        body = self.get().content.decode()
        self.assertIn("You have no datasets yet", body)
        self.assertIn("private draft until you publish it", text(body))
        self.assertNotIn('id="datasets-filters"', body)
        self.assertNotIn("dash-seg", body)
        self.assertNotIn("<thead>", body)


class SortTests(DatasetsTabTestCase):
    def setUp(self):
        super().setUp()
        tables = [self.table(f"t_{n}") for n in range(3)]
        self.dataset(
            "ds_a",
            title="alpha",
            published=moment("2026-03-01"),
            modified=moment("2026-04-01"),
            created=moment("2026-01-01"),
            tables=tables[:1],
        )
        self.dataset(
            "ds_b",
            title="Bravo",
            modified=moment("2026-05-01"),
            created=moment("2026-02-01"),
            tables=tables,
        )
        self.dataset(
            "ds_c",
            title="",  # sorts by its name, "ds_c"
            published=moment("2026-06-01"),
            created=moment("2026-03-01"),
            tables=tables[:2],
        )
        self.dataset("ds_d", title="charlie", created=moment("2026-04-01"))

    def test_the_default_is_modified_newest_first_unknown_last(self):
        self.assertEqual(self.names(), ["ds_b", "ds_a", "ds_d", "ds_c"])

    def test_modified_puts_unknown_last_both_ways_title_then_breaking_ties(self):
        self.assertEqual(
            self.names({"sort": "modified"}), ["ds_a", "ds_b", "ds_d", "ds_c"]
        )

    def test_dataset_sorts_by_title_case_blind_falling_back_to_the_name(self):
        self.assertEqual(
            self.names({"sort": "dataset"}), ["ds_a", "ds_b", "ds_d", "ds_c"]
        )
        self.assertEqual(
            self.names({"sort": "-dataset"}), ["ds_c", "ds_d", "ds_b", "ds_a"]
        )

    def test_status_puts_drafts_lowest(self):
        # ascending: drafts first (by title), then the longest published
        self.assertEqual(
            self.names({"sort": "status"}), ["ds_b", "ds_d", "ds_a", "ds_c"]
        )
        # descending: the most recently published first, drafts last
        self.assertEqual(
            self.names({"sort": "-status"}), ["ds_c", "ds_a", "ds_b", "ds_d"]
        )

    def test_tables_sorts_by_member_count(self):
        self.assertEqual(
            self.names({"sort": "tables"}), ["ds_d", "ds_a", "ds_c", "ds_b"]
        )
        self.assertEqual(
            self.names({"sort": "-tables"}), ["ds_b", "ds_c", "ds_a", "ds_d"]
        )

    def test_created(self):
        self.assertEqual(
            self.names({"sort": "created"}), ["ds_a", "ds_b", "ds_c", "ds_d"]
        )
        self.assertEqual(
            self.names({"sort": "-created"}), ["ds_d", "ds_c", "ds_b", "ds_a"]
        )

    def test_ties_fall_back_to_the_title_then_the_key(self):
        for name in ("ds_t2", "ds_t1"):
            self.dataset(name, title="same", created=moment("2026-09-09"))
        tied = [n for n in self.names({"sort": "-created"}) if n.startswith("ds_t")]
        pks = {d.name: str(d.pk) for d in Dataset.objects.filter(name__in=tied)}
        self.assertEqual(tied, sorted(tied, key=pks.get))

    def test_a_tie_under_a_descending_sort_is_broken_by_title_ascending(self):
        for name, title in (("ds_tz", "zulu"), ("ds_ty", "yankee")):
            self.dataset(name, title=title, created=moment("2026-09-10"))
        tied = [n for n in self.names({"sort": "-created"}) if n.startswith("ds_t")]
        self.assertEqual(tied, ["ds_ty", "ds_tz"])

    def test_topics_is_not_sortable(self):
        self.assertNotIn("topics", self.page().sort_links)


class UrlAndPagingTests(DatasetsTabTestCase):
    def fill(self, count):
        Dataset.objects.bulk_create(
            Dataset(
                name=f"ds_{n:03d}", metadata={"title": f"t{n:03d}"}, creator=self.user
            )
            for n in range(count)
        )

    def test_twenty_five_per_page(self):
        self.fill(PAGE_SIZE + 3)
        self.assertEqual(len(self.names()), PAGE_SIZE)
        self.assertEqual(len(self.names({"page": "2"})), 3)

    def test_the_old_page_parameter_is_ignored(self):
        self.fill(PAGE_SIZE + 3)
        page = self.page({"datasets_page": "2"})
        self.assertEqual(page.number, 1)
        self.assertEqual(page.url, self.path)

    def test_defaults_are_never_written_and_a_filter_returns_to_page_one(self):
        self.fill(PAGE_SIZE + 3)
        page = self.page({"page": "2", "sort": "-modified", "status": ""})
        self.assertEqual(page.url, f"{self.path}?page=2")
        self.assertEqual(
            page.state.url(self.path, status="draft"), f"{self.path}?status=draft"
        )

    def test_htmx_gets_the_region_with_the_canonical_address(self):
        self.dataset("ds_x")
        response = self.get({"sort": "-modified", "search": "x"}, htmx=True)
        self.assertTemplateUsed(response, REGION)
        self.assertTemplateNotUsed(response, PAGE)
        self.assertEqual(response["HX-Push-Url"], f"{self.path}?search=x")

    def test_a_direct_load_and_htmx_render_the_same_state(self):
        self.dataset("ds_x", topics=("energy",))
        query = {"topics": "energy", "sort": "created"}
        whole = self.get(query).context["page"]
        region = self.get(query, htmx=True).context["page"]
        self.assertEqual([r.name for r in whole.rows], [r.name for r in region.rows])
        self.assertEqual(whole.url, region.url)
        self.assertEqual(whole.counts, region.counts)

    def test_a_history_restore_is_answered_with_the_whole_page(self):
        response = self.get(htmx=True, HTTP_HX_HISTORY_RESTORE_REQUEST="true")
        self.assertTemplateUsed(response, PAGE)


class RetiredRoutesTests(DatasetsTabTestCase):
    def test_the_card_routes_answer_404(self):
        self.dataset("ds_retired")
        base = f"{self.path}/ds_retired"
        for suffix in (
            "card",
            "edit",
            "delete",
            "manage",
            "table-search",
            "assign",
            "unassign",
        ):
            with self.subTest(route=suffix):
                self.assertEqual(self.client.get(f"{base}/{suffix}").status_code, 404)
                self.assertEqual(
                    self.client.post(f"{base}/{suffix}", **HTMX).status_code, 404
                )

    def test_the_list_takes_no_post(self):
        response = self.client.post(self.path, {"title": "New"}, **HTMX)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Dataset.objects.exists())


class QueryCountTests(DatasetsTabTestCase):
    """A page costs the same number of queries whatever the account and
    membership size."""

    def fill(self, count, members=2):
        tables = Table.objects.bulk_create(
            Table(name=f"q_t_{count}_{n:04d}", is_publish=n % 3 != 0)
            for n in range(members)
        )
        Embargo.objects.create(table=tables[-1], duration="1_year")
        topics = [Topic.objects.get_or_create(name=n)[0] for n in ("a", "b", "c")]
        tag = Tag.objects.get_or_create(name_normalized="q_tag", name="q_tag")[0]
        tables[0].tags.add(tag)
        now = timezone.now()
        datasets = Dataset.objects.bulk_create(
            Dataset(
                name=f"q_ds_{count}_{n:03d}",
                metadata={"title": f"Q {n}"},
                creator=self.user,
                published_at=now if n % 2 else None,
                modified_at=now - timedelta(days=n) if n % 3 else None,
            )
            for n in range(count)
        )
        through = Dataset.tables.through
        through.objects.bulk_create(
            through(dataset_id=dataset.pk, table_id=table.pk)
            for dataset in datasets
            for table in tables
        )
        # every Dataset carries "a", so the Topic filter narrows by a known
        # value in every scenario rather than reading as a stale chip
        for index, dataset in enumerate(datasets):
            dataset.topics.add(*topics[: 1 + index % 3])

    def empty(self):
        Dataset.objects.all().delete()
        Table.objects.filter(name__startswith="q_t_").delete()

    def queries(self, query=None):
        with CaptureQueriesContext(connection) as captured:
            self.get(query, htmx=True)
        return len(captured)

    def test_six_unfiltered_and_eight_with_topic_and_tag_at_every_size(self):
        """Six: the session and the user; the faceted segment aggregate; the
        page, with the member count and the mix as subqueries; the members
        the popovers name; the Topics. Naming Topic and Tag adds their option
        sources. Django caches the current Site after the first request in a
        process, so one request runs first."""
        self.get(htmx=True)
        filtered = {"topics": "a", "tags": "q_tag"}
        for count, members in ((3, 2), (30, 2), (1, 2500)):
            with self.subTest(datasets=count, members=members):
                self.fill(count, members)
                self.assertEqual(self.queries(), 6)
                self.assertEqual(self.queries(filtered), 8)
                self.empty()

    def test_a_dataset_of_2500_members_reads_ten_titles(self):
        self.fill(1, 2500)
        row = self.page().rows[0]
        self.assertEqual(row.member_count, 2500)
        self.assertEqual(len(row.members), MEMBERS_SHOWN)
        self.assertEqual(row.more_members, 2490)
