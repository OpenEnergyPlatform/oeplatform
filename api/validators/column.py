import re

from api.error import APIError
from oedb.utils import MAX_COL_NAME_LENGTH


def validate_column_names(column_definitions):
    """Raise APIError if any column name is invalid"""
    for col_def in column_definitions:
        colname = col_def.get("name")
        if not colname:
            raise APIError("Column definition missing 'name' key")

        err_msg = (
            f"Unsupported column name: '{colname}'. "
            "Column name must consist of lowercase alphanumeric words or underscores "
            "and start with a letter. It must not start with an underscore or exceed "
            f"{MAX_COL_NAME_LENGTH} characters."
        )

        # Must be a valid Python identifier
        if not colname.isidentifier():
            raise APIError(err_msg)

        # No uppercase or leading underscore
        if re.search(r"[A-Z]", colname) or colname.startswith("_"):
            raise APIError(err_msg)

        # Check length
        if len(colname) > MAX_COL_NAME_LENGTH:
            raise APIError(err_msg)
