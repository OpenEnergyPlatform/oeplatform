# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Create, edit, publish and unpublish through the Dataset action service,
through their first caller, the API (#2620, spec #2613):
``POST /datasets/``, ``PATCH /datasets/<name>/``, ``…/publish/`` and
``…/unpublish/``.

Assertions are on response codes and bodies, what the database holds
afterwards (``published_at``, ``modified_at``, Topics), which log lines were
written; never on seconds. Who may write at all (401, a foreign draft's 404,
a foreign published Dataset's 403) is pinned for every write route in
``test_dataset_lifecycle_api``.
"""

from datetime import datetime
from datetime import timezone as dt_timezone

from django.utils import timezone
from rest_framework import status

from api.services import dataset_actions
from api.tests.test_dataset_actions_api import (
    LOGGER,
    LONG_AGO,
    DatasetActionAPITestCase,
)
from dataedit.models import Dataset, Embargo, Topic
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

EARLIER = datetime(2024, 6, 1, tzinfo=dt_timezone.utc)


class DatasetWriteTestCase(DatasetActionAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.energy = Topic.objects.get_or_create(name="writes_energy")[0]
        cls.climate = Topic.objects.get_or_create(name="writes_climate")[0]
        Topic.objects.get_or_create(name=PSEUDO_TOPIC_DRAFT)

    def create(self, name, **fields):
        body = {"name": name, "title": name.title(), "description": "New."}
        body.update(fields)
        return self.client.post("/api/v0/datasets/", body, format="json")

    def patch(self, name, body):
        return self.client.patch(f"/api/v0/datasets/{name}/", body, format="json")

    def publish(self, name):
        return self.client.post(f"/api/v0/datasets/{name}/publish/")

    def unpublish(self, name):
        return self.client.post(f"/api/v0/datasets/{name}/unpublish/")

    def row(self, dataset):
        return Dataset.objects.get(pk=dataset.pk)

    def topics(self, dataset):
        return sorted(dataset.topics.values_list("name", flat=True))


class FromNothingToPublishedTests(DatasetWriteTestCase):
    def test_a_dataset_is_created_filled_and_published_through_the_api(self):
        self.table("t_journey")
        created = self.create("ds_journey", topics=["writes_energy"])
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        body = created.json()
        self.assertIsNone(body["published_at"])
        self.assertEqual(body["creator"], self.creator.name)
        self.assertEqual(body["topics"], ["writes_energy"])
        self.assertEqual(body["modified_at"], body["created_at"])

        assigned = self.assign("ds_journey", "t_journey")
        self.assertEqual(assigned.status_code, status.HTTP_200_OK)

        published = self.publish("ds_journey")
        self.assertEqual(published.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(published.json()["published_at"])
        self.assertTrue(Dataset.objects.get(name="ds_journey").is_published)
        # now anyone may read it
        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.get("/api/v0/datasets/ds_journey/").status_code,
            status.HTTP_200_OK,
        )


class ReadBodyTests(DatasetWriteTestCase):
    def test_a_read_carries_state_creator_topics_and_modification(self):
        dataset = self.dataset("ds_read_body", published=True)
        dataset.topics.add(self.energy, self.climate)
        body = self.client.get("/api/v0/datasets/ds_read_body/").json()
        self.assertEqual(body["creator"], self.creator.name)
        self.assertEqual(body["topics"], ["writes_climate", "writes_energy"])
        self.assertIsNotNone(body["published_at"])
        self.assertEqual(datetime.fromisoformat(body["modified_at"]), LONG_AGO)

    def test_an_ownerless_dataset_has_a_null_creator(self):
        dataset = self.dataset("ds_ownerless", published=True)
        Dataset.objects.filter(pk=dataset.pk).update(creator=None)
        body = self.client.get("/api/v0/datasets/ds_ownerless/").json()
        self.assertIsNone(body["creator"])

    def test_the_read_fields_are_accepted_by_no_write(self):
        dataset = self.dataset("ds_read_only")
        response = self.patch(
            "ds_read_only",
            {"published_at": "2026-01-01T00:00:00Z", "creator": "Someone"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = self.row(dataset)
        self.assertIsNone(row.published_at)
        self.assertEqual(row.creator, self.creator)


class CreateTests(DatasetWriteTestCase):
    def test_topics_are_optional(self):
        response = self.create("ds_no_topics")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["topics"], [])

    def test_an_unknown_topic_and_the_draft_topic_are_a_400_naming_them(self):
        cases = {
            "unknown": (["writes_energy", "no_such_topic"], ["no_such_topic"]),
            "draft": ([PSEUDO_TOPIC_DRAFT], [PSEUDO_TOPIC_DRAFT]),
            "both": (["nope", PSEUDO_TOPIC_DRAFT], ["nope", PSEUDO_TOPIC_DRAFT]),
        }
        for case, (topics, named) in cases.items():
            with self.subTest(case):
                response = self.create(f"ds_topics_{case}", topics=topics)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                message = " ".join(response.json()["topics"])
                for name in named:
                    self.assertIn(f"“{name}”", message)
                self.assertFalse(
                    Dataset.objects.filter(name=f"ds_topics_{case}").exists()
                )

    def test_a_taken_name_is_a_400_on_name_even_for_a_foreign_draft(self):
        self.dataset("ds_taken", creator=self.stranger)
        response = self.create("ds_taken")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.json())

    def test_one_line_after_commit(self):
        with self.assertLogs(LOGGER, "INFO") as logged:
            with self.captureOnCommitCallbacks(execute=True):
                self.create("ds_logged_create", topics=["writes_energy"])
        self.assertEqual(
            [record.getMessage() for record in logged.records],
            [
                "dataset_action dataset=ds_logged_create action=create "
                f"by={self.creator.pk} via=api batch=-"
            ],
        )


class EditTests(DatasetWriteTestCase):
    def setUp(self):
        super().setUp()
        self.edited = self.dataset("ds_edit")
        Dataset.objects.filter(pk=self.edited.pk).update(
            metadata={
                "name": "ds_edit",
                "title": "Old",
                "description": "Old.",
                "@id": "https://example.org/ds_edit",
            }
        )
        self.edited.topics.add(self.energy)

    def test_only_a_title_keeps_the_at_id_and_the_topics(self):
        response = self.patch("ds_edit", {"title": "New"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        metadata = response.json()["metadata"]
        self.assertEqual(metadata["title"], "New")
        self.assertEqual(metadata["description"], "Old.")
        self.assertEqual(metadata["@id"], "https://example.org/ds_edit")
        self.assertEqual(response.json()["topics"], ["writes_energy"])

    def test_a_name_is_a_400_even_when_equal(self):
        for name in ("ds_edit", "ds_renamed"):
            with self.subTest(name):
                response = self.patch("ds_edit", {"name": name, "title": "New"})
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("name", response.json())
        self.assertEqual(self.row(self.edited).metadata["title"], "Old")

    def test_topics_replace_the_set_and_an_empty_list_empties_it(self):
        response = self.patch("ds_edit", {"topics": ["writes_climate"]})
        self.assertEqual(response.json()["topics"], ["writes_climate"])
        response = self.patch("ds_edit", {"topics": []})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.topics(self.edited), [])

    def test_an_unknown_topic_and_the_draft_topic_are_a_400_naming_them(self):
        response = self.patch(
            "ds_edit", {"title": "New", "topics": ["nope", PSEUDO_TOPIC_DRAFT]}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        message = " ".join(response.json()["topics"])
        self.assertIn("“nope”", message)
        self.assertIn(f"“{PSEUDO_TOPIC_DRAFT}”", message)
        # nothing written, the title included
        self.assertEqual(self.row(self.edited).metadata["title"], "Old")
        self.assertEqual(self.topics(self.edited), ["writes_energy"])

    def test_a_no_op_leaves_modified_at_and_logs_nothing(self):
        for body in (
            {},
            {"title": "Old"},
            {"title": "Old", "description": "Old.", "topics": ["writes_energy"]},
            {"at_id": "https://example.org/ds_edit"},
        ):
            with self.subTest(body=body):
                with self.assertNoLogs(LOGGER, "INFO"):
                    with self.captureOnCommitCallbacks(execute=True):
                        response = self.patch("ds_edit", body)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(self.modified(self.edited), LONG_AGO)

    def test_a_real_change_moves_modified_at_and_logs_what_changed(self):
        before = timezone.now()
        with self.assertLogs(LOGGER, "INFO") as logged:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.patch(
                    "ds_edit", {"title": "New", "topics": ["writes_climate"]}
                )
        self.assertGreaterEqual(self.modified(self.edited), before)
        self.assertGreaterEqual(
            datetime.fromisoformat(response.json()["modified_at"]), before
        )
        self.assertEqual(
            [record.getMessage() for record in logged.records],
            [
                "dataset_action dataset=ds_edit action=edit changed=title,topics "
                f"by={self.creator.pk} via=api batch=-"
            ],
        )

    def test_a_topics_only_change_stamps_too(self):
        self.patch("ds_edit", {"topics": ["writes_energy", "writes_climate"]})
        self.assertNotEqual(self.modified(self.edited), LONG_AGO)


class PublishGateTests(DatasetWriteTestCase):
    def test_no_members_and_no_topics_is_a_409_naming_both_and_writes_nothing(self):
        dataset = self.dataset("ds_bare")
        with self.assertNoLogs(LOGGER, "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.publish("ds_bare")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        body = response.json()
        self.assertEqual(body["failed"], ["members", "topics"])
        self.assertIn("detail", body)
        self.assertIsNone(self.row(dataset).published_at)

    def test_with_one_missing_exactly_that_one_is_named(self):
        without_topics = self.dataset("ds_no_topic", self.table("t_gate_member"))
        without_members = self.dataset("ds_no_member")
        without_members.topics.add(self.energy)
        for dataset, failed in (
            (without_topics, ["topics"]),
            (without_members, ["members"]),
        ):
            with self.subTest(dataset.name):
                response = self.publish(dataset.name)
                self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
                self.assertEqual(response.json()["failed"], failed)
                self.assertIsNone(self.row(dataset).published_at)

    def test_draft_and_embargoed_members_publish(self):
        draft = self.table("t_mix_draft", published=False, holder=self.creator)
        embargoed = self.table("t_mix_embargoed")
        Embargo.objects.create(table=embargoed, duration="1_year")
        dataset = self.dataset("ds_mix", draft, embargoed)
        dataset.topics.add(self.energy)

        check = dataset_actions.preflight(
            self.creator, dataset_actions.PUBLISH, ["ds_mix"]
        )
        self.assertEqual(
            {
                key: check.consequences[key]
                for key in ("members", "drafts", "embargoed")
            },
            {"members": 2, "drafts": 1, "embargoed": 1},
        )
        self.assertEqual(check.left_out, [])

        response = self.publish("ds_mix")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(self.row(dataset).published_at)

    def test_a_published_dataset_that_stops_passing_stays_published(self):
        member = self.table("t_leaves")
        dataset = self.dataset("ds_stays", member, published=True)
        self.unassign("ds_stays", "t_leaves")
        self.assertTrue(self.row(dataset).is_published)


class TransitionTests(DatasetWriteTestCase):
    def publishable(self, name, published=False):
        dataset = self.dataset(name, self.table(f"t_{name}"), published=published)
        dataset.topics.add(self.energy)
        return dataset

    def test_a_republish_overwrites_published_at(self):
        dataset = self.publishable("ds_republish", published=True)
        Dataset.objects.filter(pk=dataset.pk).update(published_at=EARLIER)
        response = self.publish("ds_republish")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(self.row(dataset).published_at, EARLIER)

    def test_a_republish_runs_the_gate_again(self):
        dataset = self.dataset("ds_republish_bare", published=True)
        Dataset.objects.filter(pk=dataset.pk).update(published_at=EARLIER)
        response = self.publish("ds_republish_bare")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.row(dataset).published_at, EARLIER)

    def test_unpublishing_a_draft_is_a_200_that_writes_nothing(self):
        dataset = self.dataset("ds_already_draft")
        before = Dataset.objects.filter(pk=dataset.pk).values().get()
        with self.assertNoLogs(LOGGER, "INFO"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.unpublish("ds_already_draft")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.json()["published_at"])
        self.assertEqual(Dataset.objects.filter(pk=dataset.pk).values().get(), before)

    def test_unpublish_clears_published_at_and_answers_the_body(self):
        dataset = self.publishable("ds_back_to_draft", published=True)
        response = self.unpublish("ds_back_to_draft")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.json()["published_at"])
        self.assertIsNone(self.row(dataset).published_at)

    def test_neither_moves_modified_at(self):
        dataset = self.publishable("ds_unstamped")
        self.assertEqual(self.publish("ds_unstamped").status_code, 200)
        self.assertEqual(self.unpublish("ds_unstamped").status_code, 200)
        self.assertEqual(self.modified(dataset), LONG_AGO)

    def test_each_logs_one_line_via_api(self):
        self.publishable("ds_logged")
        lines = []
        for call in (self.publish, self.publish, self.unpublish):
            with self.assertLogs(LOGGER, "INFO") as logged:
                with self.captureOnCommitCallbacks(execute=True):
                    call("ds_logged")
            lines += [record.getMessage() for record in logged.records]
        by = f"by={self.creator.pk} via=api batch=-"
        self.assertEqual(
            lines,
            [
                f"dataset_action dataset=ds_logged action=publish republish=no {by}",
                f"dataset_action dataset=ds_logged action=publish republish=yes {by}",
                f"dataset_action dataset=ds_logged action=unpublish {by}",
            ],
        )

    def test_a_body_is_ignored(self):
        self.publishable("ds_with_body")
        response = self.client.post(
            "/api/v0/datasets/ds_with_body/publish/",
            {"published_at": None},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.json()["published_at"])


class PreflightQueryTests(DatasetWriteTestCase):
    """What a preflight of the new actions costs: publish one query for the
    Datasets, two per own Dataset (the gate's EXISTS) and one for the member
    mix; unpublish one; edit two (the Dataset, its Topics), three when Topics
    are given (their validation); create two (the name, the Topics)."""

    def test_the_budgets(self):
        ready = self.dataset("ds_budget", self.table("t_budget"))
        ready.topics.add(self.energy)
        cases = (
            (4, dataset_actions.PUBLISH, ["ds_budget"], {}),
            (1, dataset_actions.UNPUBLISH, ["ds_budget"], {}),
            (2, dataset_actions.EDIT, ["ds_budget"], {"title": "New"}),
            (3, dataset_actions.EDIT, ["ds_budget"], {"topics": ["writes_energy"]}),
            (
                2,
                dataset_actions.CREATE,
                ["ds_budget_new"],
                {"title": "T", "description": "D", "topics": ["writes_energy"]},
            ),
        )
        for queries, action, names, params in cases:
            with self.subTest(action=action, params=params):
                with self.assertNumQueries(queries):
                    dataset_actions.preflight(self.creator, action, names, params)
