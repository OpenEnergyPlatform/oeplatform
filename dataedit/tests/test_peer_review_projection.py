"""
Tests for the OPR round projection (Phase 1 / Phase 2 S3).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

``projection`` rebuilds the ``PeerReview.review`` JSON from ``ReviewRound`` rows.
The defining guarantee — ``fieldReview`` is always a list, one element per round —
is asserted here. Pure functions → fast ``SimpleTestCase``.
"""  # noqa: E501

from django.test import SimpleTestCase

from dataedit.peer_review.projection import (
    build_reviews_from_rounds,
    compute_round_delta,
    field_history,
    project_review,
    reconstruct_rounds_from_review,
)


def _round(sequence, field_reviews, sets_finished=False):
    return {
        "sequence": sequence,
        "field_reviews": field_reviews,
        "sets_finished": sets_finished,
    }


def _fr(key, state, role, category="general"):
    return {
        "key": key,
        "category": category,
        "fieldReview": {"state": state, "role": role},
    }


class TestBuildReviewsFromRounds(SimpleTestCase):
    def test_single_round_single_field_yields_list_of_one(self):
        rounds = [_round(1, [_fr("title", "ok", "reviewer")])]
        reviews = build_reviews_from_rounds(rounds)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["key"], "title")
        self.assertEqual(reviews[0]["category"], "general")
        # the guarantee: fieldReview is ALWAYS a list
        self.assertEqual(
            reviews[0]["fieldReview"], [{"state": "ok", "role": "reviewer"}]
        )

    def test_two_rounds_same_field_collected_in_sequence_order(self):
        rounds = [
            _round(2, [_fr("title", "ok", "contributor")]),
            _round(1, [_fr("title", "suggestion", "reviewer")]),
        ]
        reviews = build_reviews_from_rounds(rounds)
        self.assertEqual(len(reviews), 1)
        # ascending sequence: reviewer (seq 1) then contributor (seq 2)
        self.assertEqual(
            reviews[0]["fieldReview"],
            [
                {"state": "suggestion", "role": "reviewer"},
                {"state": "ok", "role": "contributor"},
            ],
        )

    def test_distinct_fields_keep_first_appearance_order(self):
        rounds = [
            _round(1, [_fr("title", "ok", "reviewer"), _fr("name", "ok", "reviewer")]),
        ]
        reviews = build_reviews_from_rounds(rounds)
        self.assertEqual([r["key"] for r in reviews], ["title", "name"])

    def test_same_key_different_category_are_separate_entries(self):
        rounds = [
            _round(
                1,
                [
                    _fr("x", "ok", "reviewer", category="general"),
                    _fr("x", "ok", "reviewer", category="spatial"),
                ],
            )
        ]
        reviews = build_reviews_from_rounds(rounds)
        self.assertEqual(len(reviews), 2)
        self.assertEqual(
            {(r["category"], r["key"]) for r in reviews},
            {("general", "x"), ("spatial", "x")},
        )

    def test_empty_rounds_yield_empty_reviews(self):
        self.assertEqual(build_reviews_from_rounds([]), [])
        self.assertEqual(build_reviews_from_rounds([_round(1, [])]), [])


class TestProjectReview(SimpleTestCase):
    def test_preserves_header_fields_and_replaces_reviews(self):
        base = {
            "topic": "model_draft",
            "table": "t1",
            "reviewFinished": False,
            "reviews": [{"stale": "data"}],
        }
        rounds = [_round(1, [_fr("title", "ok", "reviewer")])]
        projected = project_review(base, rounds)

        self.assertEqual(projected["topic"], "model_draft")
        self.assertEqual(projected["table"], "t1")
        self.assertEqual(len(projected["reviews"]), 1)
        self.assertEqual(projected["reviews"][0]["key"], "title")
        # base is not mutated
        self.assertEqual(base["reviews"], [{"stale": "data"}])

    def test_sets_review_finished_when_a_round_finishes(self):
        rounds = [
            _round(1, [_fr("title", "ok", "reviewer")]),
            _round(2, [_fr("title", "ok", "contributor")], sets_finished=True),
        ]
        projected = project_review({"reviewFinished": False}, rounds)
        self.assertTrue(projected["reviewFinished"])

    def test_none_base_is_tolerated(self):
        projected = project_review(None, [_round(1, [_fr("title", "ok", "reviewer")])])
        self.assertEqual(len(projected["reviews"]), 1)


