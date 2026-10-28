"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Create and Edit on the datasets tab (#2624, spec #2613): one dialog through
the Dataset action service's ``create`` and ``edit`` with ``via="dashboard"``,
the live name preview, the gate dialog's "Edit…", and the first Create in an
empty account bringing in the filter bar, as seen through HTTP.

Assertions are on what the user is offered and told, what the database holds
afterwards, which response headers came back and which log lines were
written; never on markup details or seconds.
"""  # noqa: 501

import json
import re

from django.urls import reverse

from dataedit.models import Dataset, Table, Topic
from login.models import UserPermission
from login.permissions import ADMIN_PERM
from login.tests.helpers import HTMX
from login.tests.test_dataset_actions import LONG_AGO, DatasetActionTestCase
from login.tests.test_profile_owner_rule import without_csrf
from modelview.tests.html import element_markup, element_with_id, text
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

FORM = "login/partials/dataset_form_dialog.html"
PREVIEW = "login/partials/dataset_name_preview.html"


class FormTestCase(DatasetActionTestCase):
    def setUp(self):
        super().setUp()
        for name in ("energy", "climate", PSEUDO_TOPIC_DRAFT):
            Topic.objects.get_or_create(name=name)

    def form(self, action, name=None, status=200):
        query = {"dataset": name} if name else {}
        response = self.client.get(self.action_path(action), query, **HTMX)
        self.assertEqual(response.status_code, status)
        if status == 200:
            self.assertTemplateUsed(response, FORM)
        return response

    def create(self, title, description="What it is", topics=(), current=None, **extra):
        """POST the Create form, from the list at ``current`` (a query) if
        given; the response and the log lines written."""
        data = {"title": title, "description": description, "topics": list(topics)}
        with self.assertLogs("oeplatform.dataset_actions", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.post("create", {**data, **extra}, current)
        return response, logs.output

    def refused_form(self, action, data):
        """POST the form expecting a 400 and nothing written."""
        with self.assertNoLogs("oeplatform.dataset_actions", "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.post(action, data)
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, FORM)
        self.assertNotIn("HX-Trigger", response)
        return response

    def preview(self, title):
        path = reverse("login:dataset-name-preview", args=[self.user.pk])
        response = self.client.get(path, {"title": title}, **HTMX)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, PREVIEW)
        return response

    def submit_enabled(self, response):
        button = element_with_id(response.content.decode(), "dataset-form-submit")
        self.assertTrue(button, "no submit button")
        return "disabled" not in button

    def field(self, response, element_id):
        return element_with_id(response.content.decode(), element_id)

    def ticked(self, response):
        """The Topics the form shows ticked."""
        body = response.content.decode()
        return sorted(re.findall(r'<input[^>]*value="([^"]+)"[^>]*\bchecked\b', body))


class EntryPointTests(FormTestCase):
    def test_new_dataset_sits_at_the_end_of_the_filter_row(self):
        self.dataset("ds_entry")
        body = self.get().content.decode()
        button = element_markup(body, "datasets-new")
        self.assertIn("New dataset", text(button))
        self.assertIn(f'hx-get="{self.action_path("create")}"', button)
        self.assertIn('hx-target="#dataset-action-body"', button)
        self.assertIn('data-action-origin="datasets-new"', button)
        self.assertIn(button, element_markup(body, "datasets-filters"))

    def test_an_empty_account_is_offered_create_a_dataset(self):
        body = self.get().content.decode()
        button = element_markup(body, "datasets-create")
        self.assertIn("Create a dataset", text(button))
        self.assertIn(f'hx-get="{self.action_path("create")}"', button)
        self.assertIn('data-action-origin="datasets-create"', button)

    def test_the_tables_tab_offers_no_create(self):
        path = reverse("login:tables", kwargs={"user_id": self.user.pk})
        self.assertNotIn("tables-new", self.client.get(path).content.decode())


class CreateTests(FormTestCase):
    def test_the_dialog_opens_empty_with_create_disabled(self):
        response = self.form("create")
        self.assertIn("New dataset", self.body(response, "dataset-action-title"))
        self.assertIn(
            "The web address is made from the title.",
            self.body(response, "dataset-form-name"),
        )
        self.assertFalse(self.submit_enabled(response))
        topics = self.body(response, "dataset-form-topics")
        self.assertIn("at least one is needed to publish", topics)
        self.assertIn("climate", topics)
        self.assertIn("energy", topics)
        # the pseudo-topic marks draft tables and is never offered
        self.assertNotIn(f'value="{PSEUDO_TOPIC_DRAFT}"', response.content.decode())
        self.assertEqual(self.ticked(response), [])
        self.assertIn(
            f'hx-get="{reverse("login:dataset-name-preview", args=[self.user.pk])}"',
            self.field(response, "dataset-form-title"),
        )

    def test_create_makes_a_draft_and_says_which_one(self):
        response, logs = self.create(
            "Wind Power Germany", "Turbines", topics=["energy", "climate"]
        )

        detail = self.changed(response)
        dataset = Dataset.objects.get(name="wind_power_germany")
        self.assertEqual(dataset.creator, self.user)
        self.assertIsNone(dataset.published_at)
        self.assertEqual(dataset.modified_at, dataset.created_at)
        self.assertEqual(dataset.metadata["title"], "Wind Power Germany")
        self.assertEqual(dataset.metadata["description"], "Turbines")
        self.assertEqual(
            sorted(dataset.topics.values_list("name", flat=True)),
            ["climate", "energy"],
        )
        # the members drawer's contract (#2625): it opens on this name
        self.assertEqual(detail["created"], "wind_power_germany")
        self.assertEqual(detail["focus"], f"menu-{dataset.pk}")
        self.assertIn("Created “Wind Power Germany”", detail["message"])
        self.assertEqual(
            logs,
            [
                "INFO:oeplatform.dataset_actions:dataset_action"
                " dataset=wind_power_germany action=create"
                f" by={self.user.pk} via=dashboard batch=-"
            ],
        )

    def test_topics_are_optional(self):
        response, _ = self.create("No topics yet")
        self.changed(response)
        dataset = Dataset.objects.get(name="no_topics_yet")
        self.assertFalse(dataset.topics.exists())

    def test_the_new_draft_lands_on_top(self):
        self.dataset("ds_older_a", modified=LONG_AGO)
        self.dataset("ds_older_b", modified=LONG_AGO)
        self.create("Brand new")
        self.assertEqual(self.names()[0], "brand_new")

    def test_a_new_draft_the_filter_hides_is_named(self):
        self.dataset("ds_published_only", published=LONG_AGO)
        response, _ = self.create("Hidden draft", current="?status=published")
        self.assertIn(
            "It is not shown under the current filter.",
            self.changed(response)["message"],
        )

    def test_a_name_taken_by_a_strangers_draft_is_refused_and_keeps_what_was_typed(
        self,
    ):
        self.dataset("taken_name", creator=self.stranger)
        response = self.refused_form(
            "create",
            {"title": "Taken Name", "description": "Mine", "topics": ["energy"]},
        )
        self.assertIn("taken_name", self.body(response, "dataset-form-name"))
        self.assertIn("already taken", self.body(response, "dataset-form-name"))
        self.assertIn('value="Taken Name"', self.field(response, "dataset-form-title"))
        self.assertIn(
            "Mine",
            element_markup(response.content.decode(), "dataset-form-description"),
        )
        self.assertEqual(self.ticked(response), ["energy"])
        self.assertFalse(self.submit_enabled(response))
        self.assertEqual(Dataset.objects.filter(name="taken_name").count(), 1)

    def test_an_unknown_topic_and_the_draft_pseudo_topic_are_refused_by_name(self):
        response = self.refused_form(
            "create",
            {
                "title": "Odd topics",
                "description": "Mine",
                "topics": ["energy", "no_such_topic", PSEUDO_TOPIC_DRAFT],
            },
        )
        error = self.body(response, "dataset-form-topics-error")
        self.assertIn("“no_such_topic”", error)
        self.assertIn(f"“{PSEUDO_TOPIC_DRAFT}”", error)
        self.assertIn('value="Odd topics"', self.field(response, "dataset-form-title"))
        self.assertEqual(self.ticked(response), ["energy"])
        self.assertFalse(Dataset.objects.filter(name="odd_topics").exists())

    def test_a_title_without_a_letter_or_number_is_refused(self):
        response = self.refused_form("create", {"title": "!!!", "description": "x"})
        self.assertIn(
            "needs a letter or number", self.body(response, "dataset-form-name")
        )
        self.assertFalse(Dataset.objects.exists())

    def test_title_and_description_are_required(self):
        response = self.refused_form("create", {"title": "Fine", "description": " "})
        self.assertIn("required", self.body(response, "dataset-form-description-error"))
        response = self.refused_form("create", {"title": "", "description": "x"})
        self.assertIn("required", self.body(response, "dataset-form-title-error"))
        self.assertFalse(Dataset.objects.exists())

    def test_title_and_description_are_stored_trimmed(self):
        self.create("  Spaced out  ", "  Words  ")
        dataset = Dataset.objects.get(name="spaced_out")
        self.assertEqual(dataset.metadata["title"], "Spaced out")
        self.assertEqual(dataset.metadata["description"], "Words")

    def test_a_name_sent_beside_the_title_is_ignored(self):
        self.create("From the title", dataset="chosen_by_client")
        self.assertTrue(Dataset.objects.filter(name="from_the_title").exists())
        self.assertFalse(Dataset.objects.filter(name="chosen_by_client").exists())


class NamePreviewTests(FormTestCase):
    def test_an_available_name_shows_the_web_address(self):
        response = self.preview("Wind Power")
        said = self.body(response, "dataset-form-name-state")
        self.assertIn("Web address: …/datasets/wind_power", said)
        self.assertIn("Fixed once created.", said)
        self.assertTrue(self.submit_enabled(response))
        self.assertIn('hx-swap-oob="true"', self.field(response, "dataset-form-submit"))

    def test_a_name_taken_by_a_strangers_draft_reads_taken_and_reveals_nothing(self):
        self.dataset(
            "secret_plan",
            title="The stranger's secret title",
            creator=self.stranger,
            description="Only theirs",
        )
        own = self.preview("Secret plan")
        self.assertIn("already taken", self.body(own, "dataset-form-name-state"))
        self.assertFalse(self.submit_enabled(own))
        body = own.content.decode()
        for secret in ("secret title", "Only theirs", self.stranger.name):
            self.assertNotIn(secret, body)

        # a published one and the user's own read the same
        self.dataset("own_name")
        self.dataset("public_name", creator=self.stranger, published=LONG_AGO)
        for title in ("Own name", "Public name"):
            with self.subTest(title=title):
                response = self.preview(title)
                self.assertIn(
                    "already taken", self.body(response, "dataset-form-name-state")
                )
                self.assertFalse(self.submit_enabled(response))

    def test_a_title_without_a_letter_or_number(self):
        response = self.preview("–––")
        self.assertIn(
            "needs a letter or number", self.body(response, "dataset-form-name-state")
        )
        self.assertFalse(self.submit_enabled(response))

    def test_an_empty_title(self):
        response = self.preview("  ")
        self.assertIn(
            "The web address is made from the title.",
            self.body(response, "dataset-form-name-state"),
        )
        self.assertFalse(self.submit_enabled(response))

    def test_the_preview_is_the_servers_name_rule(self):
        response = self.preview("Ünïcode & CO₂ — 2030!")
        self.assertIn("…/datasets/n_code_co_2030", response.content.decode())


class EditTests(FormTestCase):
    def test_edit_is_the_first_entry_of_the_menu(self):
        dataset = self.dataset("ds_edit_menu")
        row = element_markup(self.get().content.decode(), f"row-{dataset.pk}")
        entries = re.findall(rf'id="menu-{dataset.pk}-(\w+)"', row)
        self.assertEqual(entries[0], "edit")
        entry = element_markup(row, f"menu-{dataset.pk}-edit")
        self.assertIn("Edit…", text(entry))
        self.assertIn(
            f'hx-get="{self.action_path("edit")}?dataset=ds_edit_menu"', entry
        )

    def test_the_dialog_shows_what_is_stored_and_the_name_fixed(self):
        self.dataset(
            "ds_edit_form",
            title="Stored title",
            description="Stored words",
            topics=["climate"],
        )
        response = self.form("edit", "ds_edit_form")
        self.assertIn(
            "Edit “Stored title”", self.body(response, "dataset-action-title")
        )
        self.assertIn(
            'value="Stored title"', self.field(response, "dataset-form-title")
        )
        self.assertIn(
            "Stored words",
            element_markup(response.content.decode(), "dataset-form-description"),
        )
        self.assertEqual(self.ticked(response), ["climate"])
        name = self.body(response, "dataset-form-name")
        self.assertIn("…/datasets/ds_edit_form", name)
        self.assertIn("fixed", name)
        # the name is not a field, and typing the title asks for no preview
        self.assertNotIn("hx-get", self.field(response, "dataset-form-title"))
        self.assertTrue(self.submit_enabled(response))

    def test_edit_changes_title_description_and_topics_but_never_the_name(self):
        dataset = self.dataset("ds_edit", title="Old", topics=["climate"])
        with self.assertLogs("oeplatform.dataset_actions", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.post(
                    "edit",
                    {
                        "dataset": "ds_edit",
                        "title": "Completely new",
                        "description": "New words",
                        "topics": ["energy"],
                        "name": "completely_new",
                    },
                )
        detail = self.changed(response)
        dataset.refresh_from_db()
        self.assertEqual(dataset.name, "ds_edit")
        self.assertEqual(dataset.metadata["title"], "Completely new")
        self.assertEqual(dataset.metadata["description"], "New words")
        self.assertEqual(
            list(dataset.topics.values_list("name", flat=True)), ["energy"]
        )
        self.assertGreater(dataset.modified_at, LONG_AGO)
        self.assertIn("Saved “Completely new”", detail["message"])
        self.assertEqual(detail["focus"], f"menu-{dataset.pk}")
        self.assertNotIn("created", detail)
        self.assertEqual(
            logs.output,
            [
                "INFO:oeplatform.dataset_actions:dataset_action dataset=ds_edit"
                " action=edit changed=title,description,topics"
                f" by={self.user.pk} via=dashboard batch=-"
            ],
        )

    def test_unticking_every_topic_clears_them(self):
        dataset = self.dataset("ds_untick", topics=["climate", "energy"])
        with self.captureOnCommitCallbacks(execute=True):
            response = self.post(
                "edit",
                {"dataset": "ds_untick", "title": "ds_untick", "description": ""},
            )
        self.assertEqual(response.status_code, 400)  # the description is required
        with self.captureOnCommitCallbacks(execute=True):
            response = self.post(
                "edit",
                {"dataset": "ds_untick", "title": "ds_untick", "description": "d"},
            )
        self.changed(response)
        self.assertFalse(dataset.topics.exists())

    def test_a_save_that_changes_nothing_writes_and_stamps_nothing(self):
        dataset = self.dataset(
            "ds_noop",
            title="Same",
            description="Same words",
            topics=["energy", "climate"],
            modified=LONG_AGO,
        )
        form = self.form("edit", "ds_noop")
        self.assertEqual(self.ticked(form), ["climate", "energy"])
        with self.assertNoLogs("oeplatform.dataset_actions", "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.post(
                    "edit",
                    {
                        "dataset": "ds_noop",
                        "title": "Same",
                        "description": "Same words",
                        "topics": ["climate", "energy"],
                    },
                )
        detail = self.changed(response)
        self.assertIn("Nothing was changed", detail["message"])
        dataset.refresh_from_db()
        self.assertEqual(dataset.modified_at, LONG_AGO)

    def test_a_refused_edit_keeps_what_was_typed_and_changes_nothing(self):
        dataset = self.dataset("ds_edit_refused", title="Kept", topics=["energy"])
        response = self.refused_form(
            "edit",
            {
                "dataset": "ds_edit_refused",
                "title": "Typed",
                "description": "Typed words",
                "topics": ["climate", "no_such_topic"],
            },
        )
        self.assertIn(
            "“no_such_topic”", self.body(response, "dataset-form-topics-error")
        )
        self.assertIn('value="Typed"', self.field(response, "dataset-form-title"))
        self.assertEqual(self.ticked(response), ["climate"])
        # the dialog still names the Dataset as it is stored
        self.assertIn("Edit “Kept”", self.body(response, "dataset-action-title"))
        dataset.refresh_from_db()
        self.assertEqual(dataset.metadata["title"], "Kept")
        self.assertEqual(
            list(dataset.topics.values_list("name", flat=True)), ["energy"]
        )

    def test_a_blank_title_is_refused(self):
        dataset = self.dataset("ds_blank", title="Kept", description="d")
        response = self.refused_form(
            "edit", {"dataset": "ds_blank", "title": "  ", "description": "d"}
        )
        self.assertIn("required", self.body(response, "dataset-form-title-error"))
        dataset.refresh_from_db()
        self.assertEqual(dataset.metadata["title"], "Kept")


class NotTheUsersOwnTests(FormTestCase):
    """Edit knows only the user's own Datasets: anything else is the same
    404, and nothing is written."""

    def test_edit_answers_404_alike_and_writes_nothing(self):
        self.dataset("ds_theirs_draft", title="Theirs", creator=self.stranger)
        self.dataset(
            "ds_theirs_published",
            title="Theirs",
            creator=self.stranger,
            published=LONG_AGO,
        )
        gets, posts = set(), set()
        for name in ("ds_theirs_draft", "ds_theirs_published", "ds_nobody"):
            with self.subTest(name=name):
                gets.add(without_csrf(self.form("edit", name, status=404)))
                with self.assertNoLogs("oeplatform.dataset_actions", "INFO"):
                    response = self.post(
                        "edit",
                        {"dataset": name, "title": "Hijacked", "description": "x"},
                    )
                self.assertEqual(response.status_code, 404)
                posts.add(without_csrf(response))
        self.assertEqual(len(gets), 1)
        self.assertEqual(len(posts), 1)
        self.assertFalse(Dataset.objects.filter(metadata__title="Hijacked").exists())

    def test_edit_without_a_dataset_is_404(self):
        self.form("edit", status=404)


class GateEditLinkTests(FormTestCase):
    def test_a_draft_without_topics_gets_edit_in_the_gate_dialog(self):
        dataset = self.dataset("ds_gate_edit", tables=[self.table("t_gate_edit")])
        gate = element_markup(
            self.preflight("publish", "ds_gate_edit").content.decode(),
            "dataset-action-gate",
        )
        link = element_markup(gate, "dataset-action-gate-edit")
        self.assertIn("Edit…", text(link))
        # close-before-open: the link waits for the dialog to close
        self.assertIn("data-close-then", link)
        self.assertIn('hx-trigger="dialog-closed"', link)
        self.assertIn(f'hx-get="{self.action_path("edit")}?dataset=ds_gate_edit"', link)
        self.assertIn('hx-target="#dataset-action-body"', link)
        self.assertIn(f'data-action-origin="menu-{dataset.pk}"', link)

    def test_a_draft_with_topics_gets_no_edit_link(self):
        self.dataset("ds_gate_topics", topics=["energy"])
        body = self.preflight("publish", "ds_gate_topics").content.decode()
        self.assertIn("Add at least one table", text(body))
        self.assertNotIn("dataset-action-gate-edit", body)


class FirstCreateTests(FormTestCase):
    """The filter bar (and a tab's bulk slot) sit outside the region and the
    empty state has neither: the region re-fetched after the first Create
    brings them in out of band."""

    def refetch(self, path, was_empty):
        headers = {**HTMX, "HTTP_HX_TRIGGER": "datasets-results"}
        if was_empty:
            headers["HTTP_X_LIST_EMPTY"] = "true"
        response = self.client.get(path, **headers)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_the_empty_region_says_so_when_it_refetches(self):
        region = element_with_id(self.get().content.decode(), "datasets-results")
        self.assertIn("hx-headers", region)
        self.assertIn("X-List-Empty", region)
        self.dataset("ds_not_empty")
        region = element_with_id(self.get().content.decode(), "datasets-results")
        self.assertNotIn("X-List-Empty", region)

    def test_the_first_create_brings_in_the_filter_bar(self):
        self.assertNotIn("datasets-filters", self.get().content.decode())
        self.create("First of all")

        body = self.refetch(self.path, was_empty=True)

        self.assertIn('hx-swap-oob="beforebegin:#datasets-live"', body)
        bar = element_markup(body, "datasets-filters")
        self.assertIn('id="datasets-search"', bar)
        self.assertIn('id="datasets-new"', bar)
        # and the list shows the new draft
        self.assertIn("First of all", text(element_markup(body, "datasets-results")))
        # the bar comes in once: a page that has it already gets nothing
        self.assertNotIn("hx-swap-oob", self.refetch(self.path, was_empty=False))

    def test_a_tab_with_bulk_actions_gets_its_bulk_slot_too(self):
        path = reverse("login:tables", kwargs={"user_id": self.user.pk})
        table = Table.objects.create(name="t_first_create")
        UserPermission.objects.create(holder=self.user, table=table, level=ADMIN_PERM)
        body = self.client.get(
            path, HTTP_X_LIST_EMPTY="true", HTTP_HX_TRIGGER="tables-results", **HTMX
        ).content.decode()
        oob = body[body.index('hx-swap-oob="beforebegin:#tables-live"') :]
        self.assertIn('id="tables-filters"', oob)
        self.assertIn('id="tables-bulk"', oob)
        self.assertNotIn("tables-new", body)

    def test_the_changed_event_detail_round_trips_as_json(self):
        response, _ = self.create("Json safe “quotes”")
        detail = json.loads(response["HX-Trigger"])["datasets-changed"]
        self.assertEqual(detail["created"], "json_safe_quotes")
