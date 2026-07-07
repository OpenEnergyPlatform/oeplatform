"""
Characterization (safety-net) tests for the Open Peer Review model logic.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Companion to ``test_peer_review_helpers.py``. These pin the CURRENT behavior of
the turn-taking / status logic on ``PeerReview`` and ``PeerReviewManager`` so the
planned refactor has a tripwire (Obsidian: "07 - Pain Points & Refactoring Plan",
Phase 0). They are DB-backed (``TestCase``) but deliberately avoid creating a real
OEDB table: only ``PeerReview.save(review_type="submit"/"finished")`` reaches
``Table.load`` via ``set_version_of_metadata_for_review``; the turn-taking itself
is exercised through ``update()`` and the manager methods, which need no table.

As characterization tests they document what the code does TODAY, quirks and all.
Surprising behavior is named/commented as such instead of asserting the "ideal".
"""  # noqa: E501

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from dataedit.models import (
    PeerReview,
    PeerReviewManager,
    ReviewDataStatus,
    Reviewer,
)
from login.models import myuser as User


class _OprTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reviewer = User.objects.create_user(
            name="opr_reviewer", email="opr_reviewer@test.test", affiliation="t"
        )
        cls.contributor = User.objects.create_user(
            name="opr_contributor", email="opr_contributor@test.test", affiliation="t"
        )

    def _make_opr(self, table="t_turn", review_type=None, **kwargs):
        """Create a saved PeerReview with distinct reviewer/contributor.

        With ``review_type=None`` this hits the plain ``super().save()`` path
        (no PeerReviewManager is created).
        """
        opr = PeerReview(
            table=table,
            reviewer=self.reviewer,
            contributor=self.contributor,
            review={},
            oemetadata={},
            **kwargs,
        )
        opr.save(review_type=review_type)
        return opr


class TestPeerReviewManagerTurnTaking(_OprTestBase):
    def test_default_current_reviewer_is_reviewer(self):
        opr = self._make_opr()
        pm = PeerReviewManager.objects.create(opr=opr)
        self.assertEqual(pm.current_reviewer, Reviewer.REVIEWER.value)
        self.assertEqual(pm.current_reviewer, "reviewer")

    def test_set_next_reviewer_toggles_back_and_forth(self):
        opr = self._make_opr()
        pm = PeerReviewManager.objects.create(opr=opr)

        pm.set_next_reviewer()
        self.assertEqual(pm.current_reviewer, Reviewer.CONTRIBUTOR.value)

        pm.set_next_reviewer()
        self.assertEqual(pm.current_reviewer, Reviewer.REVIEWER.value)

        # persisted (set_next_reviewer calls save())
        pm.refresh_from_db()
        self.assertEqual(pm.current_reviewer, Reviewer.REVIEWER.value)

    def test_whos_turn_maps_role_to_the_right_user(self):
        opr = self._make_opr()
        pm = PeerReviewManager.objects.create(opr=opr)

        role, user = pm.whos_turn()
        self.assertEqual(role, Reviewer.REVIEWER.value)
        self.assertEqual(user, self.reviewer)

        pm.set_next_reviewer()
        role, user = pm.whos_turn()
        self.assertEqual(role, Reviewer.CONTRIBUTOR.value)
        self.assertEqual(user, self.contributor)

    def test_is_open_since_is_set_from_days_open_on_first_save(self):
        opr = self._make_opr(
            table="t_open_since",
            date_started=timezone.now() - timedelta(days=3),
        )
        pm = PeerReviewManager.objects.create(opr=opr)
        # stored as a string of the day count
        self.assertEqual(pm.is_open_since, "3")


class TestPeerReviewSaveUpdate(_OprTestBase):
    def test_save_with_type_save_creates_manager_with_status_saved(self):
        opr = self._make_opr(table="t_save", review_type="save")
        pm = PeerReviewManager.objects.get(opr=opr)
        self.assertEqual(pm.status, ReviewDataStatus.SAVED.value)
        # turn starts on the reviewer
        self.assertEqual(pm.current_reviewer, Reviewer.REVIEWER.value)

    def test_save_keeps_exactly_one_manager_per_review(self):
        # Regression for the former duplicate-manager bug: PeerReview.save()
        # used to create a NEW PeerReviewManager on every call (two saves -> two
        # managers -> PeerReviewManager.load raised MultipleObjectsReturned).
        # It now uses get_or_create, so a review keeps exactly one manager and
        # PeerReviewManager.load works.
        opr = self._make_opr(table="t_dup", review_type="save")
        opr.save(review_type="save")
        self.assertEqual(PeerReviewManager.objects.filter(opr=opr).count(), 1)
        # the canonical loader no longer raises
        self.assertEqual(
            PeerReviewManager.load(opr=opr).status, ReviewDataStatus.SAVED.value
        )

    def test_save_raises_when_contributor_equals_reviewer(self):
        opr = PeerReview(
            table="t_same",
            reviewer=self.reviewer,
            contributor=self.reviewer,
            review={},
            oemetadata={},
        )
        with self.assertRaises(ValidationError):
            opr.save(review_type="save")

    def test_update_raises_when_contributor_equals_reviewer(self):
        # guard is checked before any manager lookup, so an unsaved opr is fine
        opr = PeerReview(
            table="t_same2",
            reviewer=self.reviewer,
            contributor=self.reviewer,
            review={},
            oemetadata={},
        )
        with self.assertRaises(ValidationError):
            opr.update(review_type="submit")

    def test_update_submit_sets_submitted_and_toggles_turn_to_contributor(self):
        opr = self._make_opr(table="t_submit", review_type="save")
        opr.update(review_type="submit")

        pm = PeerReviewManager.objects.get(opr=opr)
        self.assertEqual(pm.status, ReviewDataStatus.SUBMITTED.value)
        self.assertEqual(pm.current_reviewer, Reviewer.CONTRIBUTOR.value)

    def test_update_finished_marks_finished_and_does_not_toggle_turn(self):
        opr = self._make_opr(table="t_finish", review_type="save")
        opr.update(review_type="finished")

        opr.refresh_from_db()
        pm = PeerReviewManager.objects.get(opr=opr)
        self.assertTrue(opr.is_finished)
        self.assertIsNotNone(opr.date_finished)
        self.assertEqual(pm.status, ReviewDataStatus.FINISHED.value)
        # CHARACTERIZATION: finishing does NOT call set_next_reviewer, so the
        # turn stays where it was.
        self.assertEqual(pm.current_reviewer, Reviewer.REVIEWER.value)


class TestPeerReviewLoadAndDaysOpen(_OprTestBase):
    def test_load_returns_latest_by_date_started(self):
        older = self._make_opr(
            table="t_load",
            date_started=timezone.now() - timedelta(days=2),
        )
        newer = self._make_opr(
            table="t_load",
            date_started=timezone.now(),
        )

        loaded = PeerReview.load(table="t_load")
        self.assertEqual(loaded.pk, newer.pk)
        self.assertNotEqual(loaded.pk, older.pk)

    def test_load_returns_none_for_unknown_table(self):
        self.assertIsNone(PeerReview.load(table="no_such_table"))

    def test_days_open_counts_from_date_started_when_open(self):
        opr = self._make_opr(
            table="t_days",
            date_started=timezone.now() - timedelta(days=5),
        )
        self.assertEqual(opr.days_open, 5)

    def test_days_open_uses_date_finished_when_finished(self):
        start = timezone.now() - timedelta(days=10)
        opr = self._make_opr(table="t_days2", date_started=start)
        opr.date_finished = start + timedelta(days=4)
        opr.save()
        self.assertEqual(opr.days_open, 4)
