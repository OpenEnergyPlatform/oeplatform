"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Adding a Table to, and removing it from, one of the user's own Datasets
from its row (#2563, spec #2551), through the table action service: the ⋯
menu, the dialog's preflight, the write and its log line, as seen through
HTTP. Also the widened assignment rule as the dashboard meets it: a Data
editor through an Organization may add a draft, a platform admin with no
grant on it may not.

Assertions are on what the user is offered and told, what the database holds
afterwards, which response headers came back and which log lines were
written; never on seconds.
"""  # noqa: 501

from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest import mock

from django.utils import timezone

from api.services import table_actions
from dataedit.models import Dataset, Embargo, Topic
from login.models import WRITE_PERM, GroupPermission
from login.tests.helpers import HTMX, make_user
from login.tests.test_table_actions import ActionTestCase
from modelview.tests.html import element_with_id
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

ADD, REMOVE = table_actions.DATASET_ADD, table_actions.DATASET_REMOVE


class DatasetActionTestCase(ActionTestCase):
    def dataset(self, name, *tables, creator=None, title=None):
        dataset = Dataset.objects.create(
            name=name,
            metadata={"name": name, "title": title or ""},
            creator=creator or self.user,
        )
        dataset.tables.add(*tables)
        return dataset

    def members(self, dataset):
        return sorted(dataset.tables.values_list("name", flat=True))

    def choices(self, check):
        return [dataset.name for dataset in check.datasets]

    def chosen(self, check):
        return check.dataset.name if check.dataset else None


class DatasetMenuTests(DatasetActionTestCase):
    def html(self):
        return self.get(htmx=True).content.decode()

    def test_every_row_offers_add_to_dataset(self):
        table = self.draft("t_menu_add", level=WRITE_PERM)
        html = self.html()
        entry = element_with_id(html, f"menu-{table.pk}-{ADD}")
        self.assertIn(f'hx-get="{self.action_path(ADD)}?table=t_menu_add"', entry)
        self.assertNotIn("aria-disabled", entry)
        self.assertIn("Add to dataset…", html)

    def test_remove_is_offered_only_when_one_of_my_datasets_holds_the_table(self):
        mine = self.draft("t_in_mine")
        theirs = self.draft("t_in_theirs", published=True)
        nowhere = self.draft("t_nowhere")
        self.dataset("ds_mine", mine)
        self.dataset("ds_theirs", theirs, creator=self.stranger)
        html = self.html()
        entry = element_with_id(html, f"menu-{mine.pk}-{REMOVE}")
        self.assertIn(f'hx-get="{self.action_path(REMOVE)}?table=t_in_mine"', entry)
        self.assertEqual(html.count("Remove from dataset…"), 1)
        for table in (theirs, nowhere):
            with self.subTest(table=table.name):
                self.assertEqual(element_with_id(html, f"menu-{table.pk}-{REMOVE}"), "")

    def test_the_entries_cost_no_query(self):
        table = self.draft("t_menu_count")
        self.dataset("ds_counted", table)
        self.get(htmx=True)  # warm the Site cache, as QueryCountTests does
        with self.assertNumQueries(7):
            self.get(htmx=True)


class DatasetPreflightTests(DatasetActionTestCase):
    def test_add_offers_my_datasets_that_do_not_hold_the_table(self):
        table = self.draft("t_offer")
        self.dataset("ds_b")
        self.dataset("ds_a")
        self.dataset("ds_holds_it", table)
        self.dataset("ds_strangers", creator=self.stranger)
        check = self.check(ADD, "t_offer")
        self.assertEqual(check.names, ["t_offer"])
        self.assertEqual(self.choices(check), ["ds_a", "ds_b"])
        # two to choose from: nothing is chosen for the user
        self.assertIsNone(self.chosen(check))

    def test_remove_offers_only_my_datasets_that_hold_the_table(self):
        table = self.draft("t_held", published=True)
        self.dataset("ds_holder", table)
        self.dataset("ds_empty")
        self.dataset("ds_other_holder", table, creator=self.stranger)
        check = self.check(REMOVE, "t_held")
        self.assertEqual(self.choices(check), ["ds_holder"])
        # the only choice is chosen, so a row's remove is one confirmation
        self.assertEqual(self.chosen(check), "ds_holder")

    def test_a_dataset_is_offered_by_its_title(self):
        self.draft("t_titled")
        self.dataset("ds_titled", title="Wind atlas")
        response = self.preflight(ADD, "t_titled")
        self.assertContains(response, "Wind atlas")

    def test_a_named_dataset_leaves_out_tables_already_in_it_or_not_in_it(self):
        inside = self.draft("t_inside")
        self.draft("t_outside")
        self.dataset("ds_named", inside, title="Named")
        add = self.client.get(
            self.action_path(ADD),
            {"table": ["t_inside", "t_outside"], "dataset": "ds_named"},
            **HTMX,
        ).context["preflight"]
        self.assertEqual(add.names, ["t_outside"])
        self.assertEqual(
            [(group.reason, group.names) for group in add.left_out],
            [("Already in “Named”", ["t_inside"])],
        )
        remove = self.client.get(
            self.action_path(REMOVE),
            {"table": ["t_inside", "t_outside"], "dataset": "ds_named"},
            **HTMX,
        ).context["preflight"]
        self.assertEqual(remove.names, ["t_inside"])
        self.assertEqual(
            [(group.reason, group.names) for group in remove.left_out],
            [("Not in “Named”", ["t_outside"])],
        )

    def test_another_users_dataset_is_never_chosen(self):
        self.draft("t_not_theirs")
        self.dataset("ds_foreign", creator=self.stranger)
        check = self.client.get(
            self.action_path(ADD),
            {"table": "t_not_theirs", "dataset": "ds_foreign"},
            **HTMX,
        ).context["preflight"]
        self.assertIsNone(self.chosen(check))
        self.assertEqual(self.choices(check), [])

    def test_without_a_dataset_to_choose_nothing_can_be_confirmed(self):
        table = self.draft("t_no_choice")
        self.dataset("ds_full", table)
        for action, text in ((ADD, "Create one"), (REMOVE, "None of your datasets")):
            if action == REMOVE:
                Dataset.objects.all().delete()
            with self.subTest(action=action):
                response = self.preflight(action, "t_no_choice")
                self.assertEqual(
                    element_with_id(response.content.decode(), "table-action-confirm"),
                    "",
                )
                self.assertContains(response, text)

    def test_a_preflight_writes_nothing(self):
        self.draft("t_untouched_ds")
        dataset = self.dataset("ds_untouched")
        self.check(ADD, "t_untouched_ds")
        self.assertEqual(self.members(dataset), [])


class DatasetAddTests(DatasetActionTestCase):
    def test_add_puts_the_table_in_the_dataset_and_says_so(self):
        table = self.draft("t_add", title="Turbines")
        table.topics.add(Topic.objects.get(name="climate"))
        dataset = self.dataset("ds_add", title="Wind atlas")
        response = self.run_action(ADD, "t_add", dataset="ds_add")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.members(dataset), ["t_add"])
        # the same write as the dataset API: the Table's topics seed the Dataset
        self.assertEqual(
            list(dataset.topics.values_list("name", flat=True)), ["climate"]
        )
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(detail["message"], "Added “Turbines” to “Wind atlas”.")
        self.assertEqual(detail["focus"], f"menu-{table.pk}")

    def test_a_batch_is_added_whole(self):
        self.draft("t_add_a")
        self.draft("t_add_b")
        dataset = self.dataset("ds_batch")
        response = self.run_action(ADD, "t_add_a", "t_add_b", dataset="ds_batch")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.members(dataset), ["t_add_a", "t_add_b"])
        self.assertEqual(
            self.trigger(response, "tables-changed")["message"],
            "Added 2 tables to “ds_batch”.",
        )

    def test_a_dataset_must_be_one_of_mine(self):
        self.draft("t_params_ds")
        foreign = self.dataset("ds_strangers_own", creator=self.stranger)
        for params in ({}, {"dataset": "ds_strangers_own"}, {"dataset": "ds_nope"}):
            with self.subTest(params=params):
                response = self.run_action(ADD, "t_params_ds", **params)
                self.assertEqual(response.status_code, 400)
                self.assertIn("dataset", response.context["errors"])
                self.assertNotIn("HX-Trigger", response)
        self.assertEqual(self.members(foreign), [])

    def test_a_table_already_in_the_dataset_refuses_the_whole_request(self):
        inside = self.draft("t_already_in")
        self.draft("t_new_one")
        dataset = self.dataset("ds_race", inside)
        response = self.run_action(ADD, "t_already_in", "t_new_one", dataset="ds_race")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.members(dataset), ["t_already_in"])
        self.assertIn(
            "Already in “ds_race”", self.trigger(response, "tables-refused")["message"]
        )

    def test_a_failure_part_way_adds_nothing(self):
        self.draft("t_first_ds")
        self.draft("t_second_ds")
        dataset = self.dataset("ds_partial")
        real = table_actions.assign_table

        def fail_on_second(dataset, table):
            if table.name == "t_second_ds":
                raise RuntimeError("the database went away")
            real(dataset, table)

        self.client.raise_request_exception = False
        with self.assertLogs("django.request", "ERROR"):
            with mock.patch.object(table_actions, "assign_table", fail_on_second):
                response = self.run_action(
                    ADD, "t_first_ds", "t_second_ds", dataset="ds_partial"
                )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.members(dataset), [])


class WidenedRuleTests(DatasetActionTestCase):
    """The shared "may assign" rule as the dashboard meets it (spec: Dataset
    assignment rule, widened; WF-03 finding 6)."""

    def test_a_data_editor_through_an_organization_may_add_a_draft(self):
        organization = self.organization("Editors")
        table = self.draft("t_group_draft", level=None)
        GroupPermission.objects.create(
            holder=organization, table=table, level=WRITE_PERM
        )
        dataset = self.dataset("ds_group")
        self.assertEqual(self.check(ADD, "t_group_draft").names, ["t_group_draft"])
        response = self.run_action(ADD, "t_group_draft", dataset="ds_group")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.members(dataset), ["t_group_draft"])

    def test_a_platform_admin_without_a_grant_may_not_add_a_draft(self):
        """No platform-admin exemption: the rule reads grants only, like the
        Dataset tab's picker, so both offer the same Tables."""
        admin = make_user("DatasetRuleAdmin", is_admin=True)
        self.client.force_login(admin)
        self.user = admin
        draft = self.draft("t_admin_draft", level=None)
        embargoed = self.draft("t_admin_embargoed", level=None, published=True)
        Embargo.objects.create(
            table=embargoed,
            date_ended=timezone.now() + timedelta(days=30),
            duration="6_months",
        )
        self.draft("t_admin_published", level=None, published=True)
        dataset = self.dataset("ds_admin")
        check = self.check(ADD, draft.name, embargoed.name, "t_admin_published")
        self.assertEqual(check.names, ["t_admin_published"])
        self.assertEqual(
            {group.reason: group.names for group in check.left_out},
            {
                "Drafts and embargoed tables need Data editor on the table": [
                    "t_admin_draft",
                    "t_admin_embargoed",
                ]
            },
        )
        response = self.run_action(ADD, draft.name, dataset="ds_admin")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.members(dataset), [])


