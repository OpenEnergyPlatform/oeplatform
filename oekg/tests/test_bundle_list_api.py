"""The bundle collection: what a listing returns, and what it refuses to become.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest.mock import patch

from rdflib import Graph, Literal

from oekg.bundles import bundle_iri
from oekg.fields import DC, OEO
from oekg.graph_store import GraphStore
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.summaries import ScenarioBundlePagination
from oekg.tests.bundle_fixtures import VALID_PAYLOAD, BundleApiTestCase

A_SCENARIO = {
    "label": "A scenario",
    "acronym": "SCEN",
    "scenario_types": [str(OEO.OEO_00000364)],
    "years": ["2030-01-01T00:00:00+00:00"],
}

A_STUDY_REPORT = {
    "label": "A study report",
    "publication_date": "2024-06-01T00:00:00+00:00",
    "authors": [{"label": "A. Author"}],
}


class BundleListTestCase(BundleApiTestCase):
    def listed(self, **params):
        response = self.client.get(self.collection_url, params)
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def acronyms(self, data):
        return [entry["acronym"] for entry in data["results"]]


class BundleSummaryTest(BundleListTestCase):
    def test_a_summary_carries_what_it_takes_to_choose_a_bundle(self):
        uid, _ = self.created()

        entry = self.listed()["results"][0]

        self.assertEqual(entry["acronym"], VALID_PAYLOAD["acronym"])
        self.assertEqual(entry["label"], VALID_PAYLOAD["label"])
        self.assertEqual(entry[READ_ONLY_CONTAINER]["uid"], uid)
        self.assertEqual(entry[READ_ONLY_CONTAINER]["version"], 1)

    def test_a_summary_counts_the_parts_instead_of_carrying_them(self):
        # The point of a summary: how much is in there, without any of it.
        self.created(
            {
                **VALID_PAYLOAD,
                "scenarios": [A_SCENARIO],
                "study_reports": [A_STUDY_REPORT],
            }
        )

        entry = self.listed()["results"][0]

        self.assertEqual(
            entry[READ_ONLY_CONTAINER]["counts"],
            {"scenarios": 1, "study_reports": 1},
        )
        self.assertNotIn("scenarios", entry)
        self.assertNotIn("study_reports", entry)

    def test_a_summary_carries_no_bundle_fields_beyond_the_two_named(self):
        self.created()

        entry = self.listed()["results"][0]

        self.assertEqual(set(entry) - {READ_ONLY_CONTAINER}, {"acronym", "label"})

    def test_the_read_only_container_is_there_even_on_a_bare_bundle(self):
        self.created()

        self.assertIn(READ_ONLY_CONTAINER, self.listed()["results"][0])

    def test_a_listing_needs_no_authentication(self):
        self.created()
        self.client.logout()

        self.assertEqual(self.client.get(self.collection_url).status_code, 200)

    def test_a_bundle_the_shape_would_refuse_still_takes_one_row(self):
        # No live bundle conforms, so the listing has to survive one that does
        # not. A second acronym would take two rows out of a page while the
        # total counts the bundle once -- the page would then be longer than
        # the total claims, and the next window would shift under it.
        uid, _ = self.created()
        second = Graph()
        second.add((bundle_iri(uid), DC.acronym, Literal("A-SECOND-ACRONYM")))
        self.store.insert(second)

        data = self.listed()

        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["results"]), 1)

    def test_counts_are_not_multiplied_by_a_filter(self):
        # Two organisations on one bundle join to two rows before grouping. A
        # count that did not say DISTINCT would report two scenarios for a
        # bundle that has one.
        self.created(
            {
                **VALID_PAYLOAD,
                "organisations": [{"label": "First"}, {"label": "Second"}],
                "scenarios": [A_SCENARIO],
            }
        )

        entry = self.listed()["results"][0]

        self.assertEqual(entry[READ_ONLY_CONTAINER]["counts"]["scenarios"], 1)


class AcronymLookupTest(BundleListTestCase):
    """The one filter the contract depends on: a pipeline's way back in."""

    def test_a_pipeline_finds_its_bundle_by_acronym(self):
        uid, etag = self.created()
        self.create({**VALID_PAYLOAD, "acronym": "SOMEBODY-ELSE"})

        data = self.listed(acronym=VALID_PAYLOAD["acronym"])

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0][READ_ONLY_CONTAINER]["uid"], uid)

    def test_the_lookup_carries_the_version_the_next_write_needs(self):
        uid, etag = self.created()

        found = self.listed(acronym=VALID_PAYLOAD["acronym"])["results"][0]

        response = self.patch(
            uid,
            {"label": "Changed by the pipeline"},
            if_match='"%d"' % found[READ_ONLY_CONTAINER]["version"],
        )
        self.assertEqual(response.status_code, 200, response.data)

    def test_an_unknown_acronym_finds_nothing_rather_than_everything(self):
        self.created()

        data = self.listed(acronym="NOT-A-BUNDLE")

        self.assertEqual(data["count"], 0)
        self.assertEqual(data["results"], [])


