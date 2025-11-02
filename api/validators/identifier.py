from api.error import APIError
from oedb.utils import MAX_NAME_LENGTH, NAME_PATTERN


def assert_valid_identifier_name(identifier):
    """Raise APIError if table or schema name is invalid"""
    if not NAME_PATTERN.match(identifier) or len(identifier) > MAX_NAME_LENGTH:
        raise APIError(
            f"Unsupported identifier: {identifier}\n"
            "Names must consist of lowercase alpha-numeric words or underscores "
            "and start with a letter and must not exceed "
            f"{MAX_NAME_LENGTH} characters (current length: {len(identifier)})."
        )
