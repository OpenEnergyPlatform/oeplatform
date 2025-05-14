import re

from api.error import APIError

# Pattern for valid table/schema identifiers
MAX_IDENTIFIER_LENGTH = 50  # postgres limit minus pre/suffix for meta tables
IDENTIFIER_PATTERN = re.compile("^[a-z][a-z0-9_]{0,%s}$" % (MAX_IDENTIFIER_LENGTH - 1))


def assert_valid_identifier_name(identifier):
    """Raise APIError if table or schema name is invalid"""
    if (
        not IDENTIFIER_PATTERN.match(identifier)
        or len(identifier) > MAX_IDENTIFIER_LENGTH
    ):
        raise APIError(
            f"Unsupported identifier: {identifier}\n"
            "Names must consist of lowercase alpha-numeric words or underscores "
            "and start with a letter and must not exceed "
            f"{MAX_IDENTIFIER_LENGTH} characters (current length: {len(identifier)})."
        )
