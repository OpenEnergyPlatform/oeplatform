"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Selecting Tables and acting on many at once (#2564, spec #2551): the select
column and the bulk bar the page renders, the names behind "Select all N
matching tables", the bulk preflight and its left-out groups, the ceilings,
and bulk publish and unpublish through the table action service, as seen
through HTTP.

The selection itself lives in the browser and is tested under vitest
(``login/static/login/__tests__/tables_tab.test.js``). Assertions here are on
rows, counts, what a preflight leaves out and why, what the database holds
afterwards and which response headers came back; never on seconds.
"""  # noqa: 501

import json
from unittest import mock

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from api.services import table_actions
from dataedit.models import Dataset, Embargo, Table
from login.models import (
    ADMIN_PERM,
    DELETE_PERM,
    WRITE_PERM,
    GroupPermission,
    Organization,
    UserPermission,
)
from login.tests.helpers import HTMX
from login.tests.test_table_actions import DIALOG, ActionTestCase
from login.tests.test_tables_columns import NO_LICENSE
from modelview.tests.html import element_markup, element_with_id, text

GATE_FAILED = "Fails the Publish gate: License"


class BulkTestCase(ActionTestCase):
    def names_path(self):
        return reverse("login:table-names", kwargs={"user_id": self.user.pk})

    def matching(self, query=None, **headers):
        response = self.client.get(self.names_path(), query or {}, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        return response.json()

    def check_path(self, action):
        return reverse(
            "login:table-action-check",
            kwargs={"user_id": self.user.pk, "action": action},
        )

    def bulk_preflight(self, action, *names, **params):
        response = self.client.post(
            self.check_path(action), {"table": list(names), **params}, **HTMX
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, DIALOG)
        return response

    def bulk_check(self, action, *names, **params):
        return self.bulk_preflight(action, *names, **params).context["preflight"]

    def left_out(self, check):
        return {group.reason: group.names for group in check.left_out}


class SelectColumnTests(BulkTestCase):
    def test_every_row_has_a_checkbox_labelled_with_its_title(self):
        titled = self.draft("t_titled", title="Wind farms")
        bare = self.draft("t_bare")
        html = self.get(htmx=True).content.decode()
        self.assertIn(
            'aria-label="Select Wind farms"',
            element_with_id(html, f"select-{titled.pk}"),
        )
        self.assertIn('value="t_titled"', element_with_id(html, f"select-{titled.pk}"))
        self.assertIn(
            'aria-label="Select t_bare"', element_with_id(html, f"select-{bare.pk}")
        )

    def test_the_header_checkbox_names_the_tables_on_this_page(self):
        for i in range(30):
            self.draft(f"t_page_{i:02}")
        html = self.get(htmx=True).content.decode()
        self.assertIn(
            'aria-label="Select all 25 tables on this page"',
            element_with_id(html, "select-page"),
        )
        last = self.get({"page": 2}, htmx=True).content.decode()
        self.assertIn(
            'aria-label="Select all 5 tables on this page"',
            element_with_id(last, "select-page"),
        )

    def test_a_stacked_list_selects_the_page_with_a_box_of_its_own(self):
        """Where the rows stack the header row is hidden (CSS), and with it
        #select-page; "Select this page" is the same control there
        (``data-select-page``, which tables_tab.js reads alike, #2596)."""
        self.draft("t_stack")
        html = self.get(htmx=True).content.decode()
        stacked = element_with_id(html, "select-page-stacked")
        self.assertIn("data-select-page", stacked)
        self.assertIn("data-select-page", element_with_id(html, "select-page"))
        self.assertIn('for="select-page-stacked"', html)
        none = self.get({"search": "nothing-matches"}, htmx=True).content.decode()
        self.assertEqual(element_with_id(none, "select-page-stacked"), "")

    def test_the_banner_offers_every_matching_table(self):
        for i in range(30):
            self.draft(f"t_banner_{i:02}")
        html = self.get({"status": "draft"}, htmx=True).content.decode()
        banner = element_with_id(html, "tables-select-all")
        self.assertIn('data-total="30"', banner)
        self.assertIn(f'data-names-url="{self.names_path()}?status=draft"', banner)
        self.assertIn("Select all 30 matching tables", html)

    def test_the_scope_is_the_filters_without_sort_and_page(self):
        """Paging and sorting keep a selection; anything else is a new
        scope, and the browser clears the selection on it."""
        for i in range(30):
            self.draft(f"t_scope_{i:02}")
        scope = self.page({"status": "draft", "sort": "table", "page": "2"}).scope
        self.assertEqual(scope, "?status=draft")
        self.assertEqual(self.page({"sort": "-table"}).scope, "")
        self.assertEqual(
            self.page({"search": "scope", "publishable": "yes"}).scope,
            "?search=scope&publishable=yes",
        )

    def test_the_rows_cost_no_query(self):
        """The select column is in the row partial already: still 7 per
        list request (session, user, facets, page, two grant lookups,
        Datasets)."""
        for i in range(4):
            self.draft(f"t_q_{i}")
        self.get(htmx=True)  # warms the Site cache
        with self.assertNumQueries(7):
            self.get(htmx=True)


class BulkBarTests(BulkTestCase):
    def test_the_bar_is_outside_the_region_with_its_slot_reserved(self):
        self.draft("t_bar")
        response = self.get()
        html = response.content.decode()
        self.assertTemplateUsed(response, "login/user_tables.html")
        self.assertIn('aria-hidden="true"', element_with_id(html, "tables-bulk-idle"))
        self.assertIn("Tick tables to act on several at once.", html)
        self.assertIn("hidden", element_with_id(html, "tables-bulk-bar"))
        region_start = html.index('id="tables-results"')
        self.assertLess(html.index('id="tables-bulk"'), region_start)

    def test_the_bar_offers_publish_and_unpublish_through_the_bulk_preflight(self):
        self.draft("t_actions")
        html = self.get().content.decode()
        for verb in ("publish", "unpublish"):
            with self.subTest(verb=verb):
                button = element_with_id(html, f"bulk-{verb}")
                self.assertIn(f'hx-post="{self.check_path(verb)}"', button)
                self.assertIn("data-bulk-action", button)

    def test_an_htmx_list_request_does_not_carry_the_bar(self):
        self.draft("t_region_only")
        html = self.get(htmx=True).content.decode()
        self.assertNotIn('id="tables-bulk"', html)

    def test_no_bar_without_tables(self):
        html = self.get().content.decode()
        self.assertNotIn('id="tables-bulk"', html)


class MatchingNamesTests(BulkTestCase):
    def test_every_matching_name_across_all_pages(self):
        for i in range(30):
            self.draft(f"t_all_{i:02}")
        self.draft("t_all_published", published=True)
        answer = self.matching({"status": "draft"})
        self.assertEqual(answer["total"], 30)
        self.assertEqual(answer["names"], [f"t_all_{i:02}" for i in range(30)])

    def test_the_same_filters_as_the_list_including_publishable(self):
        self.draft("t_yes", publishable=True)
        self.draft("t_no", publishable=False)
        self.draft("t_unknown")
        query = {"publishable": "yes"}
        self.assertEqual(self.matching(query)["names"], ["t_yes"])
        self.assertEqual(
            self.matching(query)["names"],
            sorted(row.table.name for row in self.page(query).rows),
        )
        self.assertEqual(self.matching({"publishable": "no"})["names"], ["t_no"])

    def test_search_and_an_option_filter_combine(self):
        organization = self.organization("Wind Org")
        shared = self.draft("t_wind_org", level=None)
        GroupPermission.objects.create(
            holder=organization, table=shared, level=WRITE_PERM
        )
        self.draft("t_wind_mine")
        self.draft("t_solar_mine")
        query = {"search": "wind", "access": str(organization.pk)}
        self.assertEqual(self.matching(query)["names"], ["t_wind_org"])

    def test_sort_and_page_are_ignored(self):
        for i in range(30):
            self.draft(f"t_paged_{i:02}")
        answer = self.matching({"sort": "-table", "page": "2"})
        self.assertEqual(answer["total"], 30)

    def test_a_value_that_no_longer_applies_narrows_nothing(self):
        self.draft("t_stale_one")
        self.draft("t_stale_two")
        answer = self.matching({"dataset": "no_such_dataset"})
        self.assertEqual(answer["names"], ["t_stale_one", "t_stale_two"])

    def test_only_tables_on_the_dashboard(self):
        self.draft("t_mine_listed")
        stranger = Table.objects.create(name="t_strangers")
        UserPermission.objects.create(
            holder=self.stranger, table=stranger, level=WRITE_PERM
        )
        Table.objects.create(name="t_sandboxed", is_sandbox=True)
        UserPermission.objects.create(
            holder=self.user,
            table=Table.objects.get(name="t_sandboxed"),
            level=WRITE_PERM,
        )
        self.assertEqual(self.matching()["names"], ["t_mine_listed"])

    def test_another_users_names_are_not_served(self):
        self.draft("t_private")
        self.client.force_login(self.stranger)
        response = self.client.get(self.names_path(), **HTMX)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(b"t_private", response.content)

    def test_one_query_for_the_names(self):
        for i in range(40):
            self.draft(f"t_cheap_{i:02}")
        self.matching()  # warms the Site cache
        with self.assertNumQueries(3):  # session, user, the names
            self.matching({"publishable": "no", "status": "draft"})


class BulkPreflightTests(BulkTestCase):
    def test_posted_names_answer_what_the_row_preflight_answers(self):
        self.draft("t_post_a")
        self.draft("t_post_b", published=True)
        posted = self.bulk_check("publish", "t_post_a", "t_post_b")
        read = self.check("publish", "t_post_a", "t_post_b")
        self.assertEqual(posted.names, read.names)
        self.assertEqual(posted.left_out, read.left_out)

    def test_bulk_publish_leaves_out_by_role_status_and_gate_with_names(self):
        self.draft("t_ok")
        self.draft("t_editor", level=WRITE_PERM)
        self.draft("t_maintainer", level=DELETE_PERM)
        self.draft("t_out", published=True)
        self.draft("t_unlicensed", oemetadata=NO_LICENSE, publishable=False)
        check = self.bulk_check(
            "publish", "t_ok", "t_editor", "t_maintainer", "t_out", "t_unlicensed"
        )
        self.assertEqual(check.names, ["t_ok"])
        self.assertEqual(
            self.left_out(check),
            {
                "Only Table admins can publish": ["t_editor", "t_maintainer"],
                "Already published": ["t_out"],
                GATE_FAILED: ["t_unlicensed"],
            },
        )
        html = self.bulk_preflight(
            "publish", "t_ok", "t_editor", "t_out", "t_unlicensed"
        ).content.decode()
        # each left-out group names its Tables
        self.assertNotEqual(element_with_id(html, "table-action-left-out"), "")
        for name in ("t_editor", "t_out", "t_unlicensed"):
            self.assertIn(f"<code>{name}</code>", html)

    def test_the_stored_gate_flag_decides_without_a_validator_pass(self):
        """A stored pass is not validated again, so a batch of publishable
        Tables costs no validator pass; publishing still validates live."""
        for i in range(3):
            self.draft(f"t_stored_{i}", publishable=True)
        with mock.patch.object(
            Table, "validate_open_data_license", side_effect=AssertionError
        ):
            check = self.bulk_check("publish", *[f"t_stored_{i}" for i in range(3)])
        self.assertEqual(len(check.eligible), 3)

    def test_a_stored_fail_is_validated_for_its_reason(self):
        """The reason the dialog names comes from the gate run on that Table
        only; when it passes after all, the flag was stale and live wins."""
        self.draft("t_fail", oemetadata=NO_LICENSE, publishable=False)
        self.draft("t_stale_fail", publishable=False)
        check = self.bulk_check("publish", "t_fail", "t_stale_fail")
        self.assertEqual(check.names, ["t_stale_fail"])
        self.assertEqual(self.left_out(check), {GATE_FAILED: ["t_fail"]})

    def test_a_table_never_judged_runs_the_gate_live(self):
        """NULL: before ``recompute_publish_gate`` has run on an old Table.
        It is neither kept out nor let through on faith."""
        self.draft("t_null_pass")
        self.draft("t_null_fail", oemetadata=NO_LICENSE)
        self.assertIsNone(Table.objects.get(name="t_null_pass").publishable)
        check = self.bulk_check("publish", "t_null_pass", "t_null_fail")
        self.assertEqual(check.names, ["t_null_pass"])
        self.assertEqual(self.left_out(check), {GATE_FAILED: ["t_null_fail"]})

    def test_nothing_eligible_says_why_and_offers_no_confirm(self):
        self.draft("t_done", published=True)
        self.draft("t_done_too", published=True)
        html = self.bulk_preflight("publish", "t_done", "t_done_too").content.decode()
        self.assertNotEqual(element_with_id(html, "table-action-left-out"), "")
        self.assertIn("Already published", html)
        self.assertNotEqual(element_with_id(html, "table-action-nothing"), "")
        self.assertEqual(element_with_id(html, "table-action-confirm"), "")

    def test_the_confirmation_lists_what_will_run_and_posts_exactly_that(self):
        self.draft("t_run_a")
        self.draft("t_run_b")
        self.draft("t_run_skip", published=True)
        response = self.bulk_preflight("publish", "t_run_a", "t_run_b", "t_run_skip")
        html = response.content.decode()
        form = element_with_id(html, "table-action-form")
        self.assertIn(f'hx-post="{self.action_path("publish")}"', form)
        self.assertIn('name="tables" value="t_run_a,t_run_b"', html)
        self.assertNotIn('t_run_skip"', html)
        self.assertIn('name="topic"', html)
        self.assertIn('name="embargo"', html)

    def test_bulk_unpublish_names_other_peoples_datasets(self):
        table = self.draft("t_cited", published=True)
        plain = self.draft("t_plain", published=True)
        self.draft("t_also", published=True)
        self.draft("t_draft_already")
        theirs = Dataset.objects.create(
            name="ds_theirs", creator=self.stranger, metadata={"title": "Grid study"}
        )
        theirs.tables.add(table, plain)
        response = self.bulk_preflight(
            "unpublish", "t_cited", "t_plain", "t_also", "t_draft_already"
        )
        check = response.context["preflight"]
        self.assertEqual(check.names, ["t_cited", "t_plain", "t_also"])
        self.assertEqual(self.left_out(check), {"Not published": ["t_draft_already"]})
        # by title, with how many of these Tables each holds
        self.assertEqual(
            check.consequences["others_datasets"],
            [(self.stranger.name, "Grid study", 2)],
        )
        self.assertEqual(check.confirmation, "")
        self.assertIn(
            f"Grid study ({self.stranger.name}): 2 tables",
            text(element_markup(response.content.decode(), "table-action-datasets")),
        )

    def test_a_preflight_writes_nothing(self):
        self.draft("t_untouched")
        self.client.post(
            self.check_path("publish"),
            {"table": ["t_untouched"], "topic": "climate"},
            **HTMX,
        )
        self.assertEqual(self.published("t_untouched"), {"t_untouched": False})

    def test_the_bulk_preflight_takes_only_post(self):
        response = self.client.get(self.check_path("publish"), **HTMX)
        self.assertEqual(response.status_code, 405)

    def test_an_unknown_action_is_404(self):
        response = self.client.post(self.check_path("rename"), {}, **HTMX)
        self.assertEqual(response.status_code, 404)


class BulkCountTests(BulkTestCase):
    """A bulk dialog's title and its list count the same thing, the Tables
    the action acts on, and the title says out of how many were sent when
    some are left out (#2596). One Table keeps its title."""

    def title(self, response):
        return text(element_markup(response.content.decode(), "table-action-title"))

    def test_title_and_list_count_the_tables_acted_on(self):
        for action, verb, published in (
            ("publish", "published", False),
            ("delete", "deleted", False),
            ("unpublish", "unpublished", True),
        ):
            with self.subTest(action=action):
                names = [f"t_{action}_{i}" for i in range(3)]
                for name in names:
                    self.draft(name, published=published)
                # one each the action leaves out: the user is a Data editor
                self.draft(f"t_{action}_editor", level=WRITE_PERM, published=published)
                response = self.bulk_preflight(action, *names, f"t_{action}_editor")
                check = response.context["preflight"]
                self.assertEqual(check.subject, "3 of 4 tables")
                self.assertEqual(check.left_out_count, 1)
                self.assertEqual(
                    self.title(response), f"{action.capitalize()} 3 of 4 tables"
                )
                html = response.content.decode()
                self.assertEqual(
                    text(element_markup(html, "table-action-list-label")),
                    f"Will be {verb} (3):",
                )
                self.assertTrue(
                    text(element_markup(html, "table-action-left-out")).startswith(
                        "Left out (1):"
                    )
                )

    def test_with_nothing_left_out_the_title_counts_every_name(self):
        self.draft("t_all_a")
        self.draft("t_all_b")
        response = self.bulk_preflight("publish", "t_all_a", "t_all_b")
        self.assertEqual(self.title(response), "Publish 2 tables")
        self.assertEqual(
            text(element_markup(response.content.decode(), "table-action-list-label")),
            "Will be published (2):",
        )

    def test_with_nothing_eligible_the_title_says_none_of_them(self):
        self.draft("t_none_a")
        self.draft("t_none_b")
        response = self.bulk_preflight("unpublish", "t_none_a", "t_none_b")
        self.assertEqual(self.title(response), "Unpublish 0 of 2 tables")
        self.assertNotEqual(
            element_with_id(response.content.decode(), "table-action-nothing"), ""
        )

    def test_one_table_is_named_by_its_title_even_when_left_out(self):
        self.draft("t_one", title="Wind farms", published=True)
        response = self.bulk_preflight("publish", "t_one")
        self.assertEqual(self.title(response), "Publish “Wind farms”")

    def test_over_the_ceiling_the_title_counts_the_names_sent(self):
        names = [f"t_over_{i}" for i in range(4)]
        for name in names:
            self.draft(name)
        with mock.patch.dict(table_actions.CEILINGS, {"publish": 3}):
            response = self.bulk_preflight("publish", *names)
        self.assertEqual(self.title(response), "Publish 4 tables")


class CeilingTests(BulkTestCase):
    def test_publish_and_unpublish_have_a_measured_ceiling(self):
        for action in ("publish", "unpublish"):
            with self.subTest(action=action):
                self.assertGreater(table_actions.CEILINGS[action], 100)

    def test_over_the_ceiling_the_dialog_says_so_and_reads_no_table(self):
        names = [f"t_many_{i}" for i in range(4)]
        for name in names:
            self.draft(name)
        with mock.patch.dict(table_actions.CEILINGS, {"publish": 3}):
            with CaptureQueriesContext(connection) as queries:
                response = self.bulk_preflight("publish", *names)
        check = response.context["preflight"]
        self.assertTrue(check.over_ceiling)
        self.assertEqual(check.eligible, [])
        self.assertContains(
            response, "Publish takes at most 3 tables at a time; you selected 4."
        )
        self.assertEqual(
            element_with_id(response.content.decode(), "table-action-confirm"), ""
        )
        tables = Table._meta.db_table
        self.assertFalse(
            [q["sql"] for q in queries.captured_queries if f'"{tables}"' in q["sql"]]
        )

    def test_over_the_ceiling_nothing_is_published(self):
        names = [f"t_over_{i}" for i in range(3)]
        for name in names:
            self.draft(name)
        with mock.patch.dict(table_actions.CEILINGS, {"publish": 2}):
            response = self.run_action("publish", *names, topic="climate")
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Publish takes at most 2 tables at a time; you selected 3.",
            response.context["errors"]["table"],
        )
        self.assertEqual(set(self.published(*names).values()), {False})

    def test_a_selection_past_djangos_field_limit_reaches_the_preflight(self):
        """The largest dashboard holds 2,068 Tables. Sent as repeated
        ``table`` parameters, Django refuses that many before any view runs
        (``DATA_UPLOAD_MAX_NUMBER_FIELDS``, 1,000), so the bulk bar joins
        them into one ``tables`` field."""
        names = ",".join(f"t_big_{i}" for i in range(2068))
        response = self.client.post(
            self.check_path("publish"), {"tables": names}, **HTMX
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Publish takes at most 1,000 tables at a time; you selected 2,068.",
        )

    def test_a_batch_at_the_ceiling_reaches_the_service(self):
        """The dialog's form posts the eligible names joined as well: at the
        ceiling, 1,000 names plus Topic, embargo and the CSRF token would
        pass the field limit as separate fields."""
        self.draft("t_at_ceiling")
        names = ["t_at_ceiling"] + [f"t_absent_{i}" for i in range(999)]
        response = self.client.post(
            self.action_path("publish"),
            {"tables": ",".join(names), "topic": "climate", "embargo": "none"},
            **HTMX,
        )
        # refused by the service, which names what is not the user's
        self.assertEqual(response.status_code, 409)
        self.assertIn(
            "Not one of your tables",
            self.trigger(response, "tables-refused")["message"],
        )
        self.assertEqual(self.published("t_at_ceiling"), {"t_at_ceiling": False})

    def test_joined_and_repeated_names_are_one_selection(self):
        self.draft("t_joined_a")
        self.draft("t_joined_b")
        self.draft("t_repeated")
        response = self.client.post(
            self.check_path("publish"),
            {"tables": "t_joined_a, t_joined_b,", "table": ["t_repeated"]},
            **HTMX,
        )
        self.assertEqual(
            sorted(response.context["preflight"].names),
            ["t_joined_a", "t_joined_b", "t_repeated"],
        )

    def test_unpublish_states_its_ceiling(self):
        names = [f"t_unpub_{i}" for i in range(3)]
        for name in names:
            self.draft(name, published=True)
        with mock.patch.dict(table_actions.CEILINGS, {"unpublish": 2}):
            response = self.bulk_preflight("unpublish", *names)
        self.assertContains(
            response, "Unpublish takes at most 2 tables at a time; you selected 3."
        )


