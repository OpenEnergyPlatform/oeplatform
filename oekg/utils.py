import re

import requests

from oeplatform.settings import OEKG_SPARQL_ENDPOINT_URL

# Whitelist of supported formats
SUPPORTED_FORMATS = {
    "json": "application/sparql-results+json",
    "json-ld": "application/ld+json",
    "xml": "application/rdf+xml",
    "turtle": "text/turtle",
}


def execute_sparql_query(sparql_query, response_format):
    """
    Executes the SPARQL query and returns the appropriate response.

    :param sparql_query: The SPARQL query string.
    :param response_format: The requested response format.
    :return: Tuple (response content, content_type)
    """
    if not sparql_query:
        raise ValueError("Missing 'query' parameter.")

    if response_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {response_format}")

    endpoint_url = OEKG_SPARQL_ENDPOINT_URL
    headers = {
        "Accept": SUPPORTED_FORMATS[response_format],
        # "Content-Type": SUPPORTED_FORMATS[response_format],
    }

    # Execute the SPARQL query
    response = requests.post(
        endpoint_url, data={"query": sparql_query}, headers=headers
    )

    return response.content, SUPPORTED_FORMATS[response_format]


def validate_sparql_query(query):
    """
    Validate the SPARQL query to prevent injection attacks.
    """

    # Basic length check
    if not query or len(query) > 10000:  # Set an appropriate limit for your use case
        return False

    # Basic SPARQL syntax check using a regular expression (this is a simplistic check)
    pattern = re.compile(
        r"^\s*(PREFIX\s+[^\s]+:\s*<[^>]+>\s*)*(SELECT|CONSTRUCT|ASK|DESCRIBE)\s+",
        re.IGNORECASE,
    )
    if not pattern.match(query):
        return False

    # Check for disallowed keywords (e.g., DROP, DELETE, INSERT)
    disallowed_keywords = ["DROP", "DELETE", "INSERT"]
    for keyword in disallowed_keywords:
        if re.search(rf"\b{keyword}\b", query, re.IGNORECASE):
            return False

    return True
