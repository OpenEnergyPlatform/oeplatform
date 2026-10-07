"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The datasets tab's row action pipeline (#2623, spec #2613): the ⋯ menu, the
action dialog's preflight, publish, unpublish and delete through the Dataset
action service with ``via="dashboard"``, and the list's re-fetch afterwards,
as seen through HTTP.

Assertions are on what the user is offered and told, what the database holds
afterwards, which response headers came back and which log lines were
written; never on markup details or seconds.
"""  # noqa: 501

import json
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from api.services import dataset_actions
from dataedit.models import Dataset, Table
from login.tests.helpers import HTMX
from login.tests.test_datasets_tab import REGION, DatasetsTabTestCase
from login.tests.test_profile_owner_rule import without_csrf
from modelview.tests.html import element_markup, text

DIALOG = "login/partials/dataset_action_dialog.html"
LONG_AGO = timezone.now() - timedelta(days=400)


class DatasetActionTestCase(DatasetsTabTestCase):
    def ready(self, name, published=None, **extra):
        """A Dataset of the user's that passes the publish gate: one member,
        one Topic. ``modified`` is long ago, so a stamp would show."""
        extra.setdefault("tables", [self.table(f"{name}_t")])
        extra.setdefault("topics", ["energy"])
        extra.setdefault("modified", LONG_AGO)
        return self.dataset(name, published=published, **extra)

    def action_path(self, action):
        return reverse("login:dataset-action", args=[self.user.pk, action])

    def preflight(self, action, *names, status=200):
        response = self.client.get(
            self.action_path(action), {"dataset": list(names)}, **HTMX
        )
        self.assertEqual(response.status_code, status)
        if status == 200:
            self.assertTemplateUsed(response, DIALOG)
        return response

    def post(self, action, data, current=None):
        headers = dict(HTMX)
        if current is not None:
            headers["HTTP_HX_CURRENT_URL"] = f"http://testserver{self.path}{current}"
        return self.client.post(self.action_path(action), data, **headers)

    def act(self, action, name, current=None, **params):
        """POST ``action`` on the one Dataset ``name``, its after-commit
        work run, and return the response with the log lines written."""
        with self.assertLogs("oeplatform.dataset_actions", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.post(action, {"datasets": name, **params}, current)
        return response, logs.output

    def refused(self, action, name, **params):
        """POST ``action`` on ``name`` expecting nothing to be written: no
        log line at all."""
        with self.assertNoLogs("oeplatform.dataset_actions", "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                return self.post(action, {"datasets": name, **params})

    def changed(self, response):
        self.assertEqual(response.status_code, 204)
        return json.loads(response["HX-Trigger"])["datasets-changed"]

    def body(self, response, element_id):
        return text(element_markup(response.content.decode(), element_id))

    def published_at(self, dataset):
        dataset.refresh_from_db()
        return dataset.published_at


class MenuTests(DatasetActionTestCase):
    def menu(self, dataset):
        body = self.get().content.decode()
        return element_markup(body, f"row-{dataset.pk}")

    def test_a_draft_offers_publish_then_delete_last_in_red(self):
        dataset = self.dataset("ds_menu_draft")
        row = self.menu(dataset)
        self.assertIn(f'id="menu-{dataset.pk}"', row)
        self.assertIn(f'aria-label="Actions for {dataset.metadata["title"]}"', row)
        self.assertIn("Publish…", row)
        self.assertNotIn("Unpublish", row)
        self.assertLess(row.index("Publish…"), row.index("Delete…"))
        self.assertIn(
            "dash-menu__danger", element_markup(row, f"menu-{dataset.pk}-delete")
        )

    def test_a_published_dataset_offers_unpublish(self):
        dataset = self.ready("ds_menu_published", published=timezone.now())
        row = self.menu(dataset)
        self.assertIn("Unpublish…", row)
        self.assertNotIn("Publish…", row.replace("Unpublish…", ""))

    def test_every_entry_is_enabled_and_loads_the_dialog_for_this_row(self):
        dataset = self.dataset("ds_menu_enabled")
        row = self.menu(dataset)
        self.assertNotIn('aria-disabled="true"', row)
        for action in ("publish", "delete"):
            entry = element_markup(row, f"menu-{dataset.pk}-{action}")
            self.assertIn(
                f'hx-get="{self.action_path(action)}?dataset=ds_menu_enabled"', entry
            )
            self.assertIn('hx-target="#dataset-action-body"', entry)
            self.assertIn(f'data-action-origin="menu-{dataset.pk}"', entry)

    def test_no_selection_yet(self):
        self.dataset("ds_menu_no_selection")
        body = self.get().content.decode()
        self.assertNotIn("data-select-row", body)
        self.assertNotIn('id="datasets-bulk"', body)


class OfferedActionsTests(DatasetActionTestCase):
    def test_the_service_offers_what_the_action_view_asks_of_it(self):
        for name in (
            "ACTIONS",
            "preflight",
            "execute",
            "choice",
            "InvalidParameters",
            "ActionRefused",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(dataset_actions, name))

    def test_only_publish_unpublish_and_delete_are_served_here(self):
        dataset = self.dataset("ds_offered")
        for action in ("create", "edit", "members_add", "members_remove", "nope"):
            with self.subTest(action=action):
                get = self.client.get(
                    self.action_path(action), {"dataset": dataset.name}, **HTMX
                )
                post = self.client.post(
                    self.action_path(action),
                    {"datasets": dataset.name, "title": "Hijacked"},
                    **HTMX,
                )
                self.assertEqual(get.status_code, 404)
                self.assertEqual(post.status_code, 404)
        dataset.refresh_from_db()
        self.assertEqual(dataset.metadata["title"], "ds_offered")


class PublishTests(DatasetActionTestCase):
    def test_the_dialog_says_where_it_will_be_listed(self):
        self.ready("ds_pub_dialog", topics=["energy", "climate"])
        response = self.preflight("publish", "ds_pub_dialog")
        listed = self.body(response, "dataset-action-listed")
        self.assertIn("listed publicly under Climate, Energy", listed)
        self.assertIn('id="dataset-action-confirm"', response.content.decode())

    def test_the_member_mix_is_information_and_the_draft_publishes(self):
        members = [
            self.table("t_mix_published"),
            self.table("t_mix_draft", published=False),
            self.table("t_mix_embargoed", embargoed=True),
        ]
        dataset = self.ready("ds_pub_mix", tables=members)
        mix = self.body(self.preflight("publish", "ds_pub_mix"), "dataset-action-mix")
        self.assertIn("It holds 3 tables.", mix)
        self.assertIn("1 is a draft and 1 is under embargo", mix)
        self.assertIn("This does not stop the publish.", mix)

        response, logs = self.act("publish", "ds_pub_mix")

        detail = self.changed(response)
        self.assertIsNotNone(self.published_at(dataset))
        self.assertEqual(detail["focus"], f"menu-{dataset.pk}")
        self.assertIn("Published “ds_pub_mix”.", detail["message"])
        self.assertEqual(
            logs,
            [
                "INFO:oeplatform.dataset_actions:dataset_action dataset=ds_pub_mix"
                f" action=publish republish=no by={self.user.pk} via=dashboard"
                " batch=-"
            ],
        )

    def test_publishing_leaves_modified_alone(self):
        dataset = self.ready("ds_pub_modified")
        self.act("publish", "ds_pub_modified")
        dataset.refresh_from_db()
        self.assertEqual(dataset.modified_at, LONG_AGO)

    def test_a_draft_failing_the_gate_is_told_what_it_needs_and_cannot_confirm(self):
        self.dataset("ds_pub_bare")
        response = self.preflight("publish", "ds_pub_bare")
        body = response.content.decode()
        gate = self.body(response, "dataset-action-gate")
        self.assertIn("cannot be published yet", gate)
        self.assertIn("Add at least one table", gate)
        self.assertIn("Choose at least one topic", gate)
        self.assertNotIn('id="dataset-action-confirm"', body)

    def test_only_the_missing_part_is_named(self):
        self.dataset("ds_pub_no_topic", tables=[self.table("t_no_topic")])
        gate = self.body(
            self.preflight("publish", "ds_pub_no_topic"), "dataset-action-gate"
        )
        self.assertIn("Choose at least one topic", gate)
        self.assertNotIn("Add at least one table", gate)

    def test_a_post_anyway_is_refused_and_writes_nothing(self):
        dataset = self.dataset("ds_pub_forced", topics=["energy"])
        response = self.refused("publish", "ds_pub_forced")
        self.assertEqual(response.status_code, 409)
        self.assertTemplateUsed(response, DIALOG)
        refused = json.loads(response["HX-Trigger"])["datasets-refused"]
        self.assertTrue(refused["message"].startswith("Nothing was changed"))
        self.assertIn("No member tables", refused["message"])
        # the dialog keeps saying so, the check run again
        self.assertIn(
            "Nothing was changed", self.body(response, "dataset-action-notice")
        )
        self.assertIn(
            "Add at least one table", self.body(response, "dataset-action-gate")
        )
        self.assertIsNone(self.published_at(dataset))

    def test_no_republish_from_the_dashboard(self):
        when = timezone.now() - timedelta(days=3)
        dataset = self.ready("ds_pub_again", published=when)
        response = self.preflight("publish", "ds_pub_again")
        self.assertIn(
            "published already", self.body(response, "dataset-action-nothing")
        )
        self.assertNotIn('id="dataset-action-confirm"', response.content.decode())

        with self.assertNoLogs("oeplatform.dataset_actions", "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.post("publish", {"datasets": "ds_pub_again"})
        detail = self.changed(response)
        self.assertIn("published already", detail["message"])
        self.assertEqual(self.published_at(dataset), when)

    def test_a_row_the_filter_no_longer_shows_is_named(self):
        self.ready("ds_pub_hidden")
        response, _ = self.act("publish", "ds_pub_hidden", current="?status=draft")
        detail = self.changed(response)
        self.assertIn("It is not shown under the current filter.", detail["message"])

    def test_a_row_still_shown_says_nothing_about_the_filter(self):
        self.ready("ds_pub_shown")
        response, _ = self.act("publish", "ds_pub_shown", current="")
        self.assertNotIn("filter", self.changed(response)["message"])


class UnpublishTests(DatasetActionTestCase):
    def test_the_dialog_says_what_happens_and_what_stays(self):
        self.ready("ds_unpub_dialog", published=timezone.now())
        response = self.preflight("unpublish", "ds_unpub_dialog")
        said = self.body(response, "dataset-action-consequences")
        self.assertIn("leaves the public catalogue", said)
        self.assertIn("(404)", said)
        self.assertIn("can no longer tell whether the link is still alive", said)
        self.assertIn("stay as they are", self.body(response, "dataset-action-stays"))
        body = response.content.decode()
        self.assertIn('id="dataset-action-confirm"', body)
        # a plain confirmation
        self.assertNotIn('name="confirm"', body)

    def test_unpublish_clears_published_at_and_leaves_modified_alone(self):
        dataset = self.ready("ds_unpub", published=timezone.now())
        response, logs = self.act("unpublish", "ds_unpub")
        detail = self.changed(response)
        dataset.refresh_from_db()
        self.assertIsNone(dataset.published_at)
        self.assertEqual(dataset.modified_at, LONG_AGO)
        self.assertIn("Unpublished “ds_unpub”.", detail["message"])
        self.assertEqual(detail["focus"], f"menu-{dataset.pk}")
        self.assertEqual(
            logs,
            [
                "INFO:oeplatform.dataset_actions:dataset_action dataset=ds_unpub"
                f" action=unpublish by={self.user.pk} via=dashboard batch=-"
            ],
        )


class DeleteTests(DatasetActionTestCase):
    def test_a_draft_is_deleted_with_a_plain_confirmation_and_its_members_stay(self):
        member = self.table("t_del_member")
        dataset = self.dataset("ds_del_draft", tables=[member])
        response = self.preflight("delete", "ds_del_draft")
        members = self.body(response, "dataset-action-members")
        self.assertIn("The 1 member table is not deleted", members)
        body = response.content.decode()
        self.assertNotIn('name="confirm"', body)
        self.assertNotIn('id="dataset-action-published"', body)

        response, logs = self.act("delete", "ds_del_draft")

        detail = self.changed(response)
        self.assertFalse(Dataset.objects.filter(pk=dataset.pk).exists())
        self.assertTrue(Table.objects.filter(pk=member.pk).exists())
        self.assertEqual(detail["gone"], ["ds_del_draft"])
        self.assertNotIn("focus", detail)
        self.assertIn("Deleted “ds_del_draft”.", detail["message"])
        self.assertIn("member tables were kept", detail["message"])
        self.assertEqual(
            logs,
            [
                "INFO:oeplatform.dataset_actions:dataset_action dataset=ds_del_draft"
                f" action=delete published=no members=1 by={self.user.pk}"
                " via=dashboard batch=-"
            ],
        )

    def test_a_published_dataset_says_what_breaks_and_asks_for_its_name(self):
        self.ready("ds_del_pub", published=timezone.now())
        response = self.preflight("delete", "ds_del_pub")
        published = self.body(response, "dataset-action-published")
        self.assertIn("leaves the public catalogue", published)
        self.assertIn("(404)", published)
        self.assertIn("read the link as deleted", published)
        self.assertIn('name="confirm"', response.content.decode())
        self.assertIn("ds_del_pub", self.body(response, "dataset-action-form"))

    def test_without_the_typed_name_the_server_refuses_under_the_lock(self):
        member = self.table("t_del_pub_member")
        dataset = self.ready("ds_del_typed", published=timezone.now(), tables=[member])
        for confirm in ("", "ds_del_wrong"):
            with self.subTest(confirm=confirm):
                response = self.refused("delete", "ds_del_typed", confirm=confirm)
                self.assertEqual(response.status_code, 400)
                self.assertIn(
                    "ds_del_typed, to confirm",
                    self.body(response, "dataset-action-confirm-error"),
                )
                self.assertTrue(Dataset.objects.filter(pk=dataset.pk).exists())

        response, logs = self.act("delete", "ds_del_typed", confirm="ds_del_typed")

        self.assertEqual(self.changed(response)["gone"], ["ds_del_typed"])
        self.assertFalse(Dataset.objects.filter(pk=dataset.pk).exists())
        self.assertTrue(Table.objects.filter(pk=member.pk).exists())
        self.assertIn("published=yes members=1", logs[0])


class NotTheUsersOwnTests(DatasetActionTestCase):
    """The dashboard knows only the user's own Datasets: anything else is
    the same 404, and nothing is written."""

    def setUp(self):
        super().setUp()
        self.foreign_draft = self.ready("ds_foreign_draft", creator=self.stranger)
        self.foreign_published = self.ready(
            "ds_foreign_published", creator=self.stranger, published=timezone.now()
        )
        self.names = ("ds_foreign_draft", "ds_foreign_published", "ds_nobody_has")

    def test_a_preflight_answers_404_alike(self):
        for action in ("publish", "unpublish", "delete"):
            bodies = set()
            for name in self.names:
                with self.subTest(action=action, name=name):
                    response = self.preflight(action, name, status=404)
                    bodies.add(without_csrf(response))
            self.assertEqual(len(bodies), 1)

    def test_a_post_answers_404_alike_and_writes_nothing(self):
        for action in ("publish", "unpublish", "delete"):
            bodies = set()
            for name in self.names:
                with self.subTest(action=action, name=name):
                    response = self.refused(action, name, confirm=name)
                    self.assertEqual(response.status_code, 404)
                    self.assertNotIn("HX-Trigger", response)
                    bodies.add(without_csrf(response))
            self.assertEqual(len(bodies), 1)
        self.assertIsNone(self.published_at(self.foreign_draft))
        self.assertIsNotNone(self.published_at(self.foreign_published))
        self.assertEqual(Dataset.objects.filter(creator=self.stranger).count(), 2)

    def test_one_foreign_name_beside_an_own_one_is_404_too(self):
        own = self.dataset("ds_own_beside")
        response = self.refused("delete", f"ds_own_beside,{self.foreign_draft.name}")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Dataset.objects.filter(pk=own.pk).exists())


class AfterActionTests(DatasetActionTestCase):
    def test_the_region_refetch_replaces_the_history_entry(self):
        self.dataset("ds_refetch")
        response = self.get(htmx=True, HTTP_HX_TRIGGER="datasets-results")
        self.assertTemplateUsed(response, REGION)
        self.assertIn("HX-Replace-Url", response)
        self.assertNotIn("HX-Push-Url", response)

    def test_the_region_listens_for_the_changed_event(self):
        self.dataset("ds_listens")
        body = self.get(htmx=True).content.decode()
        self.assertIn('hx-trigger="datasets-changed from:body"', body)

    def test_deleting_the_last_dataset_shows_the_empty_state_and_drops_the_bar(self):
        self.dataset("ds_last")
        self.assertIn('id="datasets-filters"', self.get().content.decode())

        self.act("delete", "ds_last")

        region = self.get(htmx=True, HTTP_HX_TRIGGER="datasets-results")
        body = region.content.decode()
        self.assertIn("You have no datasets yet", body)
        # the bar outside the region goes out of band; there is no bulk slot
        self.assertIn('<div id="datasets-filters" hx-swap-oob="delete"></div>', body)
        self.assertNotIn("datasets-bulk", body)
        # a fresh page of the empty account has neither, and no stray marker
        page = self.get().content.decode()
        self.assertNotIn("datasets-filters", page)
        self.assertNotIn("hx-swap-oob", page)

    def test_a_region_with_datasets_left_removes_nothing(self):
        self.dataset("ds_left_a")
        self.dataset("ds_left_b")
        self.act("delete", "ds_left_a")
        body = self.get(htmx=True, HTTP_HX_TRIGGER="datasets-results").content.decode()
        self.assertNotIn("hx-swap-oob", body)


class EmptiedListTests(DatasetActionTestCase):
    """The out-of-band removal is the shared region's, so the tables tab,
    which has a bulk slot, loses both when it has nothing left to list."""

    def test_the_tables_tab_drops_its_bar_and_its_bulk_slot(self):
        path = reverse("login:tables", kwargs={"user_id": self.user.pk})
        body = self.client.get(path, **HTMX).content.decode()
        self.assertIn('<div id="tables-filters" hx-swap-oob="delete"></div>', body)
        self.assertIn('<div id="tables-bulk" hx-swap-oob="delete"></div>', body)
        self.assertNotIn("hx-swap-oob", self.client.get(path).content.decode())
