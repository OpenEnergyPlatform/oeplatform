"""
Tests for ReviewService (Phase 2, step S2).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

S2 extracted the view POST branching into ``ReviewService`` 1:1
(behavior-preserving). The contributor path is OEDB-free (it only touches
get_opr_by_id / merge_field_reviews / update), so it can be tested with plain ORM
rows. The reviewer path reaches the live OEDB (Table.load / load_metadata_from_db)
and is left to the existing end-to-end view tests.
"""  # noqa: E501

from django.test import TestCase

from dataedit.models import (
    PeerReview,
    PeerReviewManager,
    ReviewDataStatus,
    Reviewer,
)
from dataedit.peer_review.service import ReviewService
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
        opr = PeerReview(
            table="t_service",
            reviewer=self.reviewer,
            contributor=self.contributor,
            review={
                "reviews": [
                    {
                        "key": "title",
                        "category": "general",
                        "fieldReview": {"role": "reviewer", "state": "suggestion"},
                    }
                ]
            },
            oemetadata={},
        )
        opr.save()  # plain save, no manager created
        PeerReviewManager.objects.create(
            opr=opr,
            status=ReviewDataStatus.SUBMITTED.value,
            current_reviewer=Reviewer.CONTRIBUTOR.value,
        )
        return opr

    def test_contributor_submit_merges_review_and_toggles_turn(self):
        opr = self._opr_with_reviewer_round()
        payload = {
            "reviewType": "submit",
            "reviewData": {
                "reviews": [
                    {
                        "key": "title",
                        "category": "general",
                        "fieldReview": {"role": "contributor", "state": "ok"},
                    }
                ]
            },
        }

        ReviewService(
            table_name="t_service", actor=self.contributor
        ).submit_contributor_review(payload, review_id=opr.id)

        opr.refresh_from_db()
        field_review = opr.review["reviews"][0]["fieldReview"]
        # merge_field_reviews puts the incoming (contributor) entry first, then
        # the existing (reviewer) entry — fieldReview becomes a list.
        self.assertEqual(
            field_review,
            [
                {"role": "contributor", "state": "ok"},
                {"role": "reviewer", "state": "suggestion"},
            ],
        )

        pm = PeerReviewManager.objects.get(opr=opr)
        self.assertEqual(pm.status, ReviewDataStatus.SUBMITTED.value)
        # submit toggles the turn back to the reviewer
        self.assertEqual(pm.current_reviewer, Reviewer.REVIEWER.value)

    def test_contributor_save_sets_saved_without_toggling_turn(self):
        opr = self._opr_with_reviewer_round()
        payload = {
            "reviewType": "save",
            "reviewData": {"reviews": []},
        }

        ReviewService(
            table_name="t_service", actor=self.contributor
        ).submit_contributor_review(payload, review_id=opr.id)

        pm = PeerReviewManager.objects.get(opr=opr)
        self.assertEqual(pm.status, ReviewDataStatus.SAVED.value)
        # a draft save does not change whose turn it is
        self.assertEqual(pm.current_reviewer, Reviewer.CONTRIBUTOR.value)
