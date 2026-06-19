"""
Tests for the swappable BadgeService (Phase 2 S5).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The badge *policy* is expected to change, so these tests lock the seam (strategy
swap, reviewer override, normalization, persistence) and the current default
strategy's behavior — pure, so a fast ``SimpleTestCase``.
"""  # noqa: E501

from django.test import SimpleTestCase

from dataedit.peer_review.badges import (
    BadgeService,
    apply_badge_to_metadata,
    apply_badge_to_review,
    cumulative_tier_strategy,
    field_is_present,
    is_filled,
    normalize_badge,
)
from dataedit.utils import PeerReviewBadge

# A small fake schema in the shape get_all_field_descriptions expects.
FAKE_SCHEMA = {
    "properties": {
        "name": {"badge": "Bronze"},
        "title": {"badge": "Bronze"},
        "spatial": {"properties": {"location": {"badge": "Silver"}}},
        "resources": {"items": {"properties": {"description": {"badge": "Gold"}}}},
    }
}


class TestNormalizeBadge(SimpleTestCase):
    def test_maps_known_labels_any_case(self):
        self.assertEqual(normalize_badge("Platinum"), PeerReviewBadge.PLATINUM)
        self.assertEqual(normalize_badge("bronze"), PeerReviewBadge.BRONZE)
        self.assertEqual(normalize_badge("GOLD"), PeerReviewBadge.GOLD)

    def test_maps_ui_platin_alias(self):
        self.assertEqual(normalize_badge("platin"), PeerReviewBadge.PLATINUM)

    def test_unknown_or_empty_is_none(self):
        self.assertIsNone(normalize_badge("titanium"))
        self.assertIsNone(normalize_badge(""))
        self.assertIsNone(normalize_badge(None))


class TestIsFilled(SimpleTestCase):
    def test_empty_values(self):
        for v in [None, "", "None", "null", "[]", "{}", [], {}]:
            self.assertFalse(is_filled(v), v)

    def test_present_values(self):
        for v in ["x", 0, 123, ["a"], {"k": "v"}, False]:
            self.assertTrue(is_filled(v), v)


class TestFieldResolution(SimpleTestCase):
    def test_descends_into_first_list_element(self):
        md = {"resources": [{"description": "hello"}]}
        self.assertTrue(field_is_present(md, "resources.description"))

    def test_missing_path_is_absent(self):
        self.assertFalse(field_is_present({"resources": [{}]}, "resources.description"))
        self.assertFalse(field_is_present({}, "name"))


class TestCumulativeTierStrategy(SimpleTestCase):
    def test_iron_when_bronze_incomplete(self):
        md = {"name": "n"}  # title missing
        self.assertEqual(
            cumulative_tier_strategy(md, FAKE_SCHEMA), PeerReviewBadge.IRON
        )

    def test_bronze_when_only_bronze_complete(self):
        md = {"name": "n", "title": "t"}
        self.assertEqual(
            cumulative_tier_strategy(md, FAKE_SCHEMA), PeerReviewBadge.BRONZE
        )

    def test_silver_then_gold_cumulative(self):
        silver = {"name": "n", "title": "t", "spatial": {"location": "DE"}}
        self.assertEqual(
            cumulative_tier_strategy(silver, FAKE_SCHEMA), PeerReviewBadge.SILVER
        )

        gold = dict(silver, resources=[{"description": "d"}])
        self.assertEqual(
            cumulative_tier_strategy(gold, FAKE_SCHEMA), PeerReviewBadge.GOLD
        )

    def test_gap_stops_progression(self):
        # bronze ok, silver missing, gold present -> capped at bronze
        md = {"name": "n", "title": "t", "resources": [{"description": "d"}]}
        self.assertEqual(
            cumulative_tier_strategy(md, FAKE_SCHEMA), PeerReviewBadge.BRONZE
        )

    def test_empty_top_tier_is_not_auto_awarded(self):
        # FAKE_SCHEMA declares no Platinum fields -> never reaches Platinum
        full = {
            "name": "n",
            "title": "t",
            "spatial": {"location": "DE"},
            "resources": [{"description": "d"}],
        }
        self.assertEqual(
            cumulative_tier_strategy(full, FAKE_SCHEMA), PeerReviewBadge.GOLD
        )


class TestBadgeService(SimpleTestCase):
    def test_reviewer_choice_overrides_suggestion(self):
        # metadata would auto-suggest IRON, but the reviewer picked gold
        svc = BadgeService()
        badge = svc.resolve_final_badge(
            {"name": "n"}, reviewer_choice="gold", schema=FAKE_SCHEMA
        )
        self.assertEqual(badge, PeerReviewBadge.GOLD)

    def test_falls_back_to_suggestion_without_choice(self):
        svc = BadgeService()
        badge = svc.resolve_final_badge(
            {"name": "n", "title": "t"}, reviewer_choice=None, schema=FAKE_SCHEMA
        )
        self.assertEqual(badge, PeerReviewBadge.BRONZE)

    def test_strategy_is_swappable(self):
        def always_platinum(metadata, schema):
            return PeerReviewBadge.PLATINUM

        svc = BadgeService(strategy=always_platinum)
        self.assertEqual(svc.suggest_badge({}, FAKE_SCHEMA), PeerReviewBadge.PLATINUM)

    def test_apply_badge_to_metadata_writes_review_badge(self):
        md = {}
        apply_badge_to_metadata(md, PeerReviewBadge.SILVER)
        self.assertEqual(md["review"]["badge"], "Silver")

    def test_apply_badge_to_review_sets_badge_and_granted_badge(self):
        # the dataview card reads PeerReview.review["badge"]
        review = {"reviews": []}
        apply_badge_to_review(review, PeerReviewBadge.GOLD)
        self.assertEqual(review["badge"], "Gold")
        self.assertEqual(review["grantedBadge"], "Gold")

    def test_apply_badge_to_review_tolerates_none(self):
        result = apply_badge_to_review(None, PeerReviewBadge.BRONZE)
        self.assertEqual(result["badge"], "Bronze")
