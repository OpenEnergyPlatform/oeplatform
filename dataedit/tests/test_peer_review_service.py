"""
Tests for ReviewService (Phase 2 S3/S4 — rounds + projection).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The contributor path is OEDB-free (get_opr_by_id / round write / projection /
update), so it is tested here with plain ORM rows. The reviewer create + finish
paths reach the live OEDB (Table.load / load_metadata_from_db / save_metadata_to_db)
and are validated by running the app, not here.
"""  # noqa: E501

from django.test import TestCase

from dataedit.models import (
    PeerReview,
    PeerReviewManager,
    ReviewDataStatus,
    Reviewer,
    ReviewRound,
)
from dataedit.peer_review.projection import project_review
from dataedit.peer_review.service import ReviewFinishedError, ReviewService
from login.models import myuser as User


class TestReviewServiceContributor(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reviewer = User.objects.create_user(
            name="svc_reviewer", email="svc_reviewer@test.test", affiliation="t"
        )
        cls.contributor = User.objects.create_user(
            name="svc_contributor", email="svc_contributor@test.test", affiliation="t"
        )

    def _opr_with_reviewer_round(self):
        """An opr that already has one reviewer round (the realistic state when a
        contributor is about to reply)."""
        opr = PeerReview(
            table="t_service",
            reviewer=self.reviewer,
            contributor=self.contributor,
            review={},
            oemetadata={},
        )
        opr.save()  # plain save, no manager

        reviewer_entry = {
            "key": "title",
            "category": "general",
            "fieldReview": {"state": "suggestion", "role": "reviewer", "timestamp": 1},
        }
        ReviewRound.objects.create(
            opr=opr,
            sequence=1,
            role=Reviewer.REVIEWER.value,
            actor=self.reviewer,
            action=ReviewDataStatus.SUBMITTED.value,
            field_reviews=[reviewer_entry],
            sets_finished=False,
        )
        opr.review = project_review(
            {}, [{"sequence": 1, "field_reviews": [reviewer_entry]}]
        )
        opr.save()

        PeerReviewManager.objects.create(
            opr=opr,
            status=ReviewDataStatus.SUBMITTED.value,
            current_reviewer=Reviewer.CONTRIBUTOR.value,
        )
        return opr

    def _contributor_payload(self, review_type="submit"):
        return {
            "reviewType": review_type,
            "reviewData": {
                "reviews": [
                    {
                        "key": "title",
                        "category": "general",
                        "fieldReview": {
                            "state": "ok",
                            "role": "contributor",
                            "timestamp": 2,
                        },
                    }
                ]
            },
        }

    def test_contributor_submit_records_round_and_projects_history(self):
        opr = self._opr_with_reviewer_round()

        ReviewService(
            table_name="t_service", actor=self.contributor
        ).submit_contributor_review(self._contributor_payload(), review_id=opr.id)

        # a second (contributor) round was appended
        rounds = list(ReviewRound.objects.filter(opr=opr).order_by("sequence"))
        self.assertEqual(len(rounds), 2)
        self.assertEqual(rounds[1].role, Reviewer.CONTRIBUTOR.value)
        self.assertEqual(rounds[1].sequence, 2)
        # only this turn's delta is stored on the round
        self.assertEqual(len(rounds[1].field_reviews), 1)
        self.assertEqual(
            rounds[1].field_reviews[0]["fieldReview"]["role"], "contributor"
        )

        # the projection holds both turns as a list, in sequence order
        opr.refresh_from_db()
        field_review = opr.review["reviews"][0]["fieldReview"]
        self.assertEqual(
            [fr["role"] for fr in field_review], ["reviewer", "contributor"]
        )

        pm = PeerReviewManager.objects.get(opr=opr)
        self.assertEqual(pm.status, ReviewDataStatus.SUBMITTED.value)
        # submit toggles the turn back to the reviewer
        self.assertEqual(pm.current_reviewer, Reviewer.REVIEWER.value)

    def test_re_sent_reviewer_entry_is_not_duplicated(self):
        opr = self._opr_with_reviewer_round()
        # contributor client echoes the reviewer's prior entry plus its own
        payload = self._contributor_payload()
        payload["reviewData"]["reviews"].insert(
            0,
            {
                "key": "title",
                "category": "general",
                "fieldReview": {
                    "state": "suggestion",
                    "role": "reviewer",
                    "timestamp": 1,
                },
            },
        )

        ReviewService(
            table_name="t_service", actor=self.contributor
        ).submit_contributor_review(payload, review_id=opr.id)

        # the echoed reviewer entry was already in round 1 -> delta is just the
        # contributor's new contribution
        round2 = ReviewRound.objects.get(opr=opr, sequence=2)
        self.assertEqual(len(round2.field_reviews), 1)
        self.assertEqual(round2.field_reviews[0]["fieldReview"]["role"], "contributor")

    def test_contributor_save_is_a_draft_without_a_round(self):
        opr = self._opr_with_reviewer_round()

        ReviewService(
            table_name="t_service", actor=self.contributor
        ).submit_contributor_review(
            self._contributor_payload(review_type="save"), review_id=opr.id
        )

        # no new round for a draft
        self.assertEqual(ReviewRound.objects.filter(opr=opr).count(), 1)
        pm = PeerReviewManager.objects.get(opr=opr)
        self.assertEqual(pm.status, ReviewDataStatus.SAVED.value)
        # a draft save does not change whose turn it is
        self.assertEqual(pm.current_reviewer, Reviewer.CONTRIBUTOR.value)

    def test_submit_to_a_finished_review_is_rejected(self):
        opr = self._opr_with_reviewer_round()
        opr.is_finished = True
        opr.save()

        with self.assertRaises(ReviewFinishedError):
            ReviewService(
                table_name="t_service", actor=self.contributor
            ).submit_contributor_review(self._contributor_payload(), review_id=opr.id)
