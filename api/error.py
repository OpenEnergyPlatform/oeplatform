__license__ = """
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

import psycopg2

# Postgres error codes whose message describes something wrong with the request
# rather than with the server, and is therefore safe to show a client.
_REFLECTABLE_PGCODES = frozenset(
    {
        "42703",  # undefined_column
        "42704",  # undefined_object
        "42804",  # datatype_mismatch
        "42883",  # undefined_function
        "42P01",  # undefined_table
        "42P02",  # undefined_parameter
    }
)

# PostGIS raises everything through the generic internal-error code (XX000),
# which also covers genuine server faults, so its messages can only be
# recognised by text. Every entry here is a deliberate decision to disclose a
# specific message - do not widen this to "all internal errors".
_REFLECTABLE_MESSAGES = (
    re.compile(r"Input geometry has unknown \(\d+\) SRID"),
    re.compile(r"could not parse proj string"),
)


def reflectable_cause(error: BaseException) -> str | None:
    """The database's own reason for an error, if it is safe to show a client.

    Returns None when the cause must stay internal, in which case the caller
    keeps whatever generic message it already reports.

    This is the single place that answers "may this cause be disclosed". Both
    the query path and the table-create path consult it, so the decision does
    not drift apart between them.
    """

    # SQLAlchemy wraps DBAPI errors; the driver error carries the diagnostics
    error = getattr(error, "orig", error)

    if isinstance(error, (psycopg2.DataError, psycopg2.IntegrityError)):
        return str(error)

    if isinstance(error, psycopg2.ProgrammingError):
        if error.pgcode in _REFLECTABLE_PGCODES:
            return error.diag.message_primary
        return None

    if isinstance(error, psycopg2.InternalError):
        message = str(error)
        if any(pattern.search(message) for pattern in _REFLECTABLE_MESSAGES):
            return message
        return None

    return None


class APIError(Exception):
    """Instances of APIError will be caught
    and the error messages will be delivered as payload to the user.
    """

    def __init__(self, message, status=400):
        self.message = message
        self.status = status


class APIKeyError(APIError):
    def __init__(self, dictionary, key):
        self.message = "Key '%s' not found in %s" % (key, dictionary)
        self.status = 401
