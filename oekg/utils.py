import re


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
