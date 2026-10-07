"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The bulk bar's delete and Dataset actions (#2565, spec #2551), through the
table action service, as seen through HTTP: the bulk preflight (POSTed, the
selection as one comma-joined ``tables`` field), its left-out groups and
counted consequences, the typed count, the ceilings, the writes and what
comes back in ``HX-Trigger``.

A bulk Dataset dialog asks the preflight again when a Dataset is chosen,
sending the whole selection as ``selection``; those re-checks are requests
like any other here. That the browser swaps only the preview is htmx's part.

Assertions are on what a preflight leaves out and why, the counts it states,
what the database holds afterwards and which response headers came back;
never on seconds.
"""  # noqa: 501

import re
from unittest import mock

from django.db import connection
from django.test.utils import CaptureQueriesContext

from api.services import table_actions
from dataedit.models import Dataset, Embargo, Table
from login.list_views import RECHECKED
from login.models import WRITE_PERM
from login.tests.helpers import HTMX
from login.tests.test_table_actions import DIALOG
from login.tests.test_table_dataset_actions import DatasetActionTestCase
from login.tests.test_table_delete import DeleteTestCase
from login.tests.test_tables_bulk import BulkTestCase
from modelview.tests.html import element_markup, element_with_id, text

ADD, REMOVE = table_actions.DATASET_ADD, table_actions.DATASET_REMOVE


class BulkCase(BulkTestCase):
    def joined_preflight(self, action, *names, **params):
        """The bulk bar's preflight, as the browser sends it: the names in
        one joined field."""
        response = self.client.post(
            self.check_path(action), {"tables": ",".join(names), **params}, **HTMX
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, DIALOG)
        return response

    def joined_run(self, action, *names, **params):
        """The dialog's confirmation: the eligible names, joined."""
        return self.client.post(
            self.action_path(action), {"tables": ",".join(names), **params}, **HTMX
        )

    def html(self, response):
        return response.content.decode()


class BulkBarTests(BulkCase):
    def test_the_bar_offers_the_dataset_actions_and_delete_last(self):
        self.draft("t_bar")
        html = self.get().content.decode()
        positions = []
        for verb in ("publish", "unpublish", ADD, REMOVE, "delete"):
            with self.subTest(verb=verb):
                button = element_with_id(html, f"bulk-{verb}")
                self.assertIn(f'hx-post="{self.check_path(verb)}"', button)
                self.assertIn("data-bulk-action", button)
                self.assertNotEqual(element_with_id(html, f"bulk-menu-{verb}"), "")
                positions.append(html.index(f'id="bulk-{verb}"'))
        self.assertEqual(positions, sorted(positions))