class BulkPublishTests(BulkTestCase):
    def test_one_topic_and_one_embargo_for_the_whole_batch(self):
        names = ["t_series_1", "t_series_2", "t_series_3"]
        for name in names:
            self.draft(name)
        response = self.run_action(
            "publish", *names, topic="climate", embargo="6_months"
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(set(self.published(*names).values()), {True})
        for name in names:
            table = Table.objects.get(name=name)
            self.assertEqual(
                list(table.topics.values_list("name", flat=True)), ["climate"]
            )
        self.assertEqual(
            set(
                Embargo.objects.filter(table__name__in=names).values_list(
                    "duration", flat=True
                )
            ),
            {"6_months"},
        )
        self.assertEqual(Embargo.objects.filter(table__name__in=names).count(), 3)

    def test_a_bulk_success_has_a_summary_and_the_tables_to_show(self):
        self.draft("t_sum_a", title="Alpha")
        self.draft("t_sum_b")
        response = self.run_action(
            "publish", "t_sum_a", "t_sum_b", topic="climate", embargo="1_year"
        )
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(
            detail["message"],
            "Published 2 tables under climate, embargoed for 1 year.",
        )
        self.assertEqual(detail["tables"], ["“Alpha”", "“t_sum_b”"])
        self.assertNotIn("gone", detail)

    def test_a_row_action_has_no_list_to_show(self):
        self.draft("t_single")
        detail = self.trigger(
            self.run_action("publish", "t_single", topic="climate"), "tables-changed"
        )
        self.assertNotIn("tables", detail)

    def test_one_table_gone_stale_refuses_the_whole_batch(self):
        self.draft("t_fresh_1")
        self.draft("t_fresh_2")
        self.draft("t_now_published")
        # between the confirmation and the run, someone published one
        Table.objects.filter(name="t_now_published").update(is_publish=True)
        response = self.run_action(
            "publish", "t_fresh_1", "t_fresh_2", "t_now_published", topic="climate"
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            set(self.published("t_fresh_1", "t_fresh_2").values()), {False}
        )
        self.assertFalse(Table.objects.get(name="t_fresh_1").topics.exists())
        message = self.trigger(response, "tables-refused")["message"]
        self.assertIn("Already published", message)
        self.assertIn("t_now_published", message)
        # the still-open dialog shows the check run again
        self.assertEqual(
            response.context["preflight"].names, ["t_fresh_1", "t_fresh_2"]
        )

    def test_a_table_left_out_by_the_preflight_and_sent_anyway_is_refused(self):
        self.draft("t_mine_ok")
        self.draft("t_editor_only", level=WRITE_PERM)
        response = self.run_action(
            "publish", "t_mine_ok", "t_editor_only", topic="climate"
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.published("t_mine_ok", "t_editor_only"),
            {"t_mine_ok": False, "t_editor_only": False},
        )

    def test_through_an_organization_admin_grant(self):
        organization = Organization.objects.create(name="Admins Org")
        organization.memberships.create(user=self.user)
        table = self.draft("t_org_bulk", level=None)
        GroupPermission.objects.create(
            holder=organization, table=table, level=ADMIN_PERM
        )
        self.draft("t_direct_bulk")
        response = self.run_action(
            "publish", "t_org_bulk", "t_direct_bulk", topic="climate"
        )
        self.assertEqual(response.status_code, 204)


class BulkUnpublishTests(BulkTestCase):
    def test_every_table_goes_back_to_draft_in_one_request(self):
        names = ["t_back_1", "t_back_2"]
        for name in names:
            self.draft(name, published=True)
        response = self.run_action("unpublish", *names)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(set(self.published(*names).values()), {False})
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(
            detail["message"],
            "Unpublished 2 tables. No longer listed under their topics.",
        )
        self.assertEqual(len(detail["tables"]), 2)

    def test_a_draft_in_the_batch_refuses_it_whole(self):
        self.draft("t_pub_x", published=True)
        self.draft("t_draft_x")
        response = self.run_action("unpublish", "t_pub_x", "t_draft_x")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.published("t_pub_x"), {"t_pub_x": True})