class ListFilterTest(BundleListTestCase):
    def setUp(self):
        super().setUp()
        self.created(
            {
                **VALID_PAYLOAD,
                "acronym": "WITH-PARTS",
                "organisations": [{"label": "An institute"}],
                "scenarios": [A_SCENARIO],
                "study_reports": [A_STUDY_REPORT],
            }
        )
        self.created({**VALID_PAYLOAD, "acronym": "PLAIN"})

    def organisation_of(self, acronym):
        read = self.client.get(
            self.detail_url(
                self.listed(acronym=acronym)["results"][0][READ_ONLY_CONTAINER]["uid"]
            )
        )
        return read.data["organisations"][0]["iri"]

    def test_a_descriptor_filter_narrows_to_the_bundles_that_pick_it(self):
        both = self.listed(descriptor=VALID_PAYLOAD["descriptors"][0])
        neither = self.listed(descriptor=str(OEO.OEO_00000144))

        self.assertEqual(both["count"], 2)
        self.assertEqual(neither["count"], 0)

    def test_an_organisation_filter_narrows_to_one_bundle(self):
        data = self.listed(organisation=self.organisation_of("WITH-PARTS"))

        self.assertEqual(self.acronyms(data), ["WITH-PARTS"])

    def test_a_scenario_year_range_narrows_to_the_bundle_holding_it(self):
        inside = self.listed(year_from=2029, year_to=2031)
        outside = self.listed(year_from=2040, year_to=2050)

        self.assertEqual(self.acronyms(inside), ["WITH-PARTS"])
        self.assertEqual(outside["count"], 0)

    def test_one_end_of_a_range_is_a_range(self):
        # The user interface's own blocks need both ends and silently drop the
        # filter given one, which answers with every bundle instead.
        self.assertEqual(self.acronyms(self.listed(year_from=2029)), ["WITH-PARTS"])
        self.assertEqual(self.listed(year_to=2020)["count"], 0)

    def test_a_publication_year_range_narrows_by_study_report(self):
        self.assertEqual(
            self.acronyms(self.listed(published_from=2024, published_to=2024)),
            ["WITH-PARTS"],
        )
        self.assertEqual(self.listed(published_from=2025)["count"], 0)

    def test_different_filters_narrow_each_other(self):
        data = self.listed(
            organisation=self.organisation_of("WITH-PARTS"), acronym="PLAIN"
        )

        self.assertEqual(data["count"], 0)

    def test_a_value_that_is_not_an_iri_is_refused_rather_than_ignored(self):
        # Ignored, it would answer with more bundles than were asked for, and a
        # client cannot tell that from there being more.
        response = self.client.get(self.collection_url, {"organisation": "not an iri"})

        self.assertEqual(response.status_code, 400)

    def test_a_year_that_is_not_a_year_is_refused(self):
        response = self.client.get(self.collection_url, {"year_from": "recently"})

        self.assertEqual(response.status_code, 400)


class ListPaginationTest(BundleListTestCase):
    def setUp(self):
        super().setUp()
        for index in range(3):
            self.created({**VALID_PAYLOAD, "acronym": "BUNDLE-%d" % index})

    def test_a_listing_is_paginated_and_says_how_many_there_are(self):
        data = self.listed(page_size=2)

        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 2)
        self.assertIsNotNone(data["next"])

    def test_the_second_page_holds_the_rest(self):
        self.assertEqual(self.acronyms(self.listed(page_size=2, page=2)), ["BUNDLE-2"])

    def test_the_pages_are_ordered_and_do_not_overlap(self):
        first = self.acronyms(self.listed(page_size=2))
        second = self.acronyms(self.listed(page_size=2, page=2))

        self.assertEqual(first + second, ["BUNDLE-0", "BUNDLE-1", "BUNDLE-2"])

    def test_there_is_no_unbounded_mode(self):
        # The ceiling is lowered so three bundles can show that asking for more
        # than it gives the ceiling rather than the ask.
        with patch.object(ScenarioBundlePagination, "max_page_size", 1):
            data = self.listed(page_size=10000)

        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["count"], 3, "and it still says how many there are")

    def test_a_page_beyond_the_end_is_a_404_rather_than_an_empty_page(self):
        self.assertEqual(
            self.client.get(self.collection_url, {"page": 9}).status_code, 404
        )

    def test_the_store_is_asked_twice_however_many_bundles_there_are(self):
        # The defect this endpoint exists not to have: one query per item. The
        # two are the page and the total, and the real queries still run, so
        # the count is of work actually done rather than of a stubbed listing.
        asked = GraphStore.select
        with patch.object(
            GraphStore,
            "select",
            autospec=True,
            side_effect=lambda store, query: asked(store, query),
        ) as select:
            data = self.listed()

        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 3)
        self.assertEqual(select.call_count, 2)


class ListStillCreatesTest(BundleListTestCase):
    def test_the_collection_still_refuses_an_unauthenticated_create(self):
        # The permission rule changed shape when GET was added to this view.
        response = self.create(authenticate=False)

        self.assertIn(response.status_code, (401, 403))