class BulkDeletePreflightTests(BulkCase, DeleteTestCase):
    def test_every_table_is_listed(self):
        names = [f"t_list_{i:02}" for i in range(12)]
        for name in names[:-1]:
            self.draft(name)
        self.draft(names[-1], published=True)
        response = self.joined_preflight("delete", *names)
        check = response.context["preflight"]
        self.assertEqual(check.names, names)
        listing = element_markup(self.html(response), "table-action-list")
        for name in names:
            with self.subTest(name=name):
                self.assertIn(name, listing)
        self.assertIn('name="tables" value="' + ",".join(names), self.html(response))

    def test_the_consequences_are_counted(self):
        a = self.draft("t_a", published=True)
        b = self.draft("t_b", published=True)
        self.draft("t_c")
        mine = Dataset.objects.create(
            name="ds_mine", creator=self.user, metadata={"title": "Wind atlas"}
        )
        mine.tables.add(a, b)
        theirs = Dataset.objects.create(
            name="ds_theirs", creator=self.stranger, metadata={"title": "Grid study"}
        )
        theirs.tables.add(a)
        self.review("t_a", finished=True)
        self.review("t_b", finished=True)
        self.review("t_c", finished=False)
        Embargo.objects.create(table=b, duration="6_months")
        response = self.joined_preflight("delete", "t_a", "t_b", "t_c")
        consequences = response.context["preflight"].consequences
        # by title, as the Dataset chooser and the Datasets column name them
        self.assertEqual(consequences["own_datasets"], [("Wind atlas", 2)])
        self.assertEqual(
            consequences["others_datasets"], [(self.stranger.name, "Grid study", 1)]
        )
        self.assertEqual(len(consequences["published"]), 2)
        self.assertEqual(consequences["finished_reviews"], 2)
        self.assertEqual(consequences["open_reviews"], 1)
        self.assertEqual([t.name for t, _ in consequences["embargoed"]], ["t_b"])
        self.assertTrue(consequences["knowledge_graph"])
        html = self.html(response)
        self.assertIn(
            "2 of them are published",
            text(element_markup(html, "table-action-published")),
        )
        self.assertIn(
            "2 reviewed, 1 in review.",
            text(element_markup(html, "table-action-reviews")),
        )
        self.assertIn(
            "1 is under an embargo",
            text(element_markup(html, "table-action-embargoes")),
        )
        self.assertIn(
            "Wind atlas (2 tables)",
            text(element_markup(html, "table-action-own-datasets")),
        )
        self.assertIn(
            f"Grid study ({self.stranger.name}): 1 table",
            text(element_markup(html, "table-action-datasets")),
        )
        consequences_text = text(element_markup(html, "table-action-consequences"))
        self.assertNotIn("ds_mine", consequences_text)
        self.assertNotIn("ds_theirs", consequences_text)
        self.assertIn(
            "Links to the 2 published tables",
            text(element_markup(html, "table-action-knowledge-graph")),
        )

    def test_the_consequences_cost_the_same_whatever_the_batch(self):
        def queries(count):
            names = [f"t_cost_{count}_{i}" for i in range(count)]
            for name in names:
                table = self.draft(name, published=True)
                Dataset.objects.create(
                    name=f"ds_{name}", creator=self.stranger
                ).tables.add(table)
            self.joined_preflight("delete", *names)  # warms the Site cache
            with CaptureQueriesContext(connection) as captured:
                self.joined_preflight("delete", *names)
            return len(captured)

        self.assertEqual(queries(2), queries(20))

    def test_a_count_is_typed_for_any_published_or_more_than_ten(self):
        self.draft("t_d1")
        self.draft("t_d2")
        self.draft("t_p", published=True)
        plain = self.joined_preflight("delete", "t_d1", "t_d2")
        self.assertEqual(plain.context["preflight"].confirmation, "")
        self.assertEqual(element_with_id(self.html(plain), "action-confirm"), "")
        with_published = self.joined_preflight("delete", "t_d1", "t_p")
        self.assertEqual(with_published.context["preflight"].confirmation, "2")
        self.assertIn("Type the number of tables", self.html(with_published))
        many = [f"t_m{i}" for i in range(table_actions.TYPED_COUNT_ABOVE + 1)]
        for name in many:
            self.draft(name)
        check = self.joined_preflight("delete", *many).context["preflight"]
        self.assertEqual(check.confirmation, str(len(many)))

    def test_the_ceiling_is_stated_before_it_is_reached(self):
        self.draft("t_s1")
        self.draft("t_s2")
        html = self.html(self.joined_preflight("delete", "t_s1", "t_s2"))
        self.assertEqual(
            text(element_markup(html, "table-action-ceiling-rule")),
            "Delete takes at most 50 tables at a time.",
        )

    def test_the_ceiling_is_stated_with_the_selection_size(self):
        names = [f"t_ceil_{i}" for i in range(60)]
        response = self.joined_preflight("delete", *names)
        self.assertContains(
            response, "Delete takes at most 50 tables at a time; you selected 60."
        )
        self.assertEqual(
            element_with_id(self.html(response), "table-action-confirm"), ""
        )