class DatasetRemoveTests(DatasetActionTestCase):
    def test_remove_takes_the_table_out_and_keeps_it(self):
        table = self.draft("t_leave", title="Leaving", published=True)
        dataset = self.dataset("ds_leave", table, title="Atlas")
        topic = Topic.objects.get(name="climate")
        dataset.topics.add(topic)
        response = self.run_action(REMOVE, "t_leave", dataset="ds_leave")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.members(dataset), [])
        self.assertTrue(table.__class__.objects.filter(name="t_leave").exists())
        # removing a member never removes a curated topic
        self.assertEqual(list(dataset.topics.all()), [topic])
        self.assertEqual(
            self.trigger(response, "tables-changed")["message"],
            "Removed “Leaving” from “Atlas”.",
        )

    def test_a_table_not_in_the_dataset_is_refused(self):
        self.draft("t_never_in")
        self.dataset("ds_without")
        response = self.run_action(REMOVE, "t_never_in", dataset="ds_without")
        self.assertEqual(response.status_code, 409)

    def test_a_table_the_dataset_filter_no_longer_shows_is_named(self):
        table = self.draft("t_filtered_out")
        self.dataset("ds_filter", table, self.draft("t_still_in"))
        response = self.run_action(
            REMOVE, "t_filtered_out", current="?dataset=ds_filter", dataset="ds_filter"
        )
        self.assertIn(
            "It is not shown under the current filter.",
            self.trigger(response, "tables-changed")["message"],
        )

    def test_removing_the_last_of_my_tables_makes_the_filter_stale(self):
        """The Dataset filter offers only Datasets holding one of the user's
        Tables (#2556), so once the last one leaves, ``?dataset=`` no longer
        applies: it is ignored and shown as a muted chip, and the Table stays
        in the list. The message must not call it hidden."""
        table = self.draft("t_last_one")
        self.dataset("ds_emptied", table)
        response = self.run_action(
            REMOVE, "t_last_one", current="?dataset=ds_emptied", dataset="ds_emptied"
        )
        self.assertNotIn(
            "not shown", self.trigger(response, "tables-changed")["message"]
        )
        page = self.page({"dataset": "ds_emptied"}, htmx=True)
        self.assertEqual([row.table.name for row in page.rows], ["t_last_one"])

    def test_a_draft_member_can_be_removed_by_its_data_editor(self):
        table = self.draft("t_draft_member", level=WRITE_PERM)
        dataset = self.dataset("ds_draft_member", table)
        response = self.run_action(REMOVE, "t_draft_member", dataset="ds_draft_member")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.members(dataset), [])


