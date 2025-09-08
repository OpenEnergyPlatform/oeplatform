# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg  # noqa:E501
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa:E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import re
from datetime import datetime

try:
    from rdflib.term import Literal as RDFLiteral
except Exception:
    RDFLiteral = None
    XSD = None


def serialize_publication_date(value) -> str:
    """
    Return year 'YYYY' or 'None' from various date representations:
    - rdflib Literals with xsd:date, xsd:dateTime, xsd:gYear, xsd:gYearMonth
    - 'YYYY', 'YYYY-MM', 'YYYY-MM-DD', 'YYYY/M/D'
    - ISO 8601 datetime (with Z or offsets), optional fractional seconds
    - Typed literal strings like: "2023-01-01T00:00:00"^^<...#dateTime>
    """
    if not value:
        return "None"

    # 1) rdflib Literal: use toPython() when possible
    if RDFLiteral and isinstance(value, RDFLiteral):
        try:
            py = value.toPython()
            if hasattr(py, "year"):
                return f"{int(py.year):04d}"  # date/datetime
            if isinstance(py, int):  # gYear sometimes becomes int
                return f"{py:04d}"
        except Exception:
            pass
        # fallback to string form
        s = str(value)
    else:
        s = str(value)

    s = s.strip()

    # 2) Strip ^^datatype and outer quotes if present
    if "^^" in s:
        s = s.split("^^", 1)[0].strip()
    s = s.strip('"').strip("'")

    # 3) Normalize 2023/8/5 -> 2023-08-05 (keeps year extraction simple)
    if "/" in s and re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", s):
        y, mth, day = s.split("/")
        s = f"{y}-{int(mth):02d}-{int(day):02d}"

    # 4) Try Python's ISO parser (handles YYYY-MM-DD[THH:MM:SS[.fff]][±HH:MM])
    iso = s[:-1] + "+00:00" if s.endswith("Z") else s
    try:
        dt = datetime.fromisoformat(iso)
        return f"{dt.year:04d}"
    except Exception:
        pass

    # 5) Regex fallbacks for YYYY-MM(-DD)(T...) and bare YYYY
    m = re.match(r"^\s*(\d{4})-(\d{2})(?:-(\d{2}))?(?:T.*)?\s*$", s)
    if m:
        return m.group(1)

    m = re.match(r"^\s*(\d{4})\s*$", s)
    if m:
        return m.group(1)

    return "None"


def remove_non_printable(text):
    """
    This function removes non-printable characters from a string which cause the
    app to break. Mostly relevant for free text fields.

    Do not use this on date fields, as it will remove the date format.
    """
    if text is not None:
        allowed_chars = re.compile(r'[a-zA-Z0-9äöüÄÖÜß.,;:!?\'"()\-\s_]')
        return "".join(char if allowed_chars.match(char) else "" for char in text)
    return None