class BulkDeleteTests(BulkCase, DeleteTestCase):
    def test_a_wrong_count_deletes_nothing_and_stays_in_the_dialog(self):
        self.draft("t_x1")
        self.draft("t_x2", published=True)
        with mock.patch.object(Table, "drop_oedb_table") as drop:
            response = self.joined_run("delete", "t_x1", "t_x2", confirm="1")
        self.assertEqual(response.status_code, 400)
        self.assertIn("2", response.context["errors"]["confirm"])
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(self.exists("t_x1", "t_x2"), {"t_x1", "t_x2"})
        drop.assert_not_called()

    def test_with_its_count_typed_the_batch_goes_in_one_request(self):
        names = ["t_y1", "t_y2", "t_y3"]
        self.draft(names[0], title="Y one", published=True)
        self.draft(names[1])
        self.draft(names[2])
        with mock.patch.object(Table, "drop_oedb_table") as drop:
            response = self.joined_run("delete", *names, confirm="3")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.exists(*names), set())
        self.assertEqual(drop.call_count, 3)
        detail = self.trigger(response, "tables-changed")
        self.assertEqual(detail["message"], "Deleted 3 tables.")
        self.assertEqual(sorted(detail["gone"]), names)
        self.assertIn("“Y one”", detail["tables"])
        self.assertNotIn("warning", detail)

    def test_a_small_batch_of_drafts_needs_no_typing(self):
        self.draft("t_z1")
        self.draft("t_z2")
        with mock.patch.object(Table, "drop_oedb_table"):
            response = self.joined_run("delete", "t_z1", "t_z2")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.exists("t_z1", "t_z2"), set())

    def test_each_failed_drop_is_named_in_the_lasting_warning(self):
        names = ["t_ok", "t_stuck_1", "t_stuck_2"]
        self.draft("t_ok", title="Fine")
        self.draft("t_stuck_1", title="Stuck one")
        self.draft("t_stuck_2", title="Stuck two")

        def drop(instance, lock_timeout=None):
            if instance.name.startswith("t_stuck"):
                raise RuntimeError("the OEDB went away")

        with mock.patch.object(Table, "drop_oedb_table", drop):
            with self.assertLogs("oeplatform.table_actions", "INFO") as logs:
                response = self.joined_run("delete", *names)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.exists(*names), set())
        detail = self.trigger(response, "tables-changed")
        self.assertIs(detail["warning"], True)
        self.assertIn("“Stuck one” (t_stuck_1)", detail["message"])
        self.assertIn("“Stuck two” (t_stuck_2)", detail["message"])
        self.assertNotIn("Fine", detail["message"])
        self.assertEqual(sorted(detail["gone"]), sorted(names))
        batches = {
            re.search(r"batch=(\S+)", record.getMessage()).group(1)
            for record in logs.records
        }
        self.assertEqual(len(batches), 1)
        self.assertNotEqual(batches, {"-"})
        failed = [r for r in logs.records if r.getMessage().endswith("drop=failed")]
        self.assertEqual(len(failed), 2)

    def test_one_table_no_longer_allowed_refuses_the_whole_batch(self):
        self.draft("t_w1")
        self.draft("t_w2", level=WRITE_PERM)
        with mock.patch.object(Table, "drop_oedb_table") as drop:
            response = self.joined_run("delete", "t_w1", "t_w2")
        self.assertEqual(response.status_code, 409)
        self.assertIn(
            "Only Data maintainers and Table admins can delete",
            self.trigger(response, "tables-refused")["message"],
        )
        self.assertEqual(self.exists("t_w1", "t_w2"), {"t_w1", "t_w2"})
        drop.assert_not_called()