class TestComputeRoundDelta(SimpleTestCase):
    def test_first_round_keeps_all_incoming(self):
        incoming = [_fr("title", "ok", "reviewer"), _fr("name", "ok", "reviewer")]
        delta = compute_round_delta(incoming, prior_rounds=[])
        self.assertEqual(len(delta), 2)
        self.assertEqual({d["key"] for d in delta}, {"title", "name"})

    def test_re_sent_entries_already_in_prior_rounds_are_dropped(self):
        already = _fr("title", "suggestion", "reviewer")
        prior = [{"field_reviews": [already]}]
        # client re-sends the old entry plus a genuinely new contributor entry
        incoming = [already, _fr("title", "ok", "contributor")]
        delta = compute_round_delta(incoming, prior_rounds=prior)
        self.assertEqual(len(delta), 1)
        self.assertEqual(
            delta[0]["fieldReview"], {"state": "ok", "role": "contributor"}
        )

    def test_list_shaped_incoming_fieldreview_is_flattened(self):
        incoming = [
            {
                "key": "title",
                "category": "general",
                "fieldReview": [
                    {"state": "suggestion", "role": "reviewer"},
                    {"state": "ok", "role": "contributor"},
                ],
            }
        ]
        delta = compute_round_delta(incoming, prior_rounds=[])
        self.assertEqual(len(delta), 2)
        self.assertTrue(all(isinstance(d["fieldReview"], dict) for d in delta))

    def test_same_field_new_timestamp_is_a_new_contribution(self):
        prior = [
            {
                "field_reviews": [
                    {
                        "key": "t",
                        "category": "g",
                        "fieldReview": {"state": "ok", "timestamp": 1},
                    }
                ]
            }
        ]
        incoming = [
            {
                "key": "t",
                "category": "g",
                "fieldReview": {"state": "rejected", "timestamp": 2},
            }
        ]
        delta = compute_round_delta(incoming, prior_rounds=prior)
        self.assertEqual(len(delta), 1)
        self.assertEqual(delta[0]["fieldReview"]["timestamp"], 2)


class TestReconstructRoundsFromReview(SimpleTestCase):
    def test_splits_into_rounds_at_role_changes_ordered_by_timestamp(self):
        review = {
            "reviews": [
                {
                    "key": "title",
                    "category": "general",
                    "fieldReview": [
                        {"role": "reviewer", "state": "suggestion", "timestamp": 10},
                        {"role": "contributor", "state": "ok", "timestamp": 20},
                    ],
                },
                {
                    "key": "name",
                    "category": "general",
                    "fieldReview": {"role": "reviewer", "state": "ok", "timestamp": 5},
                },
            ]
        }
        rounds = reconstruct_rounds_from_review(review)
        # timeline: reviewer@5, reviewer@10, contributor@20 -> 2 rounds
        self.assertEqual(len(rounds), 2)
        self.assertEqual(rounds[0]["role"], "reviewer")
        self.assertEqual(rounds[0]["sequence"], 1)
        self.assertEqual(len(rounds[0]["field_reviews"]), 2)
        self.assertEqual(rounds[1]["role"], "contributor")
        self.assertEqual(rounds[1]["sequence"], 2)

    def test_empty_or_missing_review_yields_no_rounds(self):
        self.assertEqual(reconstruct_rounds_from_review(None), [])
        self.assertEqual(reconstruct_rounds_from_review({}), [])
        self.assertEqual(reconstruct_rounds_from_review({"reviews": []}), [])


class TestFieldHistory(SimpleTestCase):
    def test_orders_contributions_by_timestamp(self):
        reviews = [
            {
                "key": "title",
                "category": "general",
                "fieldReview": [
                    {"role": "contributor", "state": "ok", "timestamp": 20},
                    {"role": "reviewer", "state": "suggestion", "timestamp": 10},
                ],
            }
        ]
        history = field_history(reviews)
        self.assertEqual(
            [c["role"] for c in history["title"]], ["reviewer", "contributor"]
        )

    def test_single_dict_field_review_becomes_one_element(self):
        reviews = [{"key": "a", "category": "general", "fieldReview": {"state": "ok"}}]
        history = field_history(reviews)
        self.assertEqual(len(history["a"]), 1)

    def test_empty_or_none_yields_empty_history(self):
        self.assertEqual(field_history([]), {})
        self.assertEqual(field_history(None), {})
