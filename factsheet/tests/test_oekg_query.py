# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
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

    def test_get_related_scenarios_where_table_is_input_dataset(self):
        # Set up mock triples for testing
        triples = [
            (URIRef("scenario1"), RDF.type, namespaces.OEO.OEO_00000365),
            (URIRef("scenario1"), namespaces.OEO.RO_0002233, URIRef("input_ds_uid")),
            (URIRef("input_ds_uid"), namespaces.OEO["has_iri"], Literal("test_table")),
            (URIRef("scenario2"), RDF.type, namespaces.OEO.OEO_00000365),
            (URIRef("scenario2"), namespaces.OEO.RO_0002233, URIRef("input_ds_uid")),
            (URIRef("input_ds_uid"), namespaces.OEO["has_iri"], Literal("test_table")),
        ]

        self.oekg_mock.triples.return_value = triples

        # Call the method being tested
        result = self.oekg_query.get_related_scenarios_where_table_is_input_dataset(
            "test_table"
        )

        # Assert the expected result
        expected_result = {URIRef("scenario1"), URIRef("scenario2")}
        self.assertEqual(result, expected_result)

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