class GoneTablesTests(BulkTestCase):
    """What left the dashboard is named, so the selection lets go of it."""

    def test_a_delete_names_the_tables_that_are_gone(self):
        self.draft("t_bin_1")
        self.draft("t_bin_2")
        with mock.patch.object(Table, "drop_oedb_table"):
            response = self.run_action("delete", "t_bin_1", "t_bin_2")
        self.assertEqual(response.status_code, 204)
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(sorted(detail["gone"]), ["t_bin_1", "t_bin_2"])

    def test_leaving_a_table_in_the_access_drawer_names_it(self):
        table = self.draft("t_leaving")
        UserPermission.objects.create(
            holder=self.stranger, table=table, level=ADMIN_PERM
        )
        response = self.client.post(
            reverse(
                "login:table-access",
                kwargs={"user_id": self.user.pk, "table_name": "t_leaving"},
            ),
            {"op": "leave", "confirm": "yes"},
            **HTMX,
        )
        self.assertEqual(response.status_code, 200)
        detail = json.loads(response["HX-Trigger"])["tables-changed"]
        self.assertEqual(detail["gone"], ["t_leaving"])
        self.assertTrue(detail["stay"])

    def test_a_change_that_keeps_the_table_names_nothing_gone(self):
        self.draft("t_kept_access")
        response = self.client.post(
            reverse(
                "login:table-access",
                kwargs={"user_id": self.user.pk, "table_name": "t_kept_access"},
            ),
            {
                "op": "add",
                "kind": "user",
                "name": self.stranger.name,
                "level": str(WRITE_PERM),
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 200)
        detail = json.loads(response["HX-Trigger"])["tables-changed"]
        self.assertNotIn("gone", detail)
