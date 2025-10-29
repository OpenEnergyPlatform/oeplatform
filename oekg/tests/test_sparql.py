"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import unittest
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from oeplatform.settings import OEKG_SPARQL_ENDPOINT_URL


class SparqlEndpointTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.endpoint_url = reverse("oekg:sparql_endpoint")

    @patch("oekg.utils.execute_sparql_query")
    @unittest.skipIf(
        not OEKG_SPARQL_ENDPOINT_URL,
        reason="Skipping test: OEKG_SPARQL_ENDPOINT_URL not set",
    )
    def test_valid_sparql_query(self, mock_execute_sparql_query):
        mock_execute_sparql_query.return_value = (
            '{"head": {"vars": ["sub", "pred", "obj"]}, "results": {"bindings": []}}',
            "application/sparql-results+json",
        )

        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT * WHERE {
          ?sub ?pred ?obj .
        }
        LIMIT 10
        """

        response = self.client.post(self.endpoint_url, {"query": query})
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertIn("head", json_response)
        self.assertIn("results", json_response)
