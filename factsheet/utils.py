from typing import Any, Optional


def get_valid(data: Any, key: Optional[str], expected_type: type) -> Optional[Any]:
    """
    Retrieve a value from a dictionary if it exists, is of the expected type,
    and is not empty or None.

    Args:
        data (Any): The dictionary or string to retrieve the value from.
        key (Optional[str]): The key for the value to retrieve, if applicable.
        expected_type (type): The expected type of the value.

    Returns:
        Optional[Any]: The value if it exists, is of the expected type, and is not
        an empty string or None, otherwise None.
    """
    if key is not None and isinstance(data, dict):
        value = data.get(key)
    else:
        value = data

    if isinstance(value, expected_type) and value != "" and value is not None:
        print(value)
        return value
    return None
