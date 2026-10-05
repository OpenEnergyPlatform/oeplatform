"""
Finishing a peer review writes the live metadata through the one metadata write
path (issue #2552).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Driven through the review endpoints; asserts what a reader of the platform sees
afterwards (the displayed title, the search) and what is stored, never which
helper ran.
"""  # noqa: E501

import json
from copy import deepcopy

from django.test import TestCase
from django.urls import reverse
from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from api.actions import set_table_metadata
from dataedit.helper import find_tables
from dataedit.models import (
    PeerReview,
    PeerReviewManager,
    ReviewDataStatus,
    Reviewer,
    ReviewRound,
    Table,
)
from dataedit.peer_review.projection import project_review
from login.models import UserPermission
from login.models import myuser as User
from login.permissions import ADMIN_PERM

TABLE = "opr_finish_table"


def field(key, new_value=None, state="ok", role="reviewer"):
    review = {"state": state, "role": role, "timestamp": 1}
    if new_value is not None:
        review["newValue"] = new_value
    return {"key": key, "category": "general", "fieldReview": review}


class PeerReviewFinishTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reviewer = User.objects.create_user(
            name="finish_reviewer", email="finish_reviewer@test.test", affiliation="t"
        )
        cls.contributor = User.objects.create_user(
            name="finish_contributor",
            email="finish_contributor@test.test",
            affiliation="t",
        )
        cls.table = Table.objects.create(name=TABLE)
        UserPermission.objects.create(
            table=cls.table, holder=cls.contributor, level=ADMIN_PERM
        )

        metadata = deepcopy(OEMETADATA_V20_EXAMPLE)
        resource = metadata["resources"][0]
        resource["title"] = "Zebrafinch census"
        resource["description"] = "Annual counts of the zebrafinch population"
        # The starting state comes through the same path, so title and search
        # already describe it before the review changes anything.
        set_table_metadata(table=TABLE, metadata=metadata)

    def table_now(self) -> Table:
        return Table.objects.get(name=TABLE)

    def found_by(self, word) -> bool:
        return find_tables(query_string=word).filter(name=TABLE).exists()

    def finish_as_reviewer(self, reviews, badge="Gold"):
        return self.client.post(
            reverse("dataedit:peer_review_create", kwargs={"table": TABLE}),
            data=json.dumps(
                {
                    "reviewType": "finished",
                    "reviewData": {"reviewFinished": True, "reviews": reviews},
                    "reviewBadge": badge,
                }
            ),
            content_type="application/json",
        )


class SuccessfulFinishTest(PeerReviewFinishTestCase):
    def setUp(self):
        self.client.force_login(self.reviewer)
        response = self.finish_as_reviewer(
            [
                field("resources.0.title", "Kingfisher census"),
                field(
                    "resources.0.description",
                    "Annual counts of the kingfisher population",
                ),
            ]
        )
        self.assertEqual(response.status_code, 200, response.content)

    def test_the_displayed_title_follows_the_accepted_title(self):
        self.assertEqual(
            self.table_now().human_readable_name, f"Kingfisher census ({TABLE})"
        )

    def test_the_search_finds_a_new_word_and_no_longer_a_removed_one(self):
        self.assertTrue(self.found_by("kingfisher"))
        self.assertFalse(self.found_by("zebrafinch"))

    def test_the_live_metadata_carries_the_accepted_values_and_the_badge(self):
        resource = self.table_now().oemetadata["resources"][0]
        self.assertEqual(resource["title"], "Kingfisher census")
        self.assertEqual(self.table_now().oemetadata["review"]["badge"], "Gold")

    def test_the_table_is_marked_reviewed(self):
        self.assertTrue(self.table_now().is_reviewed)

    def test_the_review_is_finished_with_its_snapshot_and_badge(self):
        review = PeerReview.objects.get(table=TABLE)
        self.assertTrue(review.is_finished)
        self.assertEqual(
            review.oemetadata["resources"][0]["title"], "Kingfisher census"
        )
        self.assertEqual(review.oemetadata["review"]["badge"], "Gold")
        self.assertEqual(review.review["badge"], "Gold")
        self.assertEqual(review.review["grantedBadge"], "Gold")


class RefusedFinishTest(PeerReviewFinishTestCase):
    """A merge that fails validation writes nothing and says why."""

    @staticmethod
    def invalid(role):
        """A merge omi refuses: keywords must be an array."""
        return [field("resources.0.keywords", "not a list", role=role)]

    def setUp(self):
        self.metadata_before = self.table_now().oemetadata

    def assert_table_untouched(self):
        table = self.table_now()
        self.assertEqual(table.oemetadata, self.metadata_before)
        self.assertNotIn("review", table.oemetadata)
        self.assertEqual(table.human_readable_name, f"Zebrafinch census ({TABLE})")
        self.assertFalse(table.is_reviewed)
        self.assertTrue(self.found_by("zebrafinch"))

    def assert_readable_refusal(self, response):
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertIn("cannot be finished", error)
        self.assertIn("is not of type 'array'", error)

    def ongoing_review(self):
        """A review the reviewer submitted and the contributor now answers."""
        review = PeerReview.objects.create(
            table=TABLE,
            reviewer=self.reviewer,
            contributor=self.contributor,
            review={},
            oemetadata=deepcopy(self.metadata_before),
        )
        entry = field("resources.0.keywords", state="suggestion")
        ReviewRound.objects.create(
            opr=review,
            sequence=1,
            role=Reviewer.REVIEWER.value,
            actor=self.reviewer,
            action=ReviewDataStatus.SUBMITTED.value,
            field_reviews=[entry],
            sets_finished=False,
        )
        review.review = project_review({}, [{"sequence": 1, "field_reviews": [entry]}])
        review.save()
        PeerReviewManager.objects.create(
            opr=review,
            status=ReviewDataStatus.SUBMITTED.value,
            current_reviewer=Reviewer.CONTRIBUTOR.value,
        )
        return review

    def test_a_contributor_finish_leaves_the_review_where_it_was(self):
        review = self.ongoing_review()
        review_before = deepcopy(review.review)
        self.client.force_login(self.contributor)

        response = self.client.post(
            reverse(
                "dataedit:peer_review_contributor",
                kwargs={"table": TABLE, "review_id": review.pk},
            ),
            data=json.dumps(
                {
                    "reviewType": "finished",
                    "reviewData": {
                        "reviewFinished": True,
                        "reviews": self.invalid("contributor"),
                    },
                }
            ),
            content_type="application/json",
        )

        self.assert_readable_refusal(response)
        self.assert_table_untouched()
        review.refresh_from_db()
        self.assertFalse(review.is_finished)
        self.assertIsNone(review.date_finished)
        self.assertEqual(review.review, review_before)
        self.assertEqual(review.oemetadata, self.metadata_before)
        self.assertEqual(ReviewRound.objects.filter(opr=review).count(), 1)
        self.assertEqual(
            PeerReviewManager.objects.get(opr=review).status,
            ReviewDataStatus.SUBMITTED.value,
        )

    def test_a_reviewer_finish_in_one_go_leaves_no_review_behind(self):
        self.client.force_login(self.reviewer)

        response = self.finish_as_reviewer(self.invalid("reviewer"))

        self.assert_readable_refusal(response)
        self.assert_table_untouched()
        self.assertFalse(PeerReview.objects.filter(table=TABLE).exists())
        self.assertFalse(ReviewRound.objects.exists())
