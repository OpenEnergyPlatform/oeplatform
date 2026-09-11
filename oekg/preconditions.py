"""The version a mutating request says it is editing.

`If-Match` is **required** on every mutating call and there is no opt-out. The
alternative — optional, with same-field writes falling back to last-write-wins
— was on the table with a worked example and declined: a client that does not
know about the header would then overwrite somebody's change and neither of
them would be told. The cost is named rather than discovered: deliberate
overwriting is not reachable, and a repair pipeline that wants it must read
first, every time.

Three refusals, because they mean three different things to a client:

- **428** you did not say which version you were editing;
- **412** you said one, and it is not the current version;
- **409** the server's own guard fired — the bundle moved between the read the
  validation needed and the write. That one is raised at the write, not here.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import Optional

from rest_framework import status
from rest_framework.response import Response

from oekg.versioning import BundleVersion


def precondition_refusal(request, version: BundleVersion) -> Optional[Response]:
    """Why this request may not proceed on its precondition, if it may not."""
    named = versions_named(request)
    if named is None:
        return Response(
            {
                "detail": (
                    "This write needs an If-Match header carrying the version "
                    "you read, so that it cannot silently overwrite a change "
                    f"made since. The bundle is at {version.etag}."
                )
            },
            status=status.HTTP_428_PRECONDITION_REQUIRED,
        )
    if str(version.number) not in named:
        return Response(
            {
                "detail": (
                    "The bundle is not at the version this request expects, so "
                    f"nothing was written. It is at {version.etag}. Read it "
                    "again and apply the change to what you get back."
                )
            },
            status=status.HTTP_412_PRECONDITION_FAILED,
        )
    return None


def versions_named(request):
    """The versions an ``If-Match`` names, or ``None`` if it names none.

    Lenient in what it accepts and strict in what it emits: a weak validator or
    a bare number is read as the version it plainly is, while a value that is
    not a version simply matches nothing and is refused as stale.

    ``*`` names no version. It is a legal header value, and it satisfies the
    letter of the precondition while withholding the one thing the precondition
    is for, so it reads here as an absent header rather than as a match.
    """
    header = request.headers.get("If-Match")
    if header is None:
        return None
    named = []
    for entry in header.split(","):
        entry = entry.strip()
        if entry == "*":
            return None
        if entry.startswith("W/"):
            entry = entry[2:].strip()
        named.append(entry.strip('"'))
    return named
