"""The OEKG scenario-bundle API: create one, read one.

The order of operations in a create is the whole point of this slice, so it is
worth stating plainly:

1. the payload is checked for structure, and an unknown key is refused;
2. the acronym is checked for uniqueness, comparing like with like;
3. the server mints the identifier;
4. the **post-state** is assembled and validated against the shape;
5. only then is anything written, in **one** request.

Nothing is written before step 5, so an invalid payload leaves the graph
untouched -- not "mostly untouched", untouched. And because one request is one
transaction, a write that fails halfway leaves nothing behind either.

Reads need no authentication: the SPARQL endpoint already serves the same data,
so requiring a token here would protect nothing while making public research
records awkward to read.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging

from django.urls import reverse
from rdflib import Literal
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from factsheet.models import ScenarioBundleAccessControl
from oekg.bundles import (
    BUNDLE_CLASS,
    DC,
    bundle_iri,
    bundle_payload,
    build_bundle_graph,
    mint_bundle_uid,
)
from oekg.graph_store import GraphStore, GraphStoreError
from oekg.serializers import READ_ONLY_CONTAINER, ScenarioBundleSerializer
from oekg.shape import ShapeUnavailable
from oekg.validation import validate_post_state

logger = logging.getLogger("oeplatform")


class ScenarioBundleCollectionAPIView(APIView):
    """`POST` creates a scenario bundle."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ScenarioBundleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        store = GraphStore.from_settings()
        acronym = payload["acronym"].strip()
        try:
            if _acronym_taken(store, acronym):
                return Response(
                    {
                        "detail": (
                            f"A scenario bundle with the acronym {acronym!r} "
                            "already exists. Acronyms identify a bundle to a "
                            "pipeline, so they have to be unique."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            uid = mint_bundle_uid()
            post_state = build_bundle_graph(uid, payload)

            violations = validate_post_state(post_state)
            if violations:
                return Response(
                    {
                        "detail": "The bundle does not conform to the OEKG shape.",
                        "violations": [v.as_dict() for v in violations],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            store.insert(post_state)
        except ShapeUnavailable as error:
            logger.error("OEKG API cannot validate: %s", error)
            return Response(
                {"detail": "The OEKG shape is not available on this server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except GraphStoreError as error:
            logger.error("OEKG API write failed: %s", error)
            return Response(
                {"detail": "The OEKG graph store could not be written to."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Ownership is recorded now so the creator can edit later. A bundle with
        # no ownership record is administrator-only by design, which would make
        # every bundle this API creates uneditable by the person who created it.
        ScenarioBundleAccessControl.objects.create(
            owner_user=request.user, bundle_id=uid
        )

        location = reverse("api:scenario-bundle", kwargs={"uid": uid})
        response = Response(
            _represent(uid, bundle_payload(post_state, uid)),
            status=status.HTTP_201_CREATED,
        )
        response["Location"] = location
        return response


class ScenarioBundleAPIView(APIView):
    """`GET` returns one scenario bundle. Public."""

    permission_classes = [AllowAny]

    def get(self, request, uid):
        store = GraphStore.from_settings()
        try:
            subgraph = store.construct(
                "CONSTRUCT { ?s ?p ?o } WHERE { "
                f"  VALUES ?root {{ {bundle_iri(uid).n3()} }} "
                "  { ?root ?p ?o . BIND(?root AS ?s) } "
                "  UNION "
                "  { ?root ?q ?s . ?s ?p ?o } "
                "}"
            )
        except GraphStoreError as error:
            logger.error("OEKG API read failed: %s", error)
            return Response(
                {"detail": "The OEKG graph store could not be read."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if (bundle_iri(uid), None, None) not in subgraph:
            return Response(
                {"detail": f"No scenario bundle {uid}."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_represent(uid, bundle_payload(subgraph, uid)))


def _acronym_taken(store: GraphStore, acronym: str) -> bool:
    """Whether a bundle already uses this acronym.

    Compares the stored literal with the literal a write would store -- like
    with like. The user interface's check normalises one side and not the other,
    so any acronym with a space, hyphen, umlaut, slash, colon or parenthesis
    slips past it.
    """
    return store.ask(
        "ASK { ?bundle a %s ; %s %s }"
        % (BUNDLE_CLASS.n3(), DC.acronym.n3(), Literal(acronym).n3())
    )


def _represent(uid: str, payload: dict) -> dict:
    """A read returns exactly what a write accepts, plus one read-only key."""
    return {
        **payload,
        READ_ONLY_CONTAINER: {"uid": uid, "iri": str(bundle_iri(uid))},
    }
