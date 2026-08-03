"""
Characterization (safety-net) tests for the Open Peer Review helper functions.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

These tests pin the CURRENT behavior of the pure helper functions in
``dataedit/helper.py`` so that the planned OPR refactor has a tripwire. They are
"characterization" tests: they document what the code does *today*, quirks and
all, NOT what it ideally should do. Where the current behavior is surprising or
buggy, the test name / comment says so explicitly instead of asserting the
"correct" result.

Targets (see Obsidian: "07 - Pain Points & Refactoring Plan", Phase 0):
    - merge_field_reviews
    - recursive_update (+ set_nested_value / delete_nested_field)
    - process_review_data

All three are pure (no DB), so this is a fast ``SimpleTestCase``.
"""  # noqa: E501

import copy

from django.test import SimpleTestCase

from dataedit.helper import merge_field_reviews, process_review_data, recursive_update


def _review(category, key, field_review):
    """Build one entry of the review datamodel's ``reviews`` list."""
    return {"category": category, "key": key, "fieldReview": field_review}


class TestMergeFieldReviews(SimpleTestCase):
    """``merge_field_reviews(current_json, new_json)``.

    Call-site reminder (dataedit/views.py):
        current_json = the review already stored on the PeerReview row
        new_json     = the freshly submitted review datamodel

    The function seeds its working dict from ``new_json`` and then folds in
    ``current_json``. The internal variable names ("contrib"/"reviewer") are
    misleading; trust the argument roles, not the names.
    """

    def test_disjoint_keys_are_all_kept_as_is(self):
        current = {"reviews": [_review("general", "a", {"state": "ok"})]}
        new = {"reviews": [_review("general", "b", {"state": "suggestion"})]}

        merged = merge_field_reviews(current, new)

        by_key = {r["key"]: r["fieldReview"] for r in merged["reviews"]}
        self.assertEqual(set(by_key), {"a", "b"})
        # A key present on only one side keeps its ORIGINAL dict shape
        # (it is NOT wrapped into a list).
        self.assertEqual(by_key["a"], {"state": "ok"})
        self.assertEqual(by_key["b"], {"state": "suggestion"})

    def test_overlapping_key_merges_into_list_new_first_then_current(self):
        # Same (category, key) on both sides -> fieldReview becomes a LIST.
        current = {"reviews": [_review("general", "a", {"state": "ok_current"})]}
        new = {"reviews": [_review("general", "a", {"state": "sugg_new"})]}

        merged = merge_field_reviews(current, new)

        self.assertEqual(len(merged["reviews"]), 1)
        field_review = merged["reviews"][0]["fieldReview"]
        # CHARACTERIZATION: order is [new_json entry, current_json entry].
        self.assertEqual(
            field_review,
            [{"state": "sugg_new"}, {"state": "ok_current"}],
        )

    def test_overlapping_key_appends_when_sides_already_lists(self):
        current = {"reviews": [_review("g", "a", [{"state": "c1"}, {"state": "c2"}])]}
        new = {"reviews": [_review("g", "a", [{"state": "n1"}])]}

        merged = merge_field_reviews(current, new)

        field_review = merged["reviews"][0]["fieldReview"]
        # new list first, then current list appended.
        self.assertEqual(
            field_review,
            [{"state": "n1"}, {"state": "c1"}, {"state": "c2"}],
        )

    def test_mutates_current_json_in_place_side_effect(self):
        # CHARACTERIZATION of a SUBTLE BUG: merging wraps the matching
        # fieldReview dict of current_json into a list *in place*, mutating
        # the caller's input object. A refactor should remove this side effect.
        current = {"reviews": [_review("g", "a", {"state": "ok"})]}
        new = {"reviews": [_review("g", "a", {"state": "sugg"})]}

        merge_field_reviews(current, new)

        self.assertEqual(current["reviews"][0]["fieldReview"], [{"state": "ok"}])

    def test_none_current_json_raises(self):
        # CHARACTERIZATION: passing None (e.g. PeerReview.review is null) blows
        # up rather than being handled gracefully.
        new = {"reviews": [_review("g", "a", {"state": "ok"})]}
        with self.assertRaises(TypeError):
            merge_field_reviews(None, new)


