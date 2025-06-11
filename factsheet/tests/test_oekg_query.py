# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

import unittest
from unittest.mock import MagicMock

from rdflib import RDF, Graph, Literal, URIRef

from factsheet.oekg import namespaces
from factsheet.oekg.filters import OekgQuery


class TestOekgQuery(unittest.TestCase):
    def setUp(self):
        # Create a mock RDF graph for testing
        self.oekg_mock = MagicMock(spec=Graph)
        self.oekg_query = OekgQuery()
        self.oekg_query.oekg = self.oekg_mock

    def test_with_real_graph(self):
        """
        This test uses a real RDF graph to test the functionality of the
        OekgQuery class instead of mocking it. During writing the test i noticed
        that there ia workarounds hassle involved when testing graphs with
        multiple values.

        The method get_related_scenarios_where_table_is_input_dataset is checked
        if correctly retrieves scenarios where a specific table is listed as an
        input dataset.
        """
        g = Graph()

        iri = "dataedit/view/scenario/test_table"
        bundle = URIRef("bundle1")
        scenario1 = URIRef("scenario1")
        scenario2 = URIRef("scenario2")
        input1 = URIRef("input1")
        input2 = URIRef("input2")

        g.add((bundle, RDF.type, namespaces.OEO.OEO_00010252))
        g.add((bundle, namespaces.OEKG["has_scenario"], scenario1))
        g.add((bundle, namespaces.OEKG["has_scenario"], scenario2))
        g.add((scenario1, namespaces.OEO.RO_0002233, input1))
        g.add((scenario2, namespaces.OEO.RO_0002233, input2))
        g.add((input1, namespaces.OEO["has_iri"], Literal(iri)))
        g.add((input2, namespaces.OEO["has_iri"], Literal(iri)))

        self.oekg_query.oekg = g

        result = self.oekg_query.get_related_scenarios_where_table_is_input_dataset(iri)
        self.assertEqual(result, {scenario1, scenario2})

    def test_get_scenario_acronym(self):
        # Set up mock triples for testing
        triples = [
            (URIRef("scenario_uri"), namespaces.RDFS.label, Literal("Scenario Acronym"))
        ]

        self.oekg_mock.triples.return_value = triples

        # Call the method being tested
        result = self.oekg_query.get_scenario_acronym("scenario_uri")

        # Assert the expected result
        expected_result = Literal("Scenario Acronym")
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
