import unittest
from unittest.mock import Mock, patch

from django.test import Client, TestCase
from django.urls import reverse


class SparqlEndpointTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.endpoint_url = reverse(
            "sparql_endpoint"
        )  # Ensure your URL name matches the one in your urls.py

    @patch("requests.get")
    def test_valid_sparql_query(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "head": {"vars": ["sub", "pred", "obj"]},
            "results": {"bindings": []},
        }
        mock_get.return_value = mock_response

        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT * WHERE {
          ?sub ?pred ?obj .
        }
        LIMIT 10
        """

        response = self.client.get(self.endpoint_url, {"query": query})
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertIn("head", json_response)
        self.assertIn("results", json_response)

    @patch("requests.get")
    def test_invalid_sparql_query_delete(self, mock_get):
        query = """
        DELETE WHERE {
          ?sub ?pred ?obj .
        }
        """

        response = self.client.get(self.endpoint_url, {"query": query})
        self.assertEqual(
            response.status_code, 400
        )  # Expecting 400 Bad Request for invalid queries


if __name__ == "__main__":
    unittest.main()
