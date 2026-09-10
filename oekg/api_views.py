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
import uuid

from django.db import DatabaseError
from django.urls import reverse
from rdflib import RDFS, Literal, URIRef
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from factsheet.models import ScenarioBundleAccessControl
from oekg.bundles import (
    BUNDLE_CLASS,
    DC,
    build_bundle_graph,
    bundle_iri,
    bundle_payload,
    mint_bundle_uid,
    referenced_node_iris,
)
from oekg.graph_store import GraphStore, GraphStoreError
from oekg.serializers import READ_ONLY_CONTAINER, ScenarioBundleSerializer
from oekg.shape import ShapeUnavailable
from oekg.validation import validate_post_state

logger = logging.getLogger("oeplatform")


class ScenarioBundleThrottle(AnonRateThrottle):
    """Reads are public, so the public endpoint needs a ceiling of its own."""

    scope = "oekg_bundles_anon"


class ScenarioBundleUserThrottle(UserRateThrottle):
    scope = "oekg_bundles_user"


class ScenarioBundleCollectionAPIView(APIView):
    """`POST` creates a scenario bundle."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScenarioBundleThrottle, ScenarioBundleUserThrottle]

    def post(self, request):
        serializer = ScenarioBundleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        store = GraphStore.from_settings()
        # Checked and stored as the same value. Stripping one side only is how
        # the user interface's check comes to miss duplicates.
        payload["acronym"] = payload["acronym"].strip()
        acronym = payload["acronym"]
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

            known_labels = _labels_of(store, referenced_node_iris(payload))
            renamed = _renames(payload, known_labels)
            if renamed:
                return Response(
                    {
                        "detail": (
                            "A shared node cannot be renamed through this API. "
                            "Reference it by iri and send the label it already "
                            "has, or omit the iri to mint a new node."
                        ),
                        "conflicts": renamed,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            uid = mint_bundle_uid()
            post_state = build_bundle_graph(uid, payload, known_labels)

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

        # Ownership is recorded now so the creator can edit later: a bundle with
        # no ownership record is administrator-only by design, which would make
        # every bundle this API creates uneditable by its author.
        #
        # The graph and the database cannot share a transaction. The graph has
        # already committed, so a failure here is logged and named in the
        # response rather than turned into a 500 that would deny a write that
        # did happen.
        owned = True
        try:
            ScenarioBundleAccessControl.objects.create(
                owner_user=request.user, bundle_id=uid
            )
        except DatabaseError:
            owned = False
            logger.exception(
                "OEKG bundle %s was written to the graph but its ownership row "
                "could not be saved. It is administrator-only until repaired.",
                uid,
            )

        location = reverse("api:scenario-bundle", kwargs={"uid": uid})
        body = _represent(uid, bundle_payload(post_state, uid))
        if not owned:
            body[READ_ONLY_CONTAINER]["ownership_recorded"] = False
        response = Response(body, status=status.HTTP_201_CREATED)
        response["Location"] = location
        return response


class ScenarioBundleAPIView(APIView):
    """`GET` returns one scenario bundle. Public."""

    permission_classes = [AllowAny]
    throttle_classes = [ScenarioBundleThrottle, ScenarioBundleUserThrottle]

    def get(self, request, uid):
        # Identifiers are minted here, so anything that is not one cannot name a
        # bundle. Checked before it reaches a query, where an IRI-unsafe
        # character would raise out of rdflib as a 500 rather than a 404.
        if not _is_minted_identifier(uid):
            return Response(
                {"detail": f"No scenario bundle {uid}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        store = GraphStore.from_settings()
        try:
            subgraph = store.construct(
                "CONSTRUCT { ?s ?p ?o } WHERE { "
                f"  VALUES ?root {{ {bundle_iri(uid).n3()} }} "
                f"  ?root a {BUNDLE_CLASS.n3()} . "
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


def _is_minted_identifier(uid: str) -> bool:
    try:
        uuid.UUID(str(uid))
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def _labels_of(store: GraphStore, iris: list) -> dict:
    """The label each of these nodes already carries, for the ones that exist."""
    if not iris:
        return {}
    values = " ".join(URIRef(iri).n3() for iri in iris)
    rows = store.select(
        "SELECT ?node ?label WHERE { VALUES ?node { %s } ?node %s ?label }"
        % (values, RDFS.label.n3())
    )
    return {row["node"]: row["label"] for row in rows}


def _renames(payload: dict, known_labels: dict) -> list:
    """Referenced nodes whose label the payload disagrees with.

    The API offers no rename. Shared IRIs stay shared -- that is the point of a
    graph -- but a shared contact or organisation is cited by other bundles, so
    letting one payload rewrite its label would change every one of them.
    """
    conflicts = []
    for iri in referenced_node_iris(payload):
        if iri not in known_labels:
            continue
        for entry in _entries_for(payload, iri):
            if entry["label"] != known_labels[iri]:
                conflicts.append(
                    {
                        "iri": iri,
                        "stored_label": known_labels[iri],
                        "sent_label": entry["label"],
                    }
                )
    return conflicts


def _entries_for(payload: dict, iri: str) -> list:
    return [
        entry
        for field_name in ("contacts", "organisations", "funders")
        for entry in (payload.get(field_name) or [])
        if entry.get("iri") == iri
    ]


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
