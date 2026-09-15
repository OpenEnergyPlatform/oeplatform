"""What a mutating request has to carry before it is allowed to proceed.

Two guards live here, and they defend different accidents. The version catches
*somebody changed this since you looked*. The retyped acronym catches *right
verb, wrong identifier* -- a pipeline looping over a list and reaching the
wrong entry -- which no version can catch, because the version it names is the
correct current version of the wrong bundle.

Only the whole-bundle delete asks for the second one. Ceremony is proportional
to blast radius: everything else in this API can be written again.

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

CONFIRM = "confirm"


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


def confirmation_refusal(request, acronym: str) -> Optional[Response]:
    """Why this delete may not proceed on its confirmation, if it may not.

    The acronym is retyped as a query parameter and compared **exactly** with
    the one stored. Exactly, because the whole value of the check is that it
    cannot be satisfied by a value the caller already had in hand for another
    bundle -- normalising it away would let `NEMO-2030` confirm a delete of
    `nemo 2030`, which is the confusion the check exists to catch.

    Both refusals are `400` rather than `412`: nothing here is a precondition
    on the bundle's state. A missing or wrong token is a badly formed request,
    and the bundle is exactly as the caller last read it.
    """
    if acronym is None:
        # Not reachable for a bundle this API created -- the shape requires an
        # acronym -- but the browser wrote most of the bundles in the graph and
        # the API judges a write by what it introduces, not by what it found.
        # Refusing here rather than inventing a substitute token keeps the
        # check meaning what it says; the way out is to give the bundle an
        # acronym with a `PATCH`, which is allowed precisely because the
        # missing one is a violation this caller did not introduce.
        return _bad_request(
            "This scenario bundle has no acronym, so there is nothing to "
            "confirm a delete with. Give it one with a PATCH first, then "
            "delete it."
        )
    given = request.query_params.get(CONFIRM)
    if given is None:
        return _bad_request(
            "Deleting a whole scenario bundle is irreversible, so it has to be "
            f"confirmed: repeat the bundle's acronym as ?{CONFIRM}=<acronym>. "
            "Read the bundle first -- the acronym is in the response, and so "
            "is the version this delete also needs."
        )
    if given != acronym:
        return _bad_request(
            f"The confirmation {given!r} is not this bundle's acronym, so "
            "nothing was deleted. Check that this is the bundle you meant to "
            "delete before retrying."
        )
    return None


def _bad_request(detail: str) -> Response:
    return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
