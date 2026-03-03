from api.error import APIError
from oedb.utils import MAX_NAME_LENGTH, is_valid_name


def assert_valid_table_name(identifier):
    """Raise APIError if table or schema name is invalid"""
    if not is_valid_name(identifier):
        raise APIError(
            f"Unsupported identifier: {identifier}\n"
            "Names must consist of lowercase alpha-numeric words or underscores "
            "and start with a letter and must not exceed "
            f"{MAX_NAME_LENGTH} characters (current length: {len(identifier)})."
        )