class DatasetActionLogTests(DatasetActionTestCase):
    def test_the_line_names_the_dataset(self):
        table = self.draft("t_log_ds")
        self.dataset("ds_logged")
        with self.assertLogs("oeplatform.table_actions", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                self.run_action(ADD, "t_log_ds", dataset="ds_logged")
        Dataset.objects.get(name="ds_logged").tables.add(table)
        with self.assertLogs("oeplatform.table_actions", "INFO") as removed:
            with self.captureOnCommitCallbacks(execute=True):
                self.run_action(REMOVE, "t_log_ds", dataset="ds_logged")
        prefix = f"table_action table=t_log_ds action=%s by={self.user.pk} "
        self.assertEqual(
            [record.getMessage() for record in logs.records + removed.records],
            [
                prefix % "dataset_add" + "via=dashboard batch=- dataset=ds_logged",
                prefix % "dataset_remove" + "via=dashboard batch=- dataset=ds_logged",
            ],
        )

    def test_a_refused_request_logs_nothing(self):
        self.draft("t_log_ds_refused")
        with self.assertNoLogs("oeplatform.table_actions", "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                self.run_action(ADD, "t_log_ds_refused", dataset="ds_missing")


class ModificationStampTests(DatasetActionTestCase):
    """Adding a Table to a Dataset and removing it are Modifications of the
    Dataset (#2619): its ``modified_at`` moves. A change inside a member
    Table is not one."""

    LONG_AGO = datetime(2020, 1, 1, tzinfo=dt_timezone.utc)

    def stamped(self, dataset):
        return Dataset.objects.get(pk=dataset.pk).modified_at

    def test_add_and_remove_stamp_the_dataset(self):
        self.draft("t_stamp_ds")
        dataset = self.dataset("ds_stamp")
        Dataset.objects.filter(pk=dataset.pk).update(modified_at=self.LONG_AGO)
        before = timezone.now()
        self.assertEqual(
            self.run_action(ADD, "t_stamp_ds", dataset="ds_stamp").status_code, 204
        )
        added = self.stamped(dataset)
        self.assertGreaterEqual(added, before)
        Dataset.objects.filter(pk=dataset.pk).update(modified_at=self.LONG_AGO)
        self.assertEqual(
            self.run_action(REMOVE, "t_stamp_ds", dataset="ds_stamp").status_code, 204
        )
        self.assertGreaterEqual(self.stamped(dataset), added)

    def test_a_refused_request_does_not_stamp(self):
        inside = self.draft("t_stamp_inside")
        dataset = self.dataset("ds_stamp_refused", inside)
        Dataset.objects.filter(pk=dataset.pk).update(modified_at=self.LONG_AGO)
        response = self.run_action(ADD, "t_stamp_inside", dataset="ds_stamp_refused")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.stamped(dataset), self.LONG_AGO)

    def test_a_member_tables_own_change_does_not_stamp(self):
        member = self.draft("t_stamp_member")
        dataset = self.dataset("ds_stamp_member", member)
        Dataset.objects.filter(pk=dataset.pk).update(modified_at=self.LONG_AGO)
        response = self.run_action("publish", "t_stamp_member", topic="climate")
        self.assertEqual(response.status_code, 204)
        member.stamp_data_modified()
        self.assertEqual(self.stamped(dataset), self.LONG_AGO)


class DraftTopicTests(DatasetActionTestCase):
    def test_adding_a_draft_never_seeds_the_draft_pseudo_topic(self):
        draft_topic, _ = Topic.objects.get_or_create(name=PSEUDO_TOPIC_DRAFT)
        table = self.draft("t_pseudo")
        table.topics.add(draft_topic)
        dataset = self.dataset("ds_pseudo")
        self.run_action(ADD, "t_pseudo", dataset="ds_pseudo")
        self.assertEqual(self.members(dataset), ["t_pseudo"])
        self.assertEqual(list(dataset.topics.all()), [])