class TestRecursiveUpdate(SimpleTestCase):
    """``recursive_update(metadata, review_data)``.

    ``review_data`` is the FULL POST body, so reviews live at
    ``review_data["reviewData"]["reviews"]``. Accepted ``newValue``s are written
    into ``metadata``; fields whose state is ``rejected`` are removed.
    """

    @staticmethod
    def _body(reviews):
        return {"reviewData": {"reviews": reviews}}

    def _metadata(self):
        return {
            "resources": [
                {
                    "title": "old title",
                    "keywords": ["a", "b", "c"],
                }
            ]
        }

    def test_dict_field_review_sets_new_value_at_nested_path(self):
        md = self._metadata()
        body = self._body(
            [
                _review(
                    "general", "resources.0.title", {"state": "ok", "newValue": "new"}
                )
            ]
        )

        result = recursive_update(md, body)

        self.assertEqual(result["resources"][0]["title"], "new")
        # mutates and returns the same object
        self.assertIs(result, md)

    def test_rejected_dict_field_review_deletes_the_field(self):
        md = self._metadata()
        body = self._body(
            [_review("general", "resources.0.title", {"state": "rejected"})]
        )

        recursive_update(md, body)

        self.assertNotIn("title", md["resources"][0])

    def test_rejected_can_pop_a_list_element_by_index(self):
        md = self._metadata()
        body = self._body(
            [_review("general", "resources.0.keywords.1", {"state": "rejected"})]
        )

        recursive_update(md, body)

        # index 1 ("b") removed
        self.assertEqual(md["resources"][0]["keywords"], ["a", "c"])

    def test_empty_new_value_is_not_applied(self):
        md = self._metadata()
        body = self._body(
            [_review("general", "resources.0.title", {"state": "ok", "newValue": ""})]
        )

        recursive_update(md, body)

        self.assertEqual(md["resources"][0]["title"], "old title")

    def test_list_field_review_applies_new_value(self):
        md = self._metadata()
        body = self._body(
            [
                _review(
                    "general",
                    "resources.0.title",
                    [{"state": "ok", "newValue": "from-list"}],
                )
            ]
        )

        recursive_update(md, body)

        self.assertEqual(md["resources"][0]["title"], "from-list")

    def test_list_field_review_with_one_rejected_deletes_field(self):
        # CHARACTERIZATION: in a list, a single 'rejected' entry wins and the
        # field is deleted regardless of any sibling newValue entries.
        md = self._metadata()
        body = self._body(
            [
                _review(
                    "general",
                    "resources.0.title",
                    [
                        {"state": "ok", "newValue": "ignored"},
                        {"state": "rejected"},
                    ],
                )
            ]
        )

        recursive_update(md, body)

        self.assertNotIn("title", md["resources"][0])


class TestProcessReviewData(SimpleTestCase):
    """``process_review_data(review_data, metadata, categories)``.

    Attaches reviewer suggestion/comment/newValue onto each metadata field item
    (in place) and returns a ``state_dict`` mapping field key -> state. The
    ``metadata`` here is the category-grouped structure produced by
    ``sort_in_category``.
    """

    def _metadata(self):
        return {
            "general": {
                "flat": [{"field": "title", "value": "old"}],
                "grouped": {},
            }
        }

    def test_initializes_missing_review_attributes_with_empty_strings(self):
        md = self._metadata()

        process_review_data(review_data=[], metadata=md, categories=["general"])

        item = md["general"]["flat"][0]
        for attr in (
            "reviewer_suggestion",
            "suggestion_comment",
            "additional_comment",
            "newValue",
        ):
            self.assertEqual(item[attr], "")

    def test_dict_field_review_is_attached_and_state_recorded(self):
        md = self._metadata()
        review_data = [
            _review(
                "general",
                "title",
                {
                    "state": "suggestion",
                    "reviewerSuggestion": "foo",
                    "comment": "bar",
                    "newValue": "baz",
                    "additionalComment": "qux",
                },
            )
        ]

        state_dict = process_review_data(
            review_data=review_data, metadata=md, categories=["general"]
        )

        item = md["general"]["flat"][0]
        self.assertEqual(item["reviewer_suggestion"], "foo")
        self.assertEqual(item["suggestion_comment"], "bar")
        self.assertEqual(item["newValue"], "baz")
        self.assertEqual(item["additional_comment"], "qux")
        self.assertEqual(state_dict, {"title": "suggestion"})

    def test_list_field_review_uses_latest_by_timestamp(self):
        md = self._metadata()
        review_data = [
            _review(
                "general",
                "title",
                [
                    {"timestamp": 100, "state": "ok", "reviewerSuggestion": "early"},
                    {
                        "timestamp": 200,
                        "state": "rejected",
                        "reviewerSuggestion": "late",
                    },
                ],
            )
        ]

        state_dict = process_review_data(
            review_data=review_data, metadata=md, categories=["general"]
        )

        # latest timestamp (200) wins
        self.assertEqual(state_dict["title"], "rejected")
        self.assertEqual(md["general"]["flat"][0]["reviewer_suggestion"], "late")

    def test_review_for_key_absent_in_metadata_still_recorded_in_state_dict(self):
        md = self._metadata()
        review_data = [_review("general", "does.not.exist", {"state": "ok"})]

        state_dict = process_review_data(
            review_data=review_data, metadata=md, categories=["general"]
        )

        # CHARACTERIZATION: state is tracked even when no metadata item matches.
        self.assertEqual(state_dict["does.not.exist"], "ok")

    def test_none_review_data_is_tolerated(self):
        md = self._metadata()

        state_dict = process_review_data(
            review_data=None, metadata=md, categories=["general"]
        )

        self.assertEqual(state_dict, {})

    def test_does_not_mutate_the_review_data_input(self):
        md = self._metadata()
        review_data = [_review("general", "title", {"state": "ok"})]
        snapshot = copy.deepcopy(review_data)

        process_review_data(
            review_data=review_data, metadata=md, categories=["general"]
        )

        self.assertEqual(review_data, snapshot)
