"""
Tests for the OPR metadata serializer (extracted in Phase 2, step S1).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

``parse_keys`` / ``sort_in_category`` / ``get_all_field_descriptions`` were moved
verbatim out of ``TablePeerReviewView`` into ``dataedit.peer_review.metadata_serializer``.
They had no tests before; these characterize the behavior the templates rely on,
so the Phase-2/3 refactor that follows can lean on them. Pure functions → fast
``SimpleTestCase``.
"""  # noqa: E501

from django.test import SimpleTestCase

from dataedit.peer_review.metadata_serializer import (
    get_all_field_descriptions,
    parse_keys,
    sort_in_category,
)


class TestParseKeys(SimpleTestCase):
    def test_flattens_nested_dict_to_dotted_field_paths(self):
        out = parse_keys({"a": {"b": "v"}})
        self.assertEqual(out, [{"field": "a.b", "value": "v"}])

    def test_indexes_list_items(self):
        out = parse_keys({"a": ["x", "y"]})
        self.assertEqual(
            out,
            [{"field": "a.0", "value": "x"}, {"field": "a.1", "value": "y"}],
        )

    def test_empty_list_becomes_a_single_stringified_entry(self):
        out = parse_keys({"a": []})
        self.assertEqual(out, [{"field": "a", "value": "[]"}])

    def test_values_are_stringified(self):
        out = parse_keys({"n": 5, "b": True})
        self.assertEqual(
            sorted(out, key=lambda x: x["field"]),
            [{"field": "b", "value": "True"}, {"field": "n", "value": "5"}],
        )


class TestSortInCategory(SimpleTestCase):
    def _meta(self):
        return {
            "resources": [
                {
                    "name": "table1",
                    "title": "My Table",
                    "spatial": {"location": "DE"},
                    "temporal": {"referenceDate": "2024"},
                    "sources": [{"title": "Src A"}],
                    "licenses": [{"name": "CC0"}],
                }
            ]
        }

    def test_returns_all_five_categories(self):
        result = sort_in_category(self._meta())
        self.assertEqual(
            set(result), {"general", "spatial", "temporal", "source", "license"}
        )
        for cat in result.values():
            self.assertIn("flat", cat)
            self.assertIn("grouped", cat)

    def test_only_resources_fields_are_kept(self):
        meta = self._meta()
        meta["metaMetadata"] = {"foo": "bar"}  # outside resources.*
        result = sort_in_category(meta)
        all_fields = []
        for cat in result.values():
            all_fields += [i["field"] for i in cat["flat"]]
            for grp in cat["grouped"].values():
                all_fields += [i["field"] for i in grp.get("flat", [])]
        self.assertNotIn("foo", all_fields)

    def test_resource_index_prefix_is_trimmed(self):
        # "resources.0.title" should be trimmed to "title"
        result = sort_in_category(self._meta())
        general_fields = [i["field"] for i in result["general"]["flat"]]
        self.assertIn("title", general_fields)
        self.assertFalse(any(f.startswith("resources.") for f in general_fields))

    def test_empty_metadata_yields_empty_categories(self):
        result = sort_in_category({"resources": [{}]})
        for cat in ("general", "spatial", "temporal", "source", "license"):
            self.assertEqual(result[cat], {"flat": [], "grouped": {}})


class TestGetAllFieldDescriptions(SimpleTestCase):
    def test_collects_description_example_badge_title(self):
        schema = {
            "properties": {
                "name": {
                    "description": "the name",
                    "examples": ["ex1", "ex2"],
                    "badge": "Bronze",
                    "title": "Name",
                }
            }
        }
        out = get_all_field_descriptions(schema)
        self.assertEqual(
            out["name"],
            {
                "description": "the name",
                "example": "ex1",  # first of examples
                "badge": "Bronze",
                "title": "Name",
            },
        )

    def test_v1_example_fallback_when_no_examples_array(self):
        schema = {"properties": {"f": {"example": "single"}}}
        out = get_all_field_descriptions(schema)
        self.assertEqual(out["f"]["example"], "single")

    def test_recurses_into_nested_properties_and_items(self):
        schema = {
            "properties": {
                "resources": {
                    "items": {
                        "properties": {
                            "title": {"description": "resource title"},
                        }
                    }
                }
            }
        }
        out = get_all_field_descriptions(schema)
        self.assertIn("resources.title", out)
        self.assertEqual(out["resources.title"]["description"], "resource title")
