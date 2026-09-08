"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT * WHERE {
  ?sub ?pred ?obj .
}
LIMIT 10
"""


class SparqlEndpointTest(TestCase):
    """The read-only SPARQL passthrough view.

    Patched at ``oekg.views``, not ``oekg.utils``: the view does
    ``from oekg.utils import execute_sparql_query``, which binds the function
    into the view's own namespace where a patch on the source module cannot
    reach it. Patching the wrong name left this test making a real network call
    to a host that only resolves inside the compose network, so it failed on
    every local run -- and that failure had been normalised.
    """

    def setUp(self):
        self.client = Client()
        self.endpoint_url = reverse("oekg:sparql_endpoint")

    @patch("oekg.views.execute_sparql_query")
    def test_a_valid_query_is_answered_as_json(self, execute_sparql_query):
        execute_sparql_query.return_value = (
            '{"head": {"vars": ["sub", "pred", "obj"]}, "results": {"bindings": []}}',
            "application/sparql-results+json",
        )

        response = self.client.post(self.endpoint_url, {"query": QUERY})

        self.assertEqual(response.status_code, 200)
        self.assertIn("head", response.json())
        self.assertIn("results", response.json())

    @patch("oekg.views.execute_sparql_query")
    def test_the_view_does_not_reach_the_store_itself(self, execute_sparql_query):
        # Guards the patch target: if the binding moves back to oekg.utils, or
        # the view starts calling something else, this fails instead of
        # silently going over the network again.
        execute_sparql_query.return_value = ("{}", "application/sparql-results+json")

        self.client.post(self.endpoint_url, {"query": QUERY})

        execute_sparql_query.assert_called_once()

    @patch("oekg.views.execute_sparql_query")
    def test_an_unusable_query_is_a_bad_request(self, execute_sparql_query):
        execute_sparql_query.side_effect = ValueError("Missing 'query' parameter.")

        response = self.client.post(self.endpoint_url, {"query": ""})

        self.assertEqual(response.status_code, 400)
