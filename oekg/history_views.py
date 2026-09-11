"""Reading a bundle's history.

**Public, but per bundle and paginated.** The reasoning that makes bundle reads
public does not transfer: that one rests on the SPARQL endpoint already serving
the same data, and the history is in no graph -- it is in the relational
database, and what it exposes is not bundle content but *who edited what, and
when*. A per-bundle log is a record about a bundle; a global one is a profile
of a person's activity across the platform. So this endpoint is scoped to one
bundle, it is paginated with a ceiling, and the actor is a username rather than
the internal identifier the existing global dump hands out.

Changes are rendered in **field names, computed here at read time** from the
stored triples. The triples themselves stay reachable through `?expand=triples`
so that a legible summary never becomes the only account.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

from rdflib import Graph
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from factsheet.models import API_ERA, OEKG_Modifications
from oekg.api_views import (
    ScenarioBundleThrottle,
    ScenarioBundleUserThrottle,
    bundle_exists,
    no_such_bundle,
    store_unavailable,
)
from oekg.graph_store import GraphStoreError
from oekg.history import changed_fields

TRIPLES = "triples"


class HistoryPagination(PageNumberPagination):
    """A ceiling, not a default: there is no unbounded mode on a public read."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ScenarioBundleHistoryAPIView(APIView):
    """`GET` returns one bundle's change history."""

    permission_classes = [AllowAny]
    throttle_classes = [ScenarioBundleThrottle, ScenarioBundleUserThrottle]

    def get(self, request, uid):
        expand = request.query_params.get("expand")
        if expand not in (None, "", TRIPLES):
            return Response(
                {
                    "detail": (
                        f"{expand!r} is not something this endpoint can expand. "
                        f"The only value is {TRIPLES!r}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Existence is asked of the graph, not of the history: a bundle with no
        # entries is a real bundle the user interface wrote, and answering 404
        # for it would say it does not exist.
        try:
            if not bundle_exists(uid):
                return no_such_bundle(uid)
        except GraphStoreError as error:
            # "There is no such bundle" and "I could not find out" are
            # different answers, and only one of them is this endpoint's to
            # give when the graph is unreachable.
            return store_unavailable(error, "read")

        entries = OEKG_Modifications.objects.filter(bundle_id=uid).select_related(
            "user"
        )
        # Newest first: a history is read from the present backwards.
        entries = entries.order_by("-timestamp", "-id")

        paginator = HistoryPagination()
        page = paginator.paginate_queryset(entries, request, view=self)
        return paginator.get_paginated_response(
            [_represent(entry, uid, with_triples=expand == TRIPLES) for entry in page]
        )


def _represent(entry: OEKG_Modifications, uid: str, with_triples: bool) -> dict:
    body = {
        "era": entry.era,
        "verb": entry.verb,
        "actor": entry.user.name if entry.user else None,
        "timestamp": entry.timestamp,
        "resource": {"type": entry.resource_type, "uid": entry.resource_uuid},
        "version_before": entry.version_before,
        "version_after": entry.version_after,
        "changes": _changes(entry, uid),
    }
    if with_triples:
        body["triples"] = _triples(entry)
    return body


def _changes(entry: OEKG_Modifications, uid: str):
    """The field-level summary, or ``None`` where there cannot be one.

    ``None`` rather than an empty list for a pre-API row: an empty list would
    say that nothing changed, and what is actually known is that this row was
    written before anything recorded which fields it touched.
    """
    if entry.era != API_ERA:
        return None
    return changed_fields(uid, _graph(entry.removed), _graph(entry.added))


def _triples(entry: OEKG_Modifications) -> dict:
    """The stored payload, untouched -- whichever generation of row this is."""
    if entry.era == API_ERA:
        return {"removed": entry.removed, "added": entry.added}
    return {"removed": entry.old_state, "added": entry.new_state}


def _graph(payload) -> Graph:
    graph = Graph()
    if payload:
        # `parse` wants a document; the column holds already-parsed JSON.
        graph.parse(data=json.dumps(payload), format="json-ld")
    return graph
