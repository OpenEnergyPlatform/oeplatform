"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The tables tab of the profile dashboard (#2553, spec #2551): one list of
every Table the user may write, with a status segment, search, sorting,
paging and the URL state, as seen through HTTP.

Assertions are on what the page says (rows, counts, links, headers, the
templates that rendered), never on markup details or seconds.
"""  # noqa: 501

from datetime import timedelta

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from dataedit.models import Embargo, Table
from login.models import (
    ADMIN_PERM,
    DELETE_PERM,
    NO_PERM,
    WRITE_PERM,
    GroupPermission,
    Membership,
    Organization,
    UserPermission,
)
from login.tests.helpers import HTMX, make_user

REGION = "login/partials/tables_region.html"
PAGE = "login/user_tables.html"


class TablesTabTestCase(TestCase):
    """A logged-in owner and helpers to give them Tables."""

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("TablesTabOwner")
        cls.stranger = make_user("TablesTabStranger")

    def setUp(self):
        self.client.force_login(self.user)

    @property
    def path(self):
        return reverse("login:tables", kwargs={"user_id": self.user.pk})

    def table(self, name, title=None, published=False, level=ADMIN_PERM, **extra):
        table = Table.objects.create(
            name=name, human_readable_name=title, is_publish=published, **extra
        )
        if level is not None:
            UserPermission.objects.create(holder=self.user, table=table, level=level)
        return table

    def organization(self, name, member=True):
        organization = Organization.objects.create(name=name)
        if member:
            Membership.objects.create(user=self.user, group=organization)
        return organization

    def get(self, query=None, htmx=False, **headers):
        if htmx:
            headers.update(HTMX)
        response = self.client.get(self.path, query or {}, **headers)
        self.assertEqual(response.status_code, 200)
        return response

    def page(self, query=None, **kwargs):
        return self.get(query, **kwargs).context["page"]

    def names(self, query=None, **kwargs):
        return [row.table.name for row in self.page(query, **kwargs).rows]

    def counts(self, query=None):
        page = self.page(query)
        return {link.id: link.count for link in page.segment_links}


class WhichTablesAreListedTests(TablesTabTestCase):
    def test_every_direct_role_from_data_editor_up_is_listed(self):
        for name, level in (
            ("t_editor", WRITE_PERM),
            ("t_maintainer", DELETE_PERM),
            ("t_admin", ADMIN_PERM),
        ):
            self.table(name, level=level)
        self.assertEqual(self.names(), ["t_admin", "t_editor", "t_maintainer"])

    def test_a_grant_below_data_editor_is_not_access(self):
        self.table("t_none", level=NO_PERM)
        self.assertEqual(self.names(), [])

    def test_a_strangers_table_is_not_listed(self):
        table = self.table("t_foreign", level=None)
        UserPermission.objects.create(
            holder=self.stranger, table=table, level=ADMIN_PERM
        )
        self.assertEqual(self.names(), [])

    def test_a_table_reached_through_an_organization_is_listed(self):
        organization = self.organization("Org Wind")
        table = self.table("t_org", level=None)
        GroupPermission.objects.create(
            holder=organization, table=table, level=WRITE_PERM
        )
        self.assertEqual(self.names(), ["t_org"])

    def test_an_organization_the_user_is_not_in_gives_no_access(self):
        organization = self.organization("Org Elsewhere", member=False)
        table = self.table("t_not_mine", level=None)
        GroupPermission.objects.create(
            holder=organization, table=table, level=ADMIN_PERM
        )
        self.assertEqual(self.names(), [])

    def test_an_organization_grant_below_data_editor_is_not_access(self):
        organization = self.organization("Org Nothing")
        table = self.table("t_org_none", level=None)
        GroupPermission.objects.create(holder=organization, table=table, level=NO_PERM)
        self.assertEqual(self.names(), [])

    def test_sandbox_tables_are_left_out(self):
        self.table("t_sandbox", is_sandbox=True)
        self.table("t_real")
        self.assertEqual(self.names(), ["t_real"])

    def test_a_table_reached_both_ways_is_one_row_and_counts_once(self):
        """The trap the OR-ing helper sets: two joins multiply an aggregate."""
        first, second = self.organization("Org A"), self.organization("Org B")
        table = self.table("t_twice", level=WRITE_PERM)
        for organization in (first, second):
            GroupPermission.objects.create(
                holder=organization, table=table, level=WRITE_PERM
            )
        self.assertEqual(self.names(), ["t_twice"])
        self.assertEqual(
            self.counts(), {"seg-all": 1, "seg-draft": 1, "seg-published": 0}
        )


class RowTests(TablesTabTestCase):
    def row(self, name):
        return next(row for row in self.page().rows if row.table.name == name)

    def test_title_with_the_technical_name_beneath(self):
        self.table("t_titled", title="Wind turbines")
        row = self.row("t_titled")
        self.assertEqual(row.title, "Wind turbines")
        self.assertTrue(row.has_title)

    def test_a_table_without_a_title_shows_its_name_once(self):
        self.table("t_untitled")
        self.table("t_blank", title="")
        for name in ("t_untitled", "t_blank"):
            with self.subTest(name=name):
                row = self.row(name)
                self.assertEqual(row.title, name)
                self.assertFalse(row.has_title)

    def test_the_title_links_to_the_table_page(self):
        self.table("t_linked", title="Linked")
        response = self.get()
        self.assertContains(
            response, reverse("dataedit:view", kwargs={"table": "t_linked"})
        )

    def test_status_draft_and_published(self):
        self.table("t_draft")
        self.table("t_published", published=True)
        self.assertEqual(self.row("t_draft").status, "draft")
        self.assertEqual(self.row("t_published").status, "published")

    def test_an_active_embargo_reads_embargoed_until_its_end(self):
        table = self.table("t_embargoed", published=True)
        embargo = Embargo.objects.create(table=table, duration="6_months")
        row = self.row("t_embargoed")
        self.assertEqual(row.status, "embargoed")
        self.assertEqual(row.embargo_until, embargo.date_ended)

    def test_an_expired_embargo_reads_published(self):
        table = self.table("t_expired", published=True)
        Embargo.objects.create(table=table, duration="6_months")
        Embargo.objects.filter(table=table).update(
            date_ended=timezone.now() - timedelta(days=1)
        )
        self.assertEqual(self.row("t_expired").status, "published")

    def test_a_draft_under_embargo_is_a_draft(self):
        table = self.table("t_draft_embargo")
        Embargo.objects.create(table=table, duration="1_year")
        self.assertEqual(self.row("t_draft_embargo").status, "draft")

    def test_access_you_and_no_role_for_a_direct_admin(self):
        self.table("t_mine")
        row = self.row("t_mine")
        self.assertTrue(row.direct)
        self.assertEqual(row.organizations, [])
        self.assertEqual(row.role_label, "")

    def test_the_role_is_shown_below_admin(self):
        self.table("t_edit", level=WRITE_PERM)
        self.table("t_maintain", level=DELETE_PERM)
        self.assertEqual(self.row("t_edit").role_label, "Data editor")
        self.assertEqual(self.row("t_maintain").role_label, "Data maintainer")

    def test_access_through_an_organization_names_it(self):
        organization = self.organization("Org Solar")
        table = self.table("t_org_only", level=None)
        GroupPermission.objects.create(
            holder=organization, table=table, level=DELETE_PERM
        )
        row = self.row("t_org_only")
        self.assertFalse(row.direct)
        self.assertEqual(row.organizations, ["Org Solar"])
        self.assertEqual(row.role_label, "Data maintainer")

    def test_the_effective_role_is_the_highest_of_all_grants(self):
        organization = self.organization("Org Admins")
        table = self.table("t_mixed", level=WRITE_PERM)
        GroupPermission.objects.create(
            holder=organization, table=table, level=ADMIN_PERM
        )
        row = self.row("t_mixed")
        self.assertTrue(row.direct)
        self.assertEqual(row.organizations, ["Org Admins"])
        self.assertEqual(row.role_label, "")

    def test_only_the_users_own_organizations_are_named(self):
        mine = self.organization("Org Mine")
        other = self.organization("Org Other", member=False)
        table = self.table("t_shared", level=None)
        for organization in (mine, other):
            GroupPermission.objects.create(
                holder=organization, table=table, level=WRITE_PERM
            )
        self.assertEqual(self.row("t_shared").organizations, ["Org Mine"])


class SegmentAndSearchTests(TablesTabTestCase):
    def setUp(self):
        super().setUp()
        self.table("wind_draft", title="Wind draft")
        self.table("wind_published", title="Wind published", published=True)
        self.table("solar_draft", title="Solar draft")

    def test_counts_split_the_whole_list(self):
        self.assertEqual(
            self.counts(), {"seg-all": 3, "seg-draft": 2, "seg-published": 1}
        )

    def test_the_status_segment_narrows_the_rows(self):
        self.assertEqual(self.names({"status": "draft"}), ["solar_draft", "wind_draft"])
        self.assertEqual(self.names({"status": "published"}), ["wind_published"])

    def test_counts_respect_the_search_but_not_the_status(self):
        expected = {"seg-all": 2, "seg-draft": 1, "seg-published": 1}
        self.assertEqual(self.counts({"search": "wind"}), expected)
        self.assertEqual(self.counts({"search": "wind", "status": "draft"}), expected)

    def test_a_segment_with_no_tables_stays_listed(self):
        page = self.page({"search": "solar"})
        self.assertEqual(
            [(link.id, link.count) for link in page.segment_links],
            [("seg-all", 1), ("seg-draft", 1), ("seg-published", 0)],
        )

    def test_search_matches_title_or_technical_name_ignoring_case(self):
        self.assertEqual(self.names({"search": "SOLAR"}), ["solar_draft"])
        self.assertEqual(self.names({"search": "_published"}), ["wind_published"])

    def test_an_unknown_status_is_ignored(self):
        self.assertEqual(len(self.names({"status": "deleted"})), 3)


class SortTests(TablesTabTestCase):
    def setUp(self):
        super().setUp()
        self.first_b = self.table("t_b_first", title="Beta", published=True)
        self.alpha = self.table("t_alpha", title="alpha")
        self.second_b = self.table("t_b_second", title="Beta")
        self.charlie = self.table("charlie_untitled", published=True)

    def test_default_is_displayed_title_case_insensitive_then_pk(self):
        self.assertEqual(
            self.names(), ["t_alpha", "t_b_first", "t_b_second", "charlie_untitled"]
        )

    def test_descending_title_keeps_the_pk_tiebreak_ascending(self):
        self.assertEqual(
            self.names({"sort": "-table"}),
            ["charlie_untitled", "t_b_first", "t_b_second", "t_alpha"],
        )

    def test_status_ascending_puts_drafts_first_then_title(self):
        self.assertEqual(
            self.names({"sort": "status"}),
            ["t_alpha", "t_b_second", "t_b_first", "charlie_untitled"],
        )

    def test_status_descending_puts_published_first_then_title(self):
        self.assertEqual(
            self.names({"sort": "-status"}),
            ["t_b_first", "charlie_untitled", "t_alpha", "t_b_second"],
        )

    def test_an_unknown_sort_falls_back_to_the_default(self):
        self.assertEqual(self.names({"sort": "rows"}), self.names())

    def test_a_click_sorts_by_the_column_then_toggles_it(self):
        links = self.page().sort_links
        self.assertEqual(links["table"].aria_sort, "ascending")
        self.assertEqual(links["table"].url, f"{self.path}?sort=-table")
        self.assertEqual(links["status"].aria_sort, "")
        self.assertEqual(links["status"].url, f"{self.path}?sort=status")
        toggled = self.page({"sort": "-table"}).sort_links["table"]
        self.assertEqual(toggled.aria_sort, "descending")
        self.assertEqual(toggled.url, self.path)


class PagingTests(TablesTabTestCase):
    def make(self, count):
        tables = Table.objects.bulk_create(
            Table(name=f"t_{index:03d}") for index in range(count)
        )
        UserPermission.objects.bulk_create(
            UserPermission(holder=self.user, table=table, level=ADMIN_PERM)
            for table in tables
        )

    def test_twenty_five_per_page(self):
        self.make(60)
        first, last = self.page(), self.page({"page": "3"})
        self.assertEqual(len(first.rows), 25)
        self.assertEqual((first.number, first.num_pages), (1, 3))
        self.assertEqual(len(last.rows), 10)
        self.assertEqual(last.range_text, "51–60 of 60")
        self.assertEqual(last.rows[0].table.name, "t_050")

    def test_a_page_past_the_end_shows_the_last_page(self):
        self.make(30)
        page = self.page({"page": "99"})
        self.assertEqual(page.number, 2)
        self.assertEqual([row.table.name for row in page.rows][0], "t_025")

    def test_a_page_that_is_not_a_number_is_the_first(self):
        self.make(30)
        for value in ("abc", "0", "-3"):
            with self.subTest(page=value):
                self.assertEqual(self.page({"page": value}).number, 1)

    def test_the_pager_is_hidden_when_one_page_suffices(self):
        self.make(25)
        response = self.get()
        self.assertEqual(response.context["page"].num_pages, 1)
        self.assertNotContains(response, 'id="pg-1"')

    def test_the_pager_shows_neighbours_and_both_ends(self):
        self.make(25 * 83)
        pager = self.page({"page": "8"}).pager
        self.assertEqual(
            [item.number for item in pager], [1, 2, None, 7, 8, 9, None, 82, 83]
        )
        self.assertEqual([item.number for item in pager if item.current], [8])

    def test_the_range_reads_with_thousands_separators(self):
        self.make(2068)
        self.assertEqual(self.page({"page": "8"}).range_text, "176–200 of 2,068")

    def test_the_old_section_page_parameters_are_ignored(self):
        self.make(30)
        response = self.get({"published_page": "2", "draft_page": "3"})
        self.assertEqual(response.context["page"].number, 1)
        self.assertEqual(len(response.context["page"].rows), 25)


class UrlStateTests(TablesTabTestCase):
    def setUp(self):
        super().setUp()
        tables = Table.objects.bulk_create(
            Table(name=f"wind_{index:02d}", is_publish=index % 2 == 0)
            for index in range(60)
        )
        UserPermission.objects.bulk_create(
            UserPermission(holder=self.user, table=table, level=ADMIN_PERM)
            for table in tables
        )

    def test_a_bare_address_is_the_default_state(self):
        page = self.page()
        self.assertEqual(page.url, self.path)
        self.assertEqual(page.segment_links[0].url, self.path)

    def test_defaults_are_never_written(self):
        page = self.page({"sort": "table", "page": "1", "search": "  ", "status": ""})
        self.assertEqual(page.url, self.path)

    def test_a_segment_link_returns_to_page_one_and_keeps_the_rest(self):
        page = self.page({"search": "wind", "sort": "-status", "page": "2"})
        draft = next(link for link in page.segment_links if link.id == "seg-draft")
        self.assertEqual(
            draft.url, f"{self.path}?search=wind&status=draft&sort=-status"
        )

    def test_a_sort_link_returns_to_page_one(self):
        page = self.page({"status": "draft", "page": "2"})
        self.assertEqual(
            page.sort_links["status"].url, f"{self.path}?status=draft&sort=status"
        )

    def test_pager_links_keep_the_filters_and_the_sort(self):
        page = self.page({"search": "wind", "sort": "-table"})
        self.assertEqual(page.next_url, f"{self.path}?search=wind&sort=-table&page=2")
        self.assertEqual(page.pager[0].url, f"{self.path}?search=wind&sort=-table")

    def test_the_htmx_answer_names_its_canonical_address(self):
        response = self.get(
            {"page": "99", "sort": "table", "status": "draft", "published_page": "2"},
            htmx=True,
        )
        self.assertEqual(response["HX-Push-Url"], f"{self.path}?status=draft&page=2")

    def test_reset_clears_filters_and_status_but_keeps_the_sort(self):
        page = self.page({"search": "solar", "status": "draft", "sort": "-status"})
        self.assertEqual(page.reset_url, f"{self.path}?sort=-status")


class RegionTests(TablesTabTestCase):
    def setUp(self):
        super().setUp()
        self.table("t_one", title="One")
        self.table("t_two", published=True)

    def template_names(self, response):
        return {template.name for template in response.templates}

    def test_a_direct_load_renders_the_whole_page(self):
        names = self.template_names(self.get())
        self.assertIn(PAGE, names)
        self.assertIn(REGION, names)

    def test_htmx_gets_only_the_results_region(self):
        response = self.get(htmx=True)
        names = self.template_names(response)
        self.assertIn(REGION, names)
        self.assertNotIn(PAGE, names)
        self.assertNotContains(response, 'id="tables-search"')
        self.assertNotContains(response, 'id="tables-live"')

    def test_both_answers_render_the_same_state(self):
        query = {"status": "draft", "sort": "-table"}
        self.assertEqual(self.names(query), self.names(query, htmx=True))

    def test_a_history_restore_gets_the_whole_page(self):
        response = self.get(HTTP_HX_HISTORY_RESTORE_REQUEST="true", htmx=True)
        self.assertIn(PAGE, self.template_names(response))
        self.assertNotIn("HX-Push-Url", response)

    def test_the_answer_varies_on_htmx(self):
        self.assertIn("HX-Request", self.get()["Vary"])

    def test_the_filter_bar_and_live_count_sit_outside_the_region(self):
        body = self.get().content.decode()
        region_at = body.index('id="tables-results"')
        self.assertLess(body.index('id="tables-search"'), region_at)
        self.assertLess(body.index('id="tables-live"'), region_at)

    def test_the_announcement_names_the_count(self):
        self.assertEqual(self.page().announcement, "2 tables, showing 1 to 2")
        self.assertEqual(
            self.page({"status": "draft"}).announcement,
            "1 table matches, showing 1 to 1",
        )


class EmptyStateTests(TablesTabTestCase):
    def test_no_tables_at_all_explains_and_offers_two_ways_in(self):
        response = self.get()
        self.assertFalse(response.context["page"].has_any)
        self.assertNotContains(response, 'id="tables-search"')
        self.assertContains(response, reverse("dataedit:wizard_create"))
        self.assertContains(response, "Upload via the API")

    def test_a_filter_in_the_address_does_not_hide_that_there_are_none(self):
        page = self.page({"search": "wind", "status": "draft"})
        self.assertFalse(page.has_any)
        self.assertEqual(page.announcement, "You have no tables yet")

    def test_no_match_offers_reset_and_keeps_the_filter_bar(self):
        self.table("t_solar")
        response = self.get({"search": "wind"})
        page = response.context["page"]
        self.assertTrue(page.has_any)
        self.assertEqual((page.total, page.rows), (0, []))
        self.assertEqual(page.announcement, "No tables match these filters")
        self.assertContains(response, 'id="tables-search"')
        self.assertContains(response, 'id="nomatch-reset"')

    def test_no_match_in_one_status_only(self):
        self.table("t_draft_only")
        page = self.page({"status": "published"})
        self.assertTrue(page.has_any)
        self.assertEqual(page.total, 0)


class LayoutTests(TablesTabTestCase):
    def test_the_identity_strip_replaces_the_profile_sidebar(self):
        names = {t.name for t in self.get().templates}
        self.assertIn("login/partials/identity_strip.html", names)
        self.assertNotIn("login/sidebar_user.html", names)

    def test_other_tabs_keep_the_sidebar(self):
        response = self.client.get(reverse("login:datasets", args=[self.user.pk]))
        names = {t.name for t in response.templates}
        self.assertIn("login/sidebar_user.html", names)
        self.assertNotIn("login/partials/identity_strip.html", names)

    def test_the_old_cards_reload_and_alert_are_gone(self):
        self.table("t_draft")
        self.table("t_published", published=True)
        body = self.get().content.decode()
        self.assertNotIn("window.location.reload", body)
        self.assertNotIn("alert(", body)
        self.assertNotIn("table_label", body)


class QueryCountTests(TablesTabTestCase):
    """A page costs the same number of queries whatever the account size."""

    def fill(self, count, organization):
        tables = Table.objects.bulk_create(
            Table(name=f"q_{index:04d}", is_publish=index % 3 == 0)
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
        Embargo.objects.create(table=tables[0], duration="1_year")

    def queries(self, query=None):
        with CaptureQueriesContext(connection) as captured:
            self.get(query, htmx=True)
        return len(captured)

    def test_four_and_a_hundred_and_thirty_tables_cost_the_same(self):
        organization = self.organization("Org Count")
        self.fill(4, organization)
        small = self.queries()
        Table.objects.filter(name__startswith="q_").delete()
        self.fill(130, organization)
        self.assertEqual(self.queries(), small)
        self.assertEqual(self.queries({"page": "6", "search": "q_"}), small)
