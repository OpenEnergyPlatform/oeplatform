"""The acronym: the one name a pipeline can find a bundle by.

An acronym is the only handle a stateless client has. A modelling pipeline
holds nothing between runs, so it re-identifies its bundle with
`GET /scenario-bundles/?acronym=...` and writes to whatever comes back. That
makes uniqueness **load-bearing rather than tidy**: two bundles sharing an
acronym do not make a lookup ambiguous to a human reading a list, they make a
pipeline write its results into somebody else's record.

So every write that can change an acronym asks here, and asks the same way:

- **Compared like with like.** The value checked is the value stored -- the
  serializer has already trimmed it, and nothing is normalised on one side
  only. The user interface's own check normalises one side and not the other,
  which is why any acronym with a space, a hyphen or an umlaut slips past it.
- **Bound inside the write, not asked in front of it.** A separate question is
  a separate request, so two writes can both find an acronym free and both take
  it. `acronym_is_free` returns a pattern for the update's own ``WHERE``, where
  the store decides it in the same transaction as the change.
- **A bundle's own acronym is not taken by somebody else.** ``excluding`` is
  what lets a client send back what it read -- the round trip the read side
  promises, and the one `replace` is built on.

The friendly check in front is still worth making: it answers with the acronym
in the message, while the bound guard can only say that something moved.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import Optional

from rdflib import Literal
from rest_framework import status
from rest_framework.response import Response

from oekg.bundles import BUNDLE_CLASS, bundle_iri
from oekg.fields import DC
from oekg.graph_store import GraphStore

ACRONYM = DC.acronym

# Named so it cannot collide with the variables other guards bind into the same
# WHERE -- the removal walk's `?ref<n>` today, and whatever a later slice adds.
HOLDER = "?acronymHolder"


def acronym_taken(
    store: GraphStore, acronym: str, excluding: Optional[str] = None
) -> bool:
    """Whether another bundle already uses this acronym.

    ``excluding`` names a bundle that does not count against itself, so a write
    that sends an acronym back unchanged is not refused by its own value.
    """
    return store.ask("ASK { %s }" % _pattern(acronym, excluding))


def acronym_is_free(acronym: str, excluding: Optional[str] = None) -> str:
    """The same question as a pattern a write can bind into its own guard."""
    return "FILTER NOT EXISTS { %s }" % _pattern(acronym, excluding)


def acronym_conflict(acronym: str) -> Response:
    return Response(
        {
            "detail": (
                f"A scenario bundle with the acronym {acronym!r} already "
                "exists. Acronyms identify a bundle to a pipeline, so they "
                "have to be unique."
            )
        },
        status=status.HTTP_409_CONFLICT,
    )


def _pattern(acronym: str, excluding: Optional[str]) -> str:
    pattern = "%s a %s ; %s %s" % (
        HOLDER,
        BUNDLE_CLASS.n3(),
        ACRONYM.n3(),
        Literal(acronym).n3(),
    )
    if excluding is not None:
        pattern = "%s . FILTER (%s != %s)" % (
            pattern,
            HOLDER,
            bundle_iri(excluding).n3(),
        )
    return pattern
