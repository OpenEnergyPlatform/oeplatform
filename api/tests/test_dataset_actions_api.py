# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Dataset action service through its first caller, the API (#2619,
spec #2613): ``DELETE /datasets/<name>/``, ``assign-tables/`` and
``unassign-tables/``.

Assertions are on response codes and bodies, what the database holds
afterwards (members, ``modified_at``), which log lines were written and how
many queries a refusal cost; never on seconds.

The typed confirmation has no caller that can get it wrong yet (the API's
address is its confirmation; the dashboard's dialog is #2623), so
``DeleteConfirmationTests`` calls the service directly.
"""

from datetime import datetime
from datetime import timezone as dt_timezone

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.services import dataset_actions
from dataedit.models import DATASET_NOT_FOUND, Dataset, Table, Topic
from login.models import WRITE_PERM, UserPermission, myuser

LONG_AGO = datetime(2020, 1, 1, tzinfo=dt_timezone.utc)
LOGGER = "oeplatform.dataset_actions"


def make_user(name):
    user, _ = myuser.objects.get_or_create(
        name=name,
        email=f"{name.lower()}@test.com",
        did_agree=True,
        is_mail_verified=True,
    )
    return user


class DatasetActionAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.creator = make_user("ActionCreator")
        cls.stranger = make_user("ActionStranger")

    def setUp(self):
        self.client.force_authenticate(user=self.creator)

    def dataset(self, name, *tables, creator=None, published=False):
        dataset = Dataset.objects.create(
            name=name,
            metadata={"name": name, "title": name, "description": ""},
            creator=creator or self.creator,
            published_at=timezone.now() if published else None,
            modified_at=LONG_AGO,
        )
        dataset.tables.add(*tables)
        return dataset

    def table(self, name, published=True, holder=None):
        table = Table.objects.create(
            name=name,
            is_publish=published,
            oemetadata={"resources": [{"name": name}]},
        )
        if holder is not None:
            UserPermission.objects.create(holder=holder, table=table, level=WRITE_PERM)
        return table

    def members(self, dataset):
        return sorted(dataset.tables.values_list("name", flat=True))

    def modified(self, dataset):
        return Dataset.objects.get(pk=dataset.pk).modified_at

    def delete(self, name):
        return self.client.delete(f"/api/v0/datasets/{name}/")

    def assign(self, dataset, *names):
        return self.client.post(
            f"/api/v0/datasets/{dataset}/assign-tables/",
            {"tables": [{"name": name} for name in names]},
            format="json",
        )

    def unassign(self, dataset, *names):
        return self.client.post(
            f"/api/v0/datasets/{dataset}/unassign-tables/",
            {"tables": [{"name": name} for name in names]},
            format="json",
        )


class DeleteAPITests(DatasetActionAPITestCase):
    def test_a_draft_goes_with_a_bare_204_and_its_members_stay(self):
        member = self.table("t_member_stays")
        self.dataset("ds_draft_gone", member)
        response = self.delete("ds_draft_gone")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Dataset.objects.filter(name="ds_draft_gone").exists())
        self.assertTrue(Table.objects.filter(pk=member.pk).exists())

    def test_a_published_dataset_is_confirmed_by_its_address(self):
        self.dataset("ds_published_gone", published=True)
        response = self.delete("ds_published_gone")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dataset.objects.filter(name="ds_published_gone").exists())

    def test_a_repeat_is_a_404(self):
        self.dataset("ds_twice")
        self.assertEqual(self.delete("ds_twice").status_code, 204)
        response = self.delete("ds_twice")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"detail": DATASET_NOT_FOUND})

    def test_a_foreign_draft_is_a_404_worded_as_an_unknown_name(self):
        self.dataset("ds_their_draft", creator=self.stranger)
        foreign = self.delete("ds_their_draft")
        unknown = self.delete("ds_never_existed")
        self.assertEqual(foreign.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(foreign.content, unknown.content)
        self.assertTrue(Dataset.objects.filter(name="ds_their_draft").exists())

    def test_a_foreign_published_dataset_is_a_403(self):
        self.dataset("ds_their_published", creator=self.stranger, published=True)
        response = self.delete("ds_their_published")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Dataset.objects.filter(name="ds_their_published").exists())

    def test_one_line_after_commit_saying_state_and_members(self):
        self.dataset("ds_logged_draft", self.table("t_log_a"), self.table("t_log_b"))
        self.dataset("ds_logged_published", published=True)
        with self.assertLogs(LOGGER, "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                self.delete("ds_logged_draft")
                self.delete("ds_logged_published")
        self.assertEqual(len(callbacks), 2)
        line = "dataset_action dataset=%s action=delete %s by=%s via=api batch=-"
        self.assertEqual(
            [record.getMessage() for record in logs.records],
            [
                line % ("ds_logged_draft", "published=no members=2", self.creator.pk),
                line
                % ("ds_logged_published", "published=yes members=0", self.creator.pk),
            ],
        )

    def test_a_refused_delete_logs_nothing(self):
        self.dataset("ds_not_mine", creator=self.stranger, published=True)
        with self.assertNoLogs(LOGGER, "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                self.delete("ds_not_mine")
                self.delete("ds_nowhere")


class DeleteConfirmationTests(DatasetActionAPITestCase):
    """The typed confirmation, enforced by ``execute`` under the lock: the
    name for one published Dataset, the count for a batch holding a
    published one or more than ``TYPED_COUNT_ABOVE``, nothing for drafts
    alone."""

    def run_delete(self, *names, confirm=""):
        return dataset_actions.execute(
            self.creator, dataset_actions.DELETE, list(names), {"confirm": confirm}
        )

    def test_what_each_case_asks_for(self):
        self.dataset("ds_c_draft")
        self.dataset("ds_c_published", published=True)
        many = [f"ds_c_many_{i}" for i in range(dataset_actions.TYPED_COUNT_ABOVE + 1)]
        for name in many:
            self.dataset(name)
        cases = {
            ("ds_c_draft",): "",
            ("ds_c_published",): "ds_c_published",
            ("ds_c_draft", "ds_c_published"): "2",
            tuple(many[:-1]): "",
            tuple(many): str(len(many)),
        }
        for names, typed in cases.items():
            with self.subTest(names=names[:2]):
                check = dataset_actions.preflight(
                    self.creator, dataset_actions.DELETE, list(names)
                )
                self.assertEqual(check.confirmation, typed)

    def test_a_published_dataset_without_its_name_is_kept(self):
        self.dataset("ds_keep_me", self.table("t_keep_member"), published=True)
        with self.assertNoLogs(LOGGER, "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                for confirm in ("", "ds_keep", "1"):
                    with self.subTest(confirm=confirm):
                        with self.assertRaises(
                            dataset_actions.InvalidParameters
                        ) as refused:
                            self.run_delete("ds_keep_me", confirm=confirm)
                        self.assertIn("confirm", refused.exception.errors)
        self.assertEqual(
            self.members(Dataset.objects.get(name="ds_keep_me")), ["t_keep_member"]
        )

    def test_it_is_judged_on_the_dataset_as_it_is_when_locked(self):
        dataset = self.dataset("ds_published_since")
        check = dataset_actions.preflight(
            self.creator, dataset_actions.DELETE, ["ds_published_since"]
        )
        self.assertEqual(check.confirmation, "")
        Dataset.objects.filter(pk=dataset.pk).update(published_at=timezone.now())
        with self.assertRaises(dataset_actions.InvalidParameters):
            self.run_delete("ds_published_since")
        self.run_delete("ds_published_since", confirm="ds_published_since")
        self.assertFalse(Dataset.objects.filter(pk=dataset.pk).exists())

    def test_a_batch_is_deleted_whole_or_not_at_all(self):
        self.dataset("ds_batch_mine")
        self.dataset("ds_batch_theirs", creator=self.stranger, published=True)
        with self.assertRaises(dataset_actions.ActionRefused) as refused:
            self.run_delete("ds_batch_mine", "ds_batch_theirs", confirm="2")
        self.assertTrue(refused.exception.for_role)
        self.assertEqual(
            Dataset.objects.filter(name__startswith="ds_batch_").count(), 2
        )


class AssignAPITests(DatasetActionAPITestCase):
    def test_a_strangers_published_table_can_be_added(self):
        table = self.table("t_strangers_published", holder=self.stranger)
        dataset = self.dataset("ds_curated")
        response = self.assign("ds_curated", "t_strangers_published")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["added"], ["t_strangers_published"])
        self.assertEqual(self.members(dataset), [table.name])

    def test_a_strangers_draft_refuses_the_whole_request_naming_it(self):
        self.table("t_fine")
        self.table("t_strangers_draft", published=False, holder=self.stranger)
        dataset = self.dataset("ds_refused")
        response = self.assign("ds_refused", "t_fine", "t_strangers_draft")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("t_strangers_draft", response.json()["detail"])
        self.assertNotIn("t_fine", response.json()["detail"])
        self.assertEqual(self.members(dataset), [])
        self.assertEqual(self.modified(dataset), LONG_AGO)

    def test_an_existing_member_is_passed_over_and_reported_as_before(self):
        member = self.table("t_already")
        dataset = self.dataset("ds_already", member)
        response = self.assign("ds_already", "t_already", "t_not_a_table")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # as before #2619: after the call it is in the Dataset, so a
        # repeated call answers as the first did
        self.assertEqual(response.data["added"], ["t_already"])
        self.assertEqual(response.data["missing"], [{"name": "t_not_a_table"}])
        self.assertEqual(self.members(dataset), ["t_already"])

    def test_a_table_made_unassignable_after_the_preflight_refuses_whole(self):
        self.table("t_still_fine")
        withdrawn = self.table("t_withdrawn", holder=self.stranger)
        dataset = self.dataset("ds_race")
        names = ["t_still_fine", "t_withdrawn"]
        params = {"dataset": "ds_race"}
        check = dataset_actions.preflight(
            self.creator, dataset_actions.MEMBERS_ADD, names, params
        )
        self.assertEqual(check.names, names)
        Table.objects.filter(pk=withdrawn.pk).update(is_publish=False)
        with self.assertNoLogs(LOGGER, "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                with self.assertRaises(dataset_actions.ActionRefused) as refused:
                    dataset_actions.execute(
                        self.creator, dataset_actions.MEMBERS_ADD, names, params
                    )
        self.assertEqual(
            refused.exception.refused,
            [dataset_actions.LeftOut(dataset_actions.MAY_NOT_ASSIGN, ["t_withdrawn"])],
        )
        self.assertEqual(self.members(dataset), [])

    def test_a_foreign_draft_is_a_404_and_a_foreign_published_a_403(self):
        self.table("t_target")
        self.dataset("ds_their_draft_members", creator=self.stranger)
        self.dataset("ds_their_public_members", creator=self.stranger, published=True)
        for route in (self.assign, self.unassign):
            with self.subTest(route=route.__name__):
                draft = route("ds_their_draft_members", "t_target")
                unknown = route("ds_no_such_members", "t_target")
                public = route("ds_their_public_members", "t_target")
                self.assertEqual(draft.status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(draft.content, unknown.content)
                self.assertEqual(draft.json(), {"detail": DATASET_NOT_FOUND})
                self.assertEqual(public.status_code, status.HTTP_403_FORBIDDEN)


class UnassignAPITests(DatasetActionAPITestCase):
    def test_any_member_is_removed_without_a_table_role_and_topics_stay(self):
        theirs = self.table("t_their_draft", published=False, holder=self.stranger)
        dataset = self.dataset("ds_curation", theirs)
        topic = Topic.objects.create(name="dataset_actions_topic")
        dataset.topics.add(topic)
        response = self.unassign("ds_curation", "t_their_draft", "t_never_in")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["removed"], ["t_their_draft"])
        self.assertEqual(response.data["missing"], [{"name": "t_never_in"}])
        self.assertEqual(self.members(dataset), [])
        self.assertTrue(Table.objects.filter(pk=theirs.pk).exists())
        self.assertEqual(list(dataset.topics.all()), [topic])


class CeilingTests(DatasetActionAPITestCase):
    def test_over_2500_names_is_a_400_before_anything_is_read(self):
        self.dataset("ds_ceiling")
        names = [f"t_{i}" for i in range(2501)]
        for route, words in (
            (self.assign, "Adding tables to a dataset"),
            (self.unassign, "Removing tables from a dataset"),
        ):
            with self.subTest(route=route.__name__):
                with self.assertNumQueries(0):
                    response = route("ds_ceiling", *names)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(
                    response.json(),
                    {
                        "tables": [
                            f"{words} takes at most 2,500 tables at a time;"
                            " you selected 2,501."
                        ]
                    },
                )

    def test_2500_names_reach_the_service(self):
        self.dataset("ds_at_ceiling")
        names = [f"t_{i}" for i in range(2500)]
        response = self.unassign("ds_at_ceiling", *names)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["missing"]), 2500)


class PreflightQueryTests(DatasetActionAPITestCase):
    """What a preflight costs is constant in the number of names: delete one
    query, an add four (the Dataset, the Tables, the members and the
    assignable among them), a removal two (the Dataset, the members)."""

    def test_the_budgets_hold_for_one_name_and_for_many(self):
        tables = [self.table(f"t_budget_{i}") for i in range(30)]
        self.dataset("ds_budget", *tables[:10])
        for i in range(30):
            self.dataset(f"ds_budget_del_{i}")
        names = [table.name for table in tables]
        params = {"dataset": "ds_budget"}
        for count in (1, 30):
            with self.subTest(names=count):
                with self.assertNumQueries(1):
                    dataset_actions.preflight(
                        self.creator,
                        dataset_actions.DELETE,
                        [f"ds_budget_del_{i}" for i in range(count)],
                    )
                with self.assertNumQueries(4):
                    dataset_actions.preflight(
                        self.creator, dataset_actions.MEMBERS_ADD, names[:count], params
                    )
                with self.assertNumQueries(2):
                    dataset_actions.preflight(
                        self.creator,
                        dataset_actions.MEMBERS_REMOVE,
                        names[:count],
                        params,
                    )


class MemberLogTests(DatasetActionAPITestCase):
    def test_one_line_per_table_after_commit_tied_by_a_batch(self):
        self.table("t_line_a")
        self.table("t_line_b")
        self.dataset("ds_lines")
        with self.assertLogs(LOGGER, "INFO") as added:
            with self.captureOnCommitCallbacks(execute=True):
                self.assign("ds_lines", "t_line_a", "t_line_b")
        with self.assertLogs(LOGGER, "INFO") as removed:
            with self.captureOnCommitCallbacks(execute=True):
                self.unassign("ds_lines", "t_line_a", "t_nowhere")
        messages = [record.getMessage() for record in added.records]
        batch = messages[0].split("batch=")[1]
        self.assertNotEqual(batch, "-")
        prefix = "dataset_action dataset=ds_lines action=%s table=%s by=%s via=api"
        self.assertEqual(
            messages,
            [
                prefix % ("members_add", "t_line_a", self.creator.pk)
                + f" batch={batch}",
                prefix % ("members_add", "t_line_b", self.creator.pk)
                + f" batch={batch}",
            ],
        )
        self.assertEqual(
            [record.getMessage() for record in removed.records],
            [prefix % ("members_remove", "t_line_a", self.creator.pk) + " batch=-"],
        )

    def test_a_refused_or_empty_change_logs_nothing(self):
        self.table("t_their_draft_log", published=False, holder=self.stranger)
        self.dataset("ds_quiet", self.table("t_quiet_member"))
        with self.assertNoLogs(LOGGER, "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                self.assign("ds_quiet", "t_their_draft_log")
                self.assign("ds_quiet", "t_quiet_member")
                self.unassign("ds_quiet", "t_nowhere")


class StampTests(DatasetActionAPITestCase):
    """``modified_at`` moves on a real change of the membership, and only
    then."""

    def test_create_stamps_its_creation_time(self):
        response = self.client.post(
            "/api/v0/datasets/",
            {"name": "ds_created", "title": "Created", "description": "New."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dataset = Dataset.objects.get(name="ds_created")
        self.assertIsNotNone(dataset.modified_at)
        self.assertEqual(dataset.modified_at, dataset.created_at)

    def test_adding_and_removing_stamp(self):
        self.table("t_stamp")
        dataset = self.dataset("ds_stamped")
        before = timezone.now()
        self.assign("ds_stamped", "t_stamp")
        added = self.modified(dataset)
        self.assertGreaterEqual(added, before)
        Dataset.objects.filter(pk=dataset.pk).update(modified_at=LONG_AGO)
        self.unassign("ds_stamped", "t_stamp")
        self.assertGreaterEqual(self.modified(dataset), added)

    def test_a_no_op_does_not_stamp(self):
        member = self.table("t_noop_member")
        self.table("t_noop_outside")
        dataset = self.dataset("ds_noop", member)
        self.assign("ds_noop", "t_noop_member", "t_no_such")
        self.unassign("ds_noop", "t_noop_outside", "t_no_such")
        self.assertEqual(self.modified(dataset), LONG_AGO)

    def test_a_refused_request_does_not_stamp(self):
        self.table("t_refused_draft", published=False, holder=self.stranger)
        dataset = self.dataset("ds_not_stamped")
        self.assign("ds_not_stamped", "t_refused_draft")
        self.assertEqual(self.modified(dataset), LONG_AGO)
