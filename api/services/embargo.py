from datetime import datetime, timedelta

from api.error import APIError
from dataedit.models import Embargo


class EmbargoValidationError(APIError):
    """Raised when embargo payload is invalid"""

    pass


def parse_embargo_payload(embargo_data):
    """
    Validate embargo_data dict and return True if an embargo should be applied.
    Raises EmbargoValidationError on invalid format.
    """
    if not embargo_data:
        return False

    if not isinstance(embargo_data, dict):
        raise EmbargoValidationError("The embargo payload must be a dict")

    duration = embargo_data.get("duration")
    if duration in ("6_months", "1_year"):
        return True
    if duration == "none":
        return False

    raise EmbargoValidationError(
        f"Invalid embargo duration: '{duration}'. Use '6_months', '1_year', or 'none'."
    )


def apply_embargo(table_object, embargo_data):
    """
    Create or update an Embargo for the given table_object based on embargo_data.
    """
    duration = embargo_data.get("duration")
    weeks = 26 if duration == "6_months" else 52
    now = datetime.now()

    embargo, created = Embargo.objects.get_or_create(
        table=table_object,
        defaults={
            "duration": duration,
            "date_started": now,
            "date_ended": now + timedelta(weeks=weeks),
        },
    )

    if not created:
        # Update existing embargo
        start = embargo.date_started or now
        embargo.date_started = start
        embargo.date_ended = start + timedelta(weeks=weeks)
        embargo.duration = duration
        embargo.save()
