"""
Tests for the swappable BadgeService (Phase 2 S5) – extended

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Complete test coverage for dataedit.peer_review.badges
on branch feature-1232-badges-in-opr
"""  # noqa

from django.test import SimpleTestCase

from dataedit.peer_review.badges import (
    BadgeService,
    _last_field_review_state,
    _resolve_path,
    apply_badge_to_metadata,
    apply_badge_to_review,
    badge_label,
    cumulative_tier_strategy,
    extract_field_states,
    extract_ok_fields,
    field_is_present,
    fields_by_tier,
    is_filled,
    normalize_badge,
    normalize_review_key,
    review_based_cumulative_tier_strategy,
    review_based_cumulative_tier_strategy_details,
)
from dataedit.utils import PeerReviewBadge

# A small fake schema in the shape get_all_field_descriptions expects,
# with explicit Iron fields
FAKE_SCHEMA = {
    "properties": {
        "id": {"badge": "Iron"},
        "context": {"properties": {"homepage": {"badge": "Iron"}}},
        "name": {"badge": "Bronze"},
        "title": {"badge": "Bronze"},
        "spatial": {"properties": {"location": {"badge": "Silver"}}},
        "resources": {
            "items": {
                "properties": {
                    "description": {"badge": "Gold"},
                    "path": {"badge": "Platinum"},
                }
            }
        },
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


class TestResolvePath(SimpleTestCase):
    """_resolve_path is the tolerant dotted-path lookup used by field_is_present."""

    def test_resolves_simple_dotted_path(self):
        md = {"spatial": {"location": "Berlin"}}
        self.assertEqual(_resolve_path(md, "spatial.location"), "Berlin")

    def test_descends_into_first_list_element(self):
        md = {"resources": [{"description": "hello"}, {"description": "bye"}]}
        self.assertEqual(_resolve_path(md, "resources.description"), "hello")

    def test_missing_intermediate_returns_none(self):
        self.assertIsNone(_resolve_path({}, "a.b"))
        self.assertIsNone(_resolve_path({"a": {}}, "a.b"))
        self.assertIsNone(_resolve_path({"resources": []}, "resources.title"))

    def test_single_element_list_is_unwrapped(self):
        md = {"x": ["only"]}
        self.assertEqual(_resolve_path(md, "x"), "only")


class TestFieldResolution(SimpleTestCase):
    def test_descends_into_first_list_element(self):
        md = {"resources": [{"description": "hello"}]}
        self.assertTrue(field_is_present(md, "resources.description"))

    def test_missing_path_is_absent(self):
        self.assertFalse(field_is_present({"resources": [{}]}, "resources.description"))
        self.assertFalse(field_is_present({}, "name"))


class TestFieldsByTier(SimpleTestCase):
    def test_groups_by_declared_badge(self):
        tiers = fields_by_tier(FAKE_SCHEMA)
        # fields_by_tier only includes BRONZE, SILVER, GOLD, PLATINUM
        self.assertCountEqual(tiers[PeerReviewBadge.BRONZE], ["name", "title"])
        self.assertCountEqual(tiers[PeerReviewBadge.SILVER], ["spatial.location"])
        self.assertCountEqual(tiers[PeerReviewBadge.GOLD], ["resources.description"])
        self.assertEqual(tiers[PeerReviewBadge.PLATINUM], [])

    def test_returns_empty_list_for_undeclared_tier(self):
        tiers = fields_by_tier(FAKE_SCHEMA)
        # Platinum is declared in TIER_ORDER but not in FAKE_SCHEMA
        self.assertIn(PeerReviewBadge.PLATINUM, tiers)
        self.assertEqual(tiers[PeerReviewBadge.PLATINUM], [])


class TestFieldsByTierIron(SimpleTestCase):
    def test_includes_iron_and_orders_deterministically(self):
        tiers = fields_by_tier(FAKE_SCHEMA)
        self.assertCountEqual(tiers[PeerReviewBadge.IRON], ["context.homepage", "id"])
        self.assertCountEqual(tiers[PeerReviewBadge.BRONZE], ["name", "title"])
        self.assertCountEqual(tiers[PeerReviewBadge.SILVER], ["spatial.location"])
        self.assertCountEqual(tiers[PeerReviewBadge.GOLD], ["resources.description"])
        self.assertCountEqual(tiers[PeerReviewBadge.PLATINUM], ["resources.path"])

    def test_defaults_to_oemetadata_schema_when_none(self):
        # should not raise – uses OEMETADATA_V20_SCHEMA internally
        tiers = fields_by_tier(None)
        self.assertIn(PeerReviewBadge.IRON, tiers)
        self.assertTrue(len(tiers[PeerReviewBadge.IRON]) > 0)


# class TestCumulativeTierStrategy(SimpleTestCase):
#     def test_iron_when_bronze_incomplete(self):
#         md = {"name": "n"}  # title missing
#         self.assertEqual(
#             cumulative_tier_strategy(md, FAKE_SCHEMA), PeerReviewBadge.IRON
#         )

#     def test_bronze_when_only_bronze_complete(self):
#         md = {"name": "n", "title": "t"}
#         self.assertEqual(
#             cumulative_tier_strategy(md, FAKE_SCHEMA), PeerReviewBadge.BRONZE
#         )

#     def test_silver_then_gold_cumulative(self):
#         silver = {"name": "n", "title": "t", "spatial": {"location": "DE"}}
#         self.assertEqual(
#             cumulative_tier_strategy(silver, FAKE_SCHEMA), PeerReviewBadge.SILVER
#         )

#         gold = dict(silver, resources=[{"description": "d"}])
#         self.assertEqual(
#             cumulative_tier_strategy(gold, FAKE_SCHEMA), PeerReviewBadge.GOLD
#         )

#     def test_gap_stops_progression(self):
#         # bronze ok, silver missing, gold present -> capped at bronze
#         md = {"name": "n", "title": "t", "resources": [{"description": "d"}]}
#         self.assertEqual(
#             cumulative_tier_strategy(md, FAKE_SCHEMA), PeerReviewBadge.BRONZE
#         )

#     def test_empty_top_tier_is_not_auto_awarded(self):
#         # FAKE_SCHEMA declares no Platinum fields -> never reaches Platinum
#         full = {
#             "name": "n",
#             "title": "t",
#             "spatial": {"location": "DE"},
#             "resources": [{"description": "d"}],
#         }
#         self.assertEqual(
#             cumulative_tier_strategy(full, FAKE_SCHEMA), PeerReviewBadge.GOLD
#         )


class TestCumulativeTierStrategy(SimpleTestCase):
    """cumulative_tier_strategy – iron is explicit, not just fallback."""

    def test_iron_awarded_when_iron_fields_complete(self):
        md = {"id": "x", "context": {"homepage": "https://example.org"}}
        self.assertEqual(
            cumulative_tier_strategy(md, FAKE_SCHEMA),
            PeerReviewBadge.IRON,
        )

    def test_bronze_requires_iron_first(self):
        # bronze fields filled, iron missing -> stays IRON (fallback start value)
        md = {"name": "n", "title": "t"}
        self.assertEqual(
            cumulative_tier_strategy(md, FAKE_SCHEMA),
            PeerReviewBadge.IRON,
        )

    def test_full_cumulative_iron_to_platinum(self):
        md = {
            "id": "x",
            "context": {"homepage": "https://e.org"},
            "name": "n",
            "title": "t",
            "spatial": {"location": "DE"},
            "resources": [{"description": "d", "path": "/tmp"}],
        }
        self.assertEqual(
            cumulative_tier_strategy(md, FAKE_SCHEMA),
            PeerReviewBadge.PLATINUM,
        )

    def test_gap_stops_at_first_missing_tier_iron_path(self):
        # iron+bronze ok, silver missing, gold+platinum present
        md = {
            "id": "x",
            "context": {"homepage": "h"},
            "name": "n",
            "title": "t",
            "resources": [{"description": "d", "path": "p"}],
        }
        self.assertEqual(
            cumulative_tier_strategy(md, FAKE_SCHEMA),
            PeerReviewBadge.BRONZE,
        )


class TestNormalizeReviewKey(SimpleTestCase):
    def test_strips_numeric_list_indices(self):
        self.assertEqual(normalize_review_key("resources.0.title"), "resources.title")
        self.assertEqual(
            normalize_review_key("resources.12.schema.fields.2.name"),
            "resources.schema.fields.name",
        )
        self.assertEqual(normalize_review_key("name"), "name")

    def test_handles_multiple_indices(self):
        self.assertEqual(
            normalize_review_key("resources.0.sources.1.title"),
            "resources.sources.title",
        )

    def test_empty_and_none_safe(self):
        self.assertEqual(normalize_review_key(""), "")
        # None is falsy – function returns input unchanged
        self.assertIsNone(normalize_review_key(None))  # type: ignore[arg-type]


class TestLastFieldReviewState(SimpleTestCase):
    def test_extracts_state_from_dict(self):
        self.assertEqual(_last_field_review_state({"state": "ok"}), "ok")
        self.assertEqual(
            _last_field_review_state({"state": "Suggestion"}), "suggestion"
        )

    def test_takes_last_element_of_list(self):
        fr = [
            {"state": "suggestion", "timestamp": 1},
            {"state": "rejected", "timestamp": 2},
            {"state": "ok", "timestamp": 3},
        ]
        self.assertEqual(_last_field_review_state(fr), "ok")

    def test_empty_list_and_none_guard(self):
        self.assertEqual(_last_field_review_state([]), "")
        self.assertEqual(_last_field_review_state(None), "")
        self.assertEqual(_last_field_review_state("bad"), "")


class TestExtractOkFields(SimpleTestCase):
    def test_collects_ok_normalized_keys(self):
        review = {
            "reviews": [
                {
                    "key": "resources.0.title",
                    "category": "general",
                    "fieldReview": {"state": "ok"},
                },
                {
                    "key": "spatial.location",
                    "category": "spatial",
                    "fieldReview": {"state": "suggestion"},
                },
                {
                    "key": "name",
                    "category": "general",
                    "fieldReview": [{"state": "rejected"}, {"state": "ok"}],
                },
            ]
        }
        ok = extract_ok_fields(review)
        self.assertEqual(ok, {"resources.title", "name"})

    def test_ignores_non_ok_states(self):
        review = {
            "reviews": [
                {"key": "title", "fieldReview": {"state": "rejected"}},
                {"key": "name", "fieldReview": {"state": ""}},
            ]
        }
        self.assertEqual(extract_ok_fields(review), set())

    def test_handles_missing_reviews_gracefully(self):
        self.assertEqual(extract_ok_fields({}), set())
        self.assertEqual(extract_ok_fields({"reviews": None}), set())
        self.assertEqual(extract_ok_fields(None), set())  # type: ignore[arg-type]


class TestExtractFieldStates(SimpleTestCase):
    def test_maps_normalized_key_to_last_state(self):
        review = {
            "reviews": [
                {
                    "key": "resources.0.description",
                    "fieldReview": [
                        {"state": "suggestion"},
                        {"state": "ok", "role": "contributor"},
                    ],
                },
                {"key": "title", "fieldReview": {"state": "rejected"}},
            ]
        }
        states = extract_field_states(review)
        self.assertEqual(states, {"resources.description": "ok", "title": "rejected"})


class TestReviewBasedCumulativeTierStrategy(SimpleTestCase):
    """Review-state based, cumulative – uses fields_by_tier (bronze→platinum)."""

    def test_bronze_awarded_when_bronze_fields_ok(self):
        # FAKE_SCHEMA bronze = name, title
        review = {
            "reviews": [
                {"key": "name", "fieldReview": {"state": "ok"}},
                {"key": "title", "fieldReview": {"state": "ok"}},
            ]
        }
        badge = review_based_cumulative_tier_strategy(review, FAKE_SCHEMA)
        self.assertEqual(badge, PeerReviewBadge.BRONZE)

    def test_silver_requires_bronze_first(self):
        # silver ok, bronze missing -> None (caller maps None→IRON)
        review = {
            "reviews": [{"key": "spatial.location", "fieldReview": {"state": "ok"}}]
        }
        badge = review_based_cumulative_tier_strategy(review, FAKE_SCHEMA)
        self.assertIsNone(badge)

    def test_silver_awarded_when_bronze_and_silver_ok(self):
        review = {
            "reviews": [
                {"key": "name", "fieldReview": {"state": "ok"}},
                {"key": "title", "fieldReview": {"state": "ok"}},
                {"key": "spatial.location", "fieldReview": {"state": "ok"}},
            ]
        }
        badge = review_based_cumulative_tier_strategy(review, FAKE_SCHEMA)
        self.assertEqual(badge, PeerReviewBadge.SILVER)

    def test_handles_indexed_resource_keys(self):
        # review keys come as resources.0.description
        review = {
            "reviews": [
                {"key": "name", "fieldReview": {"state": "ok"}},
                {"key": "title", "fieldReview": {"state": "ok"}},
                {"key": "spatial.location", "fieldReview": {"state": "ok"}},
                {"key": "resources.0.description", "fieldReview": {"state": "ok"}},
            ]
        }
        badge = review_based_cumulative_tier_strategy(review, FAKE_SCHEMA)
        self.assertEqual(badge, PeerReviewBadge.GOLD)

    def test_last_field_review_wins(self):
        review = {
            "reviews": [
                {"key": "name", "fieldReview": {"state": "ok"}},
                {
                    "key": "title",
                    "fieldReview": [{"state": "suggestion"}, {"state": "ok"}],
                },
            ]
        }
        badge = review_based_cumulative_tier_strategy(review, FAKE_SCHEMA)
        self.assertEqual(badge, PeerReviewBadge.BRONZE)


class TestReviewBasedCumulativeTierStrategyDetails(SimpleTestCase):
    def test_returns_diagnostics_on_failure(self):
        # bronze incomplete (title missing)
        review = {
            "reviews": [
                {"key": "name", "fieldReview": {"state": "ok"}},
                {"key": "spatial.location", "fieldReview": {"state": "ok"}},
            ]
        }
        badge, details = review_based_cumulative_tier_strategy_details(
            review, FAKE_SCHEMA
        )
        self.assertIsNone(badge)
        self.assertEqual(details["failed_at"], PeerReviewBadge.BRONZE)
        self.assertIn("title", details["missing"][PeerReviewBadge.BRONZE])
        self.assertIn("name", details["ok_fields"])

    def test_details_include_full_requirement_map(self):
        review = {"reviews": []}
        badge, details = review_based_cumulative_tier_strategy_details(
            review, FAKE_SCHEMA
        )
        self.assertIsNone(badge)
        self.assertIn("required_by_tier", details)
        self.assertIn(PeerReviewBadge.BRONZE, details["required_by_tier"])


class TestBadgeLabel(SimpleTestCase):
    def test_capitalizes_enum_name(self):
        self.assertEqual(badge_label(PeerReviewBadge.IRON), "Iron")
        self.assertEqual(badge_label(PeerReviewBadge.BRONZE), "Bronze")
        self.assertEqual(badge_label(PeerReviewBadge.SILVER), "Silver")
        self.assertEqual(badge_label(PeerReviewBadge.GOLD), "Gold")
        self.assertEqual(badge_label(PeerReviewBadge.PLATINUM), "Platinum")


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

    def test_suggest_badge_accepts_review_datamodel(self):
        # new review-state path – BadgeService auto-detects {'reviews':[...]}
        svc = (
            BadgeService()
        )  # defaults to cumulative_tier_strategy which detects review shape
        review_data = {
            "reviews": [
                {"key": "name", "fieldReview": {"state": "ok"}},
                {"key": "title", "fieldReview": {"state": "ok"}},
            ]
        }
        badge = svc.suggest_badge(review_data, schema=FAKE_SCHEMA)
        # review_based path returns BRONZE, wrapper maps None→IRON –
        # here bronze succeeds
        self.assertEqual(badge, PeerReviewBadge.BRONZE)