class BulkDatasetPreflightTests(BulkCase, DatasetActionTestCase):
    def test_the_dialog_offers_my_datasets_and_leaves_out_by_role(self):
        self.draft("t_mine_1", level=WRITE_PERM)
        self.draft("t_mine_2", level=WRITE_PERM)
        self.draft("t_strangers", level=None)
        self.dataset("ds_one", title="One")
        self.dataset("ds_two", title="Two")
        response = self.joined_preflight(ADD, "t_mine_1", "t_mine_2", "t_strangers")
        check = response.context["preflight"]
        self.assertEqual(self.choices(check), ["ds_one", "ds_two"])
        self.assertIsNone(check.dataset)
        self.assertEqual(check.names, ["t_mine_1", "t_mine_2"])
        self.assertEqual(
            self.left_out(check), {table_actions.NOT_YOURS: ["t_strangers"]}
        )
        html = self.html(response)
        # the re-check on choosing carries the whole selection
        self.assertIn(
            'value="t_mine_1,t_mine_2,t_strangers"',
            element_with_id(html, "table-action-selection"),
        )
        self.assertIn(
            f'hx-post="{self.check_path(ADD)}"',
            element_with_id(html, "table-action-chooser"),
        )

    def test_choosing_a_dataset_re_checks_the_whole_selection(self):
        """What the select sends: its form, with the eligible ``tables`` and
        the whole ``selection``. The answer still names the Table the role
        left out, now beside the ones already in the Dataset."""
        a = self.draft("t_in_a", level=WRITE_PERM)
        self.draft("t_new_b", level=WRITE_PERM)
        self.draft("t_other", level=None)
        self.dataset("ds_target", a, title="Target")
        self.dataset("ds_spare")
        response = self.client.post(
            self.check_path(ADD),
            {
                "tables": "t_in_a,t_new_b",
                "selection": "t_in_a,t_new_b,t_other",
                "dataset": "ds_target",
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 200)
        check = response.context["preflight"]
        self.assertEqual(self.chosen(check), "ds_target")
        self.assertEqual(check.names, ["t_new_b"])
        self.assertEqual(
            self.left_out(check),
            {
                table_actions.NOT_YOURS: ["t_other"],
                "Already in “Target”": ["t_in_a"],
            },
        )
        html = self.html(response)
        preview = element_markup(html, "table-action-preview")
        self.assertIn('name="tables" value="t_new_b"', preview)
        self.assertEqual(
            text(element_markup(html, "table-action-recheck")),
            "1 of 3 tables will be added to “Target”.",
        )
        # the title counts what the list counts, so it follows the choice
        # and the re-check swaps it with the preview (#2596)
        self.assertEqual(
            text(element_markup(html, "table-action-title")),
            "Add 1 of 3 tables to a dataset",
        )
        self.assertIn(
            "#table-action-title",
            element_with_id(html, "table-action-chooser"),
        )
        self.assertNotEqual(element_with_id(html, "table-action-confirm"), "")

    def test_a_dataset_filled_since_the_dialog_opened_leaves_nothing(self):
        """The dialog offers only Datasets missing one of the Tables; if the
        last of them is added elsewhere before the user chooses it, the
        re-check has nothing left to add and offers no confirmation."""
        a = self.draft("t_full_a", level=WRITE_PERM)
        b = self.draft("t_full_b", level=WRITE_PERM)
        full = self.dataset("ds_full", a, title="Full")
        self.dataset("ds_spare")
        opened = self.joined_preflight(ADD, "t_full_a", "t_full_b")
        self.assertIn("ds_full", self.choices(opened.context["preflight"]))
        full.tables.add(b)
        response = self.client.post(
            self.check_path(ADD),
            {
                "tables": "t_full_a,t_full_b",
                "selection": "t_full_a,t_full_b",
                "dataset": "ds_full",
            },
            **HTMX,
        )
        check = response.context["preflight"]
        self.assertEqual(check.names, [])
        self.assertFalse(check.confirmable)
        html = self.html(response)
        self.assertEqual(
            text(element_markup(html, "table-action-nothing")),
            "Nothing to add to “Full”.",
        )
        self.assertEqual(element_with_id(html, "table-action-confirm"), "")

    def test_remove_leaves_out_what_the_chosen_dataset_does_not_hold(self):
        a = self.draft("t_r_a", level=WRITE_PERM)
        b = self.draft("t_r_b", level=WRITE_PERM)
        self.draft("t_r_c", level=WRITE_PERM)
        self.dataset("ds_holds", a, b, title="Holds")
        self.dataset("ds_other", a)
        check = self.joined_preflight(
            REMOVE, "t_r_a", "t_r_b", "t_r_c", dataset="ds_holds"
        ).context["preflight"]
        self.assertEqual(sorted(self.choices(check)), ["ds_holds", "ds_other"])
        self.assertEqual(check.names, ["t_r_a", "t_r_b"])
        self.assertEqual(self.left_out(check), {"Not in “Holds”": ["t_r_c"]})

    def test_a_row_dialog_does_not_re_check(self):
        self.draft("t_row", level=WRITE_PERM)
        self.dataset("ds_row_1")
        self.dataset("ds_row_2")
        html = self.html(self.preflight(ADD, "t_row"))
        self.assertNotIn('name="selection"', html)
        self.assertEqual(element_with_id(html, "table-action-chooser"), "")
        self.assertNotEqual(element_with_id(html, "action-dataset"), "")

    def test_the_dataset_actions_have_a_measured_ceiling(self):
        for action in (ADD, REMOVE):
            with self.subTest(action=action):
                self.assertGreater(table_actions.CEILINGS[action], 100)

    def test_over_the_ceiling_the_dialog_says_so_and_offers_no_choice(self):
        names = [f"t_over_{i}" for i in range(3)]
        for name in names:
            self.draft(name, level=WRITE_PERM)
        self.dataset("ds_over")
        with mock.patch.dict(table_actions.CEILINGS, {ADD: 2}):
            response = self.joined_preflight(ADD, *names)
        self.assertContains(
            response,
            "Adding to a dataset takes at most 2 tables at a time; you selected 3.",
        )
        html = self.html(response)
        self.assertEqual(element_with_id(html, "action-dataset"), "")
        self.assertEqual(element_with_id(html, "table-action-confirm"), "")


class BulkDatasetTests(BulkCase, DatasetActionTestCase):
    def test_a_batch_is_added_in_one_request(self):
        names = ["t_add_1", "t_add_2", "t_add_3"]
        for name in names:
            self.draft(name, level=WRITE_PERM)
        dataset = self.dataset("ds_bulk", title="Bulk")
        with self.assertLogs("oeplatform.table_actions", "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.joined_run(ADD, *names, dataset="ds_bulk")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.members(dataset), names)
        detail = self.trigger(response, "tables-changed")
        self.assertTrue(detail["message"].startswith("Added 3 tables to “Bulk”."))
        self.assertEqual(len(detail["tables"]), 3)
        self.assertEqual(len(logs.records), 3)
        self.assertTrue(
            all(r.getMessage().endswith("dataset=ds_bulk") for r in logs.records)
        )

    def test_a_batch_is_removed_in_one_request(self):
        a = self.draft("t_rm_1", level=WRITE_PERM)
        b = self.draft("t_rm_2", level=WRITE_PERM)
        dataset = self.dataset("ds_rm", a, b, title="Rm")
        response = self.joined_run(REMOVE, "t_rm_1", "t_rm_2", dataset="ds_rm")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.members(dataset), [])
        self.assertTrue(
            self.trigger(response, "tables-changed")["message"].startswith(
                "Removed 2 tables from “Rm”."
            )
        )
        self.assertEqual(Table.objects.filter(name__in=["t_rm_1", "t_rm_2"]).count(), 2)

    def test_a_failure_part_way_adds_nothing(self):
        names = ["t_part_1", "t_part_2", "t_part_3"]
        for name in names:
            self.draft(name, level=WRITE_PERM)
        dataset = self.dataset("ds_part")
        real = table_actions.assign_table
        calls = []

        def assign(target, table):
            calls.append(table.name)
            if len(calls) == 2:
                raise RuntimeError("the database went away")
            real(target, table)

        with mock.patch.object(table_actions, "assign_table", assign):
            with self.assertRaises(RuntimeError):
                self.joined_run(ADD, *names, dataset="ds_part")
        self.assertEqual(self.members(dataset), [])

    def test_a_table_already_in_the_dataset_refuses_the_whole_batch(self):
        """A confirmation sent before the re-check on choosing came back
        names Tables already in the Dataset: nothing is added, and the
        dialog comes back with the check run on the chosen Dataset."""
        a = self.draft("t_race_a", level=WRITE_PERM)
        self.draft("t_race_b", level=WRITE_PERM)
        dataset = self.dataset("ds_race", a, title="Race")
        response = self.joined_run(ADD, "t_race_a", "t_race_b", dataset="ds_race")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.members(dataset), ["t_race_a"])
        check = response.context["preflight"]
        self.assertEqual(check.names, ["t_race_b"])
        self.assertIn(
            "Already in “Race”", self.trigger(response, "tables-refused")["message"]
        )

    def test_a_confirmation_checked_against_another_dataset_runs_nothing(self):
        """Confirmed in the moment between choosing a Dataset and its
        re-check coming back: the names were checked against the Dataset
        chosen before, so nothing is added and the dialog shows the check
        for the one sent, on the whole selection."""
        a = self.draft("t_quick_a", level=WRITE_PERM)
        self.draft("t_quick_b", level=WRITE_PERM)
        self.draft("t_quick_c", level=None)
        before = self.dataset("ds_before")
        after = self.dataset("ds_after", a, title="After")
        response = self.client.post(
            self.action_path(ADD),
            {
                "tables": "t_quick_a,t_quick_b",
                "selection": "t_quick_a,t_quick_b,t_quick_c",
                "dataset": "ds_after",
                "previewed": "ds_before",
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(response.context["notice"], RECHECKED)
        self.assertEqual(self.members(before), [])
        self.assertEqual(self.members(after), ["t_quick_a"])
        check = response.context["preflight"]
        self.assertEqual(self.chosen(check), "ds_after")
        self.assertEqual(check.names, ["t_quick_b"])
        self.assertEqual(
            self.left_out(check),
            {
                table_actions.NOT_YOURS: ["t_quick_c"],
                "Already in “After”": ["t_quick_a"],
            },
        )

    def test_a_confirmation_checked_against_its_own_dataset_runs(self):
        self.draft("t_same_a", level=WRITE_PERM)
        dataset = self.dataset("ds_same")
        response = self.client.post(
            self.action_path(ADD),
            {
                "tables": "t_same_a",
                "selection": "t_same_a,t_absent",
                "dataset": "ds_same",
                "previewed": "ds_same",
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.members(dataset), ["t_same_a"])

    def test_a_refused_batch_is_checked_again_on_the_whole_selection(self):
        a = self.draft("t_ref_a", level=WRITE_PERM)
        self.draft("t_ref_b", level=WRITE_PERM)
        dataset = self.dataset("ds_ref", title="Ref")
        # added elsewhere after the dialog's check
        dataset.tables.add(a)
        response = self.client.post(
            self.action_path(ADD),
            {
                "tables": "t_ref_a,t_ref_b",
                "selection": "t_ref_a,t_ref_b,t_ref_gone",
                "dataset": "ds_ref",
                "previewed": "ds_ref",
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 409)
        check = response.context["preflight"]
        self.assertEqual(check.requested, ["t_ref_a", "t_ref_b", "t_ref_gone"])
        self.assertEqual(
            self.left_out(check),
            {
                table_actions.NOT_YOURS: ["t_ref_gone"],
                "Already in “Ref”": ["t_ref_a"],
            },
        )
        self.assertEqual(self.members(dataset), ["t_ref_a"])

    def test_an_unusable_dataset_keeps_the_whole_selection(self):
        self.draft("t_bad_a", level=WRITE_PERM)
        self.dataset("ds_mine_1")
        self.dataset("ds_mine_2")
        self.dataset("ds_strangers", creator=self.stranger)
        response = self.client.post(
            self.action_path(ADD),
            {
                "tables": "t_bad_a",
                "selection": "t_bad_a,t_bad_gone",
                "dataset": "ds_strangers",
            },
            **HTMX,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("dataset", response.context["errors"])
        check = response.context["preflight"]
        self.assertEqual(check.requested, ["t_bad_a", "t_bad_gone"])
        self.assertEqual(
            self.left_out(check), {table_actions.NOT_YOURS: ["t_bad_gone"]}
        )

    def test_over_the_ceiling_nothing_is_added(self):
        names = [f"t_much_{i}" for i in range(3)]
        for name in names:
            self.draft(name, level=WRITE_PERM)
        dataset = self.dataset("ds_much")
        with mock.patch.dict(table_actions.CEILINGS, {ADD: 2}):
            response = self.joined_run(ADD, *names, dataset="ds_much")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.context["errors"]["table"],
            "Adding to a dataset takes at most 2 tables at a time; you selected 3.",
        )
        self.assertEqual(self.members(dataset), [])
