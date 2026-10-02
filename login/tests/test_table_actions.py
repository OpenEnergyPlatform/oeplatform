"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The row action pipeline of the tables tab (#2561, spec #2551): the ⋯ menu,
the action dialog's preflight, publish and unpublish through the table action
service, and the list's re-fetch afterwards, as seen through HTTP.

Assertions are on what the user is offered and told, what the database holds
afterwards, which response headers came back and which log lines were
written; never on seconds.
"""  # noqa: 501

import json
from unittest import mock

from django.urls import reverse

from api.error import APIError
from api.services import table_actions
from dataedit.models import Dataset, Embargo, Table, Topic
from login.models import (
    ADMIN_PERM,
    DELETE_PERM,
    WRITE_PERM,
    GroupPermission,
    Organization,
    UserPermission,
)
from login.tests.helpers import HTMX
from login.tests.test_tables_columns import NO_LICENSE, OPEN_LICENSE
from login.tests.test_tables_tab import TablesTabTestCase
from modelview.tests.html import element_with_id
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

DIALOG = "login/partials/table_action_dialog.html"


class ActionTestCase(TablesTabTestCase):
    def draft(self, name, level=ADMIN_PERM, **extra):
        extra.setdefault("oemetadata", OPEN_LICENSE)
        return self.table(name, level=level, **extra)

    def action_path(self, action):
        return reverse(
            "login:table-action", kwargs={"user_id": self.user.pk, "action": action}
        )

    def preflight(self, action, *names):
        response = self.client.get(
            self.action_path(action), {"table": list(names)}, **HTMX
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, DIALOG)
        return response

    def check(self, action, *names):
        return self.preflight(action, *names).context["preflight"]

    def run_action(self, action, *names, current=None, **params):
        headers = dict(HTMX)
        if current is not None:
            headers["HTTP_HX_CURRENT_URL"] = f"http://testserver{self.path}{current}"
        return self.client.post(
            self.action_path(action), {"table": list(names), **params}, **headers
        )

    def trigger(self, response, event):
        return json.loads(response["HX-Trigger"])[event]

    def published(self, *names):
        return dict(
            Table.objects.filter(name__in=names).values_list("name", "is_publish")
        )


class RowMenuTests(ActionTestCase):
    def html(self):
        return self.get(htmx=True).content.decode()

    def test_a_table_admin_is_offered_publish_on_a_draft(self):
        table = self.draft("t_mine")
        entry = element_with_id(self.html(), f"menu-{table.pk}-publish")
        self.assertIn(
            f'hx-get="{self.action_path("publish")}?table=t_mine"', entry, entry
        )
        self.assertNotIn("aria-disabled", entry)

    def test_a_published_table_offers_unpublish_instead(self):
        table = self.draft("t_out", published=True)
        html = self.html()
        self.assertIn("hx-get", element_with_id(html, f"menu-{table.pk}-unpublish"))
        self.assertEqual(element_with_id(html, f"menu-{table.pk}-publish"), "")

    def test_below_table_admin_the_action_is_disabled_with_the_reason(self):
        for level in (WRITE_PERM, DELETE_PERM):
            Table.objects.all().delete()
            table = self.draft(f"t_level_{level}", level=level)
            with self.subTest(level=level):
                response = self.get(htmx=True)
                entry = element_with_id(
                    response.content.decode(), f"menu-{table.pk}-publish"
                )
                self.assertIn('aria-disabled="true"', entry)
                # Bootstrap's .disabled would take it out of the keyboard order
                self.assertNotRegex(entry, r'class="[^"]*\bdisabled\b')
                self.assertNotIn("hx-get", entry)
                self.assertContains(response, "Only Table admins can publish")

    def test_a_role_through_an_organization_counts(self):
        organization = Organization.objects.create(name="Org Admins")
        organization.memberships.create(user=self.user)
        table = self.draft("t_org_admin", level=None)
        GroupPermission.objects.create(
            holder=organization, table=table, level=ADMIN_PERM
        )
        entry = element_with_id(self.html(), f"menu-{table.pk}-publish")
        self.assertNotIn("aria-disabled", entry)

    def test_edit_metadata_and_upload_link_to_the_existing_pages(self):
        table = self.draft("t_links")
        html = self.html()
        self.assertIn(
            reverse("dataedit:meta_edit", kwargs={"table": "t_links"}),
            element_with_id(html, f"menu-{table.pk}-edit"),
        )
        self.assertIn(
            reverse("dataedit:wizard_upload", kwargs={"table": "t_links"}),
            element_with_id(html, f"menu-{table.pk}-upload"),
        )

    def test_entries_whose_ticket_has_not_landed_are_absent(self):
        table = self.draft("t_later")
        html = self.html()
        for entry in ("delete", "access"):
            with self.subTest(entry=entry):
                self.assertEqual(element_with_id(html, f"menu-{table.pk}-{entry}"), "")

    def test_the_menu_costs_no_query(self):
        """The role gates come from the page's context and the row's level,
        which the page already reads; the 7-query budget is untouched."""
        self.draft("t_count")
        self.get(htmx=True)  # warm the Site cache, as QueryCountTests does
        with self.assertNumQueries(7):
            self.get(htmx=True)


class PreflightTests(ActionTestCase):
    def test_an_eligible_draft(self):
        self.draft("t_ready", title="Ready")
        check = self.check("publish", "t_ready")
        self.assertEqual(check.names, ["t_ready"])
        self.assertEqual(check.left_out, [])
        self.assertEqual(check.subject, "“Ready”")

    def test_left_out_groups_name_their_reason(self):
        self.draft("t_ok")
        self.draft("t_editor", level=WRITE_PERM)
        self.draft("t_already", published=True)
        self.draft("t_unlicensed", oemetadata=NO_LICENSE)
        foreign = Table.objects.create(name="t_foreign", oemetadata=OPEN_LICENSE)
        UserPermission.objects.create(
            holder=self.stranger, table=foreign, level=ADMIN_PERM
        )
        check = self.check(
            "publish",
            "t_ok",
            "t_editor",
            "t_already",
            "t_unlicensed",
            "t_foreign",
            "t_missing",
        )
        self.assertEqual(check.total, 6)
        self.assertEqual(check.names, ["t_ok"])
        self.assertEqual(
            {group.reason: group.names for group in check.left_out},
            {
                "Only Table admins can publish": ["t_editor"],
                "Already published": ["t_already"],
                "Fails the Publish gate: License": ["t_unlicensed"],
                # one reason for both, so the answer does not reveal which
                # Tables exist
                "Not one of your tables": ["t_foreign", "t_missing"],
            },
        )

    def test_unpublish_leaves_out_drafts_and_roles_below_admin(self):
        self.draft("t_pub", published=True)
        self.draft("t_pub_editor", published=True, level=WRITE_PERM)
        self.draft("t_draft")
        check = self.check("unpublish", "t_pub", "t_pub_editor", "t_draft")
        self.assertEqual(check.names, ["t_pub"])
        self.assertEqual(
            {group.reason: group.names for group in check.left_out},
            {
                "Only Table admins can unpublish": ["t_pub_editor"],
                "Not published": ["t_draft"],
            },
        )

    def test_only_real_topics_are_offered(self):
        Topic.objects.get_or_create(name=PSEUDO_TOPIC_DRAFT)
        self.draft("t_topics")
        topics = [
            t.name for t in self.preflight("publish", "t_topics").context["topics"]
        ]
        self.assertNotIn(PSEUDO_TOPIC_DRAFT, topics)
        self.assertEqual(
            topics,
            sorted(
                Topic.objects.exclude(name=PSEUDO_TOPIC_DRAFT).values_list(
                    "name", flat=True
                )
            ),
        )
        self.assertGreaterEqual(len(topics), 13)

    def test_unpublish_names_other_peoples_datasets(self):
        table = self.draft("t_cited", published=True)
        Dataset.objects.create(name="ds_mine", creator=self.user).tables.add(table)
        Dataset.objects.create(name="ds_theirs", creator=self.stranger).tables.add(
            table
        )
        response = self.preflight("unpublish", "t_cited")
        self.assertEqual(
            response.context["preflight"].consequences["others_datasets"],
            [(self.stranger.name, "ds_theirs")],
        )
        self.assertContains(response, "no longer be listed under its topics")

    def test_nothing_eligible_offers_no_confirmation(self):
        self.draft("t_noconfirm", level=WRITE_PERM)
        response = self.preflight("publish", "t_noconfirm")
        self.assertEqual(
            element_with_id(response.content.decode(), "table-action-confirm"), ""
        )
        self.assertContains(response, "Nothing to")

    def test_a_preflight_writes_nothing(self):
        self.draft("t_untouched")
        self.check("publish", "t_untouched")
        self.assertEqual(self.published("t_untouched"), {"t_untouched": False})

    def test_an_unknown_action_is_not_found(self):
        response = self.client.get(self.action_path("explode"), {"table": "x"}, **HTMX)
        self.assertEqual(response.status_code, 404)

    def test_another_users_endpoint_is_not_found(self):
        self.draft("t_owner_rule")
        self.client.force_login(self.stranger)
        response = self.client.get(
            self.action_path("publish"), {"table": "t_owner_rule"}
        )
        self.assertEqual(response.status_code, 404)


class PublishTests(ActionTestCase):
    def test_publish_writes_topic_and_status_and_says_so(self):
        table = self.draft("t_go", title="Go")
        response = self.run_action("publish", "t_go", topic="climate", embargo="none")
        self.assertEqual(response.status_code, 204)
        table.refresh_from_db()
        self.assertTrue(table.is_publish)
        self.assertEqual(list(table.topics.values_list("name", flat=True)), ["climate"])
        self.assertFalse(Embargo.objects.filter(table=table).exists())
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(detail["message"], "Published “Go” under climate.")
        self.assertEqual(detail["focus"], f"menu-{table.pk}")

    def test_an_embargo_is_written_and_named(self):
        table = self.draft("t_embargo")
        response = self.run_action(
            "publish", "t_embargo", topic="grid", embargo="6_months"
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Embargo.objects.get(table=table).duration, "6_months")
        self.assertIn(
            "embargoed for 6 months",
            self.trigger(response, "tables-changed")["message"],
        )

    def test_unusable_parameters_are_refused_beside_the_field(self):
        Topic.objects.get_or_create(name=PSEUDO_TOPIC_DRAFT)
        self.draft("t_params")
        for params, field in (
            ({"topic": PSEUDO_TOPIC_DRAFT}, "topic"),
            ({}, "topic"),
            ({"topic": "no_such_topic"}, "topic"),
            ({"topic": "climate", "embargo": "forever"}, "embargo"),
        ):
            with self.subTest(params=params):
                response = self.run_action("publish", "t_params", **params)
                self.assertEqual(response.status_code, 400)
                self.assertTemplateUsed(response, DIALOG)
                self.assertIn(field, response.context["errors"])
                self.assertNotIn("HX-Trigger", response)
                self.assertEqual(self.published("t_params"), {"t_params": False})

    def test_a_table_no_longer_allowed_refuses_the_whole_request(self):
        self.draft("t_fine")
        demoted = self.draft("t_demoted")
        UserPermission.objects.filter(table=demoted).update(level=WRITE_PERM)
        response = self.run_action(
            "publish", "t_fine", "t_demoted", topic="climate", embargo="none"
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.published("t_fine", "t_demoted"),
            {"t_fine": False, "t_demoted": False},
        )
        message = self.trigger(response, "tables-refused")["message"]
        self.assertTrue(message.startswith("Nothing was changed:"), message)
        self.assertIn("t_demoted", message)
        # the dialog stays, with the check run again
        self.assertEqual(response.context["notice"], message)
        self.assertEqual(response.context["preflight"].names, ["t_fine"])

    def test_already_published_or_failing_the_gate_is_refused(self):
        self.draft("t_was_published", published=True)
        self.draft("t_lost_license", oemetadata=NO_LICENSE)
        for name in ("t_was_published", "t_lost_license"):
            with self.subTest(name=name):
                response = self.run_action("publish", name, topic="climate")
                self.assertEqual(response.status_code, 409)
        self.assertEqual(self.published("t_lost_license"), {"t_lost_license": False})

    def test_a_stored_pass_is_not_trusted_by_publishing(self):
        """The preflight takes a stored pass at its word; publishing does not,
        so a flag gone stale refuses the request and writes nothing."""
        self.draft("t_stale_pass", oemetadata=NO_LICENSE, publishable=True)
        self.draft("t_fine_too", publishable=True)
        self.assertEqual(
            self.check("publish", "t_stale_pass", "t_fine_too").names,
            ["t_stale_pass", "t_fine_too"],
        )
        response = self.run_action(
            "publish", "t_stale_pass", "t_fine_too", topic="climate"
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.published("t_stale_pass", "t_fine_too"),
            {"t_stale_pass": False, "t_fine_too": False},
        )
        message = self.trigger(response, "tables-refused")["message"]
        self.assertIn("t_stale_pass", message)
        self.assertNotIn("t_fine_too", message)

    def test_a_stored_fail_is_checked_again_live(self):
        """Live wins, as in the Publishable cell: a Table whose metadata was
        fixed past the write path is not kept out by its stale flag."""
        self.draft("t_stale_fail", publishable=False)
        self.assertEqual(self.check("publish", "t_stale_fail").names, ["t_stale_fail"])

    def test_a_row_action_is_a_batch_of_one_and_a_batch_is_all_or_nothing(self):
        self.draft("t_first")
        self.draft("t_second")
        real = table_actions.move_publish

        def fail_on_second(table, topic, embargo):
            if table.name == "t_second":
                raise APIError("the database went away")
            real(table, topic, embargo)

        with mock.patch.object(table_actions, "move_publish", fail_on_second):
            response = self.run_action(
                "publish", "t_first", "t_second", topic="climate"
            )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.published("t_first", "t_second"),
            {"t_first": False, "t_second": False},
        )
        self.assertFalse(Table.objects.get(name="t_first").topics.exists())

    def test_a_batch_publishes_every_table(self):
        self.draft("t_a")
        self.draft("t_b")
        response = self.run_action("publish", "t_a", "t_b", topic="supply")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.published("t_a", "t_b"), {"t_a": True, "t_b": True})
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(detail["message"], "Published 2 tables under supply.")
        self.assertNotIn("focus", detail)

    def test_a_table_the_filter_no_longer_shows_is_named(self):
        self.draft("t_leaves", title="Leaves")
        response = self.run_action(
            "publish", "t_leaves", current="?status=draft", topic="climate"
        )
        self.assertIn(
            "It is not shown under the current filter.",
            self.trigger(response, "tables-changed")["message"],
        )

    def test_a_table_still_shown_is_not_named(self):
        self.draft("t_stays")
        response = self.run_action("publish", "t_stays", current="", topic="climate")
        self.assertNotIn(
            "not shown", self.trigger(response, "tables-changed")["message"]
        )


class UnpublishTests(ActionTestCase):
    def test_unpublish_keeps_the_topics(self):
        table = self.draft("t_back", title="Back", published=True)
        table.topics.add(Topic.objects.get(name="climate"))
        response = self.run_action("unpublish", "t_back")
        self.assertEqual(response.status_code, 204)
        table.refresh_from_db()
        self.assertFalse(table.is_publish)
        self.assertEqual(list(table.topics.values_list("name", flat=True)), ["climate"])
        self.assertEqual(
            self.trigger(response, "tables-changed")["message"],
            "Unpublished “Back”. No longer listed under its topics.",
        )

    def test_a_draft_is_refused(self):
        self.draft("t_never_published")
        response = self.run_action("unpublish", "t_never_published")
        self.assertEqual(response.status_code, 409)


class ActionLogTests(ActionTestCase):
    def test_one_line_per_table_once_the_change_has_committed(self):
        self.draft("t_log_a")
        self.draft("t_log_b")
        with self.assertLogs("oeplatform.table_actions", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                self.run_action(
                    "publish", "t_log_a", "t_log_b", topic="climate", embargo="1_year"
                )
        self.assertEqual(len(logs.records), 2)
        lines = [record.getMessage() for record in logs.records]
        batches = {line.split("batch=")[1].split()[0] for line in lines}
        self.assertEqual(len(batches), 1)
        self.assertNotIn("-", batches)
        self.assertEqual(
            lines[0],
            f"table_action table=t_log_a action=publish by={self.user.pk} "
            f"via=dashboard batch={batches.pop()} topic=climate embargo=1_year",
        )

    def test_a_single_table_has_no_batch(self):
        self.draft("t_log_single", published=True)
        with self.assertLogs("oeplatform.table_actions", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                self.run_action("unpublish", "t_log_single")
        self.assertEqual(
            [record.getMessage() for record in logs.records],
            [
                f"table_action table=t_log_single action=unpublish "
                f"by={self.user.pk} via=dashboard batch=-"
            ],
        )

    def test_a_refused_request_logs_nothing(self):
        self.draft("t_log_refused", level=WRITE_PERM)
        with self.assertNoLogs("oeplatform.table_actions", "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                self.run_action("publish", "t_log_refused", topic="climate")


class ListRefreshTests(ActionTestCase):
    def test_the_region_re_fetches_itself_on_tables_changed(self):
        self.draft("t_region")
        query = {"status": "draft", "sort": "-table"}
        html = self.get(query, htmx=True).content.decode()
        region = element_with_id(html, "tables-results")
        self.assertIn('hx-trigger="tables-changed from:body"', region)
        self.assertIn(f'hx-get="{self.path}?status=draft&amp;sort=-table"', region)

    def test_the_re_fetch_replaces_the_history_entry(self):
        self.draft("t_replace")
        response = self.get(
            {"status": "draft"}, htmx=True, HTTP_HX_TRIGGER="tables-results"
        )
        self.assertEqual(response["HX-Replace-Url"], f"{self.path}?status=draft")
        self.assertNotIn("HX-Push-Url", response)

    def test_a_filter_change_still_pushes(self):
        self.draft("t_push")
        response = self.get({"status": "draft"}, htmx=True, HTTP_HX_TRIGGER="seg-draft")
        self.assertEqual(response["HX-Push-Url"], f"{self.path}?status=draft")
        self.assertNotIn("HX-Replace-Url", response)

    def test_after_publishing_the_re_fetch_shows_the_new_state(self):
        self.draft("t_refetched")
        self.run_action("publish", "t_refetched", topic="climate")
        page = self.page(
            {"status": "draft"}, htmx=True, HTTP_HX_TRIGGER="tables-results"
        )
        self.assertEqual(page.rows, [])
        self.assertEqual(page.counts["published"], 1)
