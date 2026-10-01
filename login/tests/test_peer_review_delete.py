"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

from django.test import TestCase
from django.urls import reverse

from dataedit.models import PeerReview, Table
from login.models import myuser


class PeerReviewDeleteTests(TestCase):
    """Only a peer review's reviewer may delete it.

    The delete button is rendered for the reviewer alone: on the profile's
    reviews page inside the "Participating as Reviewer" block, and on the
    reviewer's review page (``dataedit/opr_review.html``). Both entry points
    share ``dataedit.helper.delete_peer_review``.
    """

    @classmethod
    def setUpTestData(cls):
        cls.reviewer = myuser.objects.create_user(
            name="ReviewDeleteReviewer",
            email="review-delete-reviewer@test.test",
            affiliation="test",
        )
        cls.contributor = myuser.objects.create_user(
            name="ReviewDeleteContributor",
            email="review-delete-contributor@test.test",
            affiliation="test",
        )
        cls.stranger = myuser.objects.create_user(
            name="ReviewDeleteStranger",
            email="review-delete-stranger@test.test",
            affiliation="test",
        )
        cls.table = Table.objects.create(name="review_delete_table")

    def setUp(self):
        self.review = PeerReview.objects.create(
            table=self.table.name,
            reviewer=self.reviewer,
            contributor=self.contributor,
            review={},
        )

    def delete_from_profile(self, review_id):
        return self.client.post(
            reverse("login:delete_peer_review_simple"),
            data=json.dumps({"review_id": review_id}),
            content_type="application/json",
        )

    def delete_from_review_page(self):
        return self.client.post(
            reverse(
                "dataedit:peer_review_reviewer",
                kwargs={"table": self.table.name, "review_id": self.review.pk},
            ),
            data=json.dumps({"reviewType": "delete", "reviewData": {}}),
            content_type="application/json",
        )

    def review_exists(self):
        return PeerReview.objects.filter(pk=self.review.pk).exists()

    def test_the_reviewer_deletes_their_review(self):
        self.client.force_login(self.reviewer)

        response = self.delete_from_profile(self.review.pk)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.review_exists())

    def test_another_user_is_refused(self):
        self.client.force_login(self.stranger)

        response = self.delete_from_profile(self.review.pk)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.review_exists())

    def test_the_contributor_is_refused(self):
        self.client.force_login(self.contributor)

        response = self.delete_from_profile(self.review.pk)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.review_exists())

    def test_an_anonymous_caller_is_refused(self):
        response = self.delete_from_profile(self.review.pk)

        self.assertEqual(response.status_code, 401)
        self.assertTrue(self.review_exists())

    def test_an_unknown_id_is_not_found(self):
        self.client.force_login(self.reviewer)

        response = self.delete_from_profile(self.review.pk + 1000)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.review_exists())

    def test_a_missing_id_is_a_bad_request(self):
        self.client.force_login(self.reviewer)

        response = self.delete_from_profile(None)

        self.assertEqual(response.status_code, 400)
        self.assertTrue(self.review_exists())

    def test_the_review_page_lets_the_reviewer_delete(self):
        self.client.force_login(self.reviewer)

        response = self.delete_from_review_page()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.review_exists())

    def test_the_review_page_refuses_another_user(self):
        self.client.force_login(self.stranger)

        response = self.delete_from_review_page()

        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.review_exists())
