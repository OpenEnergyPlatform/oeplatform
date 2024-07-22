import re


def serialize_publication_date(triple_object_pub_year: str):
    """
    Serialize strings in different formats to return the year (yyyy) only.

    Args:
    triple_object_pub_year (str): A string representing the publication
    date in various formats.

    Returns:
    str: The year in yyyy format, or "None" if the date is invalid or empty.
    """

    # Return "None" if the input is an empty string
    if not triple_object_pub_year:
        return "None"

    # Regex patterns to match different date formats
    patterns = [
        r"^(?P<year>\d{4})-\d{2}-\d{2}$",  # Matches "2022-11-28"
        r"^(?P<year>\d{4})/\d{1,2}/\d{1,2}$",  # Matches "2023/8/15"
        r"^(?P<year>\d{4})$",  # Matches "2023"
        r"^(?P<year>\d{4})-\d{2}-\d{2}\^\^xsd:date$",  # Matches "2017-03-06^^xsd:date"
    ]

    # Attempt to match the input string with each pattern
    for pattern in patterns:
        match = re.match(pattern, triple_object_pub_year)
        if match:
            return match.group("year")

    # If none of the patterns match, return "None" for invalid date formats
    return "None"
