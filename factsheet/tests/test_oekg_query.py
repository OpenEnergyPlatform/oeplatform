"""
SPDX-FileCopyrightText: 2025 Jonas Huber
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import unittest

from rdflib import RDF, Graph, Literal, URIRef

from factsheet.oekg import namespaces
from factsheet.oekg.filters import OekgQuery


class TestOekgQuery(unittest.TestCase):
    def setUp(self):
        self.oekg_query = OekgQuery()

    def _make_graph_with_input(self, table_iri_literal: str):
        g = Graph()
        bundle = URIRef("https://oekg.test/bundle1")
        scenario = URIRef("https://oekg.test/scenario/A")
        input_ds = URIRef("https://oekg.test/dataset/in1")

        g.add((bundle, RDF.type, namespaces.OEO.OEO_00020227))
        g.add((bundle, namespaces.OBO.BFO_0000051, scenario))
        g.add((scenario, namespaces.OEO.OEO_00020437, input_ds))
        g.add((input_ds, namespaces.OEO.OEO_00390094, Literal(table_iri_literal)))
        return g, bundle, scenario

    def _make_graph_with_output(self, table_iri_literal: str):
        g = Graph()
        bundle = URIRef("https://oekg.test/bundle2")
        scenario = URIRef("https://oekg.test/scenario/B")
        output_ds = URIRef("https://oekg.test/dataset/out1")

        g.add((bundle, RDF.type, namespaces.OEO.OEO_00020227))
        g.add((bundle, namespaces.OBO.BFO_0000051, scenario))
        g.add((scenario, namespaces.OEO.OEO_00020436, output_ds))
        g.add((output_ds, namespaces.OEO.OEO_00390094, Literal(table_iri_literal)))
        return g, bundle, scenario

    # -------- input dataset tests --------

    def test_input_basic_relative_path(self):
        iri = "dataedit/view/scenario/test_table"
        g, _, scenario = self._make_graph_with_input(iri)
        self.oekg_query.oekg = g
        got = self.oekg_query.get_related_scenarios_where_table_is_input_dataset(iri)
        self.assertEqual(got, {scenario})

    def test_input_full_url_matches_relative(self):
        stored = "https://openenergyplatform.org/dataedit/view/scenario/test_table"
        query = "dataedit/view/scenario/test_table"
        g, _, scenario = self._make_graph_with_input(stored)
        self.oekg_query.oekg = g
        got = self.oekg_query.get_related_scenarios_where_table_is_input_dataset(query)
        self.assertEqual(got, {scenario})

    # -------- output dataset tests --------

    def test_output_basic_relative_path(self):
        iri = "dataedit/view/scenario/out_table"
        g, _, scenario = self._make_graph_with_output(iri)
        self.oekg_query.oekg = g
        got = self.oekg_query.get_related_scenarios_where_table_is_output_dataset(iri)
        self.assertEqual(got, {scenario})

    def test_output_full_url_matches_relative(self):
        stored = "https://openenergyplatform.org/dataedit/view/scenario/out_table"
        query = "dataedit/view/scenario/out_table"
        g, _, scenario = self._make_graph_with_output(stored)
        self.oekg_query.oekg = g
        got = self.oekg_query.get_related_scenarios_where_table_is_output_dataset(query)
        self.assertEqual(got, {scenario})

    # -------- bundle mapping helpers --------

    def test_get_scenario_bundles_where_table_is_input(self):
        iri = "dataedit/view/scenario/in_table"
        g, bundle, scenario = self._make_graph_with_input(iri)
        self.oekg_query.oekg = g
        pairs = self.oekg_query.get_scenario_bundles_where_table_is_input(iri)
        # Function returns tuples (bundle_uri, bundle_uri) by design; just assert
        # bundle present
        self.assertEqual(pairs, {(bundle, bundle)})

    def test_get_scenario_bundles_where_table_is_output(self):
        iri = "dataedit/view/scenario/out_table"
        g, bundle, scenario = self._make_graph_with_output(iri)
        self.oekg_query.oekg = g
        pairs = self.oekg_query.get_scenario_bundles_where_table_is_output(iri)
        self.assertEqual(pairs, {(bundle, bundle)})

    # -------- simple acronym helper (kept from your original) --------

    def test_get_scenario_acronym(self):
        g = Graph()
        scen = URIRef("https://oekg.test/scenario/C")
        g.add((scen, namespaces.RDFS.label, Literal("Scenario Acronym")))
        self.oekg_query.oekg = g
        got = self.oekg_query.get_scenario_acronym(scen)
        self.assertEqual(got, Literal("Scenario Acronym"))


if __name__ == "__main__":
    unittest.main()
