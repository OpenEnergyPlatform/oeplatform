"""The OEKG scenario-bundle API: create one, read one, change one field.

The order of operations in a create is the whole point, so it is worth stating
plainly:

1. the payload is checked for structure, and an unknown key is refused;
2. the acronym is checked for uniqueness, comparing like with like;
3. the server mints the identifier;
4. the **post-state** is assembled and validated against the shape;
5. only then is anything written, in **one** request -- and the acronym check
   is bound inside that request, so two concurrent creates cannot both take an
   acronym they both found free.

Nothing is written before step 5, so an invalid payload leaves the graph
untouched -- not "mostly untouched", untouched. And because one request is one
transaction, a write that fails halfway leaves nothing behind either.

A patch runs the same course with two additions: it reads the bundle first,
because the shape can only be checked against a whole bundle, and that read
opens a window. **The window is closed inside the write**, by binding the
version the read saw in the update's own guard -- see `oekg/versioning.py` for
why that guard needs a read-back to speak. Three refusals mean three different
things and get three statuses:

- **428** the client did not say which version it was editing;
- **412** it named a version, and that is not the current one;
- **409** the server's own guard fired -- the bundle moved between the read and
  the write. Re-read, re-apply, retry.

A patch touches only the keys it names. A key that is absent is untouched --
not read and rewritten, genuinely untouched -- which is also what stops an
unrelated patch from re-minting every framework and model in the bundle.

Reads need no authentication: the SPARQL endpoint already serves the same data,
so requiring a token here would protect nothing while making public research
records awkward to read.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
from typing import Optional

from django.db import DatabaseError
from django.urls import reverse
from rdflib import RDFS, Graph, Literal, URIRef
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from factsheet.models import ScenarioBundleAccessControl
from oekg.api_support import (
    ScenarioBundleThrottle,
    ScenarioBundleUserThrottle,
    is_minted_identifier,
    no_such_bundle,
    shape_unavailable,
    store_unavailable,
)
from oekg.bundles import (
    BUNDLE_CLASS,
    DC,
    build_bundle_graph,
    bundle_delta,
    bundle_iri,
    bundle_payload,
    bundle_subgraph,
    mint_bundle_uid,
    referenced_node_iris,
)
from oekg.graph_store import GraphStore, GraphStoreError
from oekg.history import CREATE, UPDATE, record_write
from oekg.permissions import may_write_bundle
from oekg.serializers import READ_ONLY_CONTAINER, ScenarioBundleSerializer
from oekg.shape import ShapeUnavailable
from oekg.validation import validate_post_state
from oekg.versioning import (
    FIRST_VERSION,
    UNVERSIONED,
    BundleVersion,
    guarded_operation,
    mint_write_token,
    read_version,
    version_triples,
    write_applied,
)

logger = logging.getLogger("oeplatform")


class ScenarioBundleCollectionAPIView(APIView):
    """`POST` creates a scenario bundle."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScenarioBundleThrottle, ScenarioBundleUserThrottle]

    def post(self, request):
        serializer = ScenarioBundleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        store = GraphStore.from_settings()
        # One value, checked and stored. The serializer has already trimmed
        # it, so the check and the write cannot compare different things --
        # which is the whole of the user interface's bug.
        acronym = payload["acronym"]
        try:
            if _acronym_taken(store, acronym):
                return _acronym_conflict(acronym)

            known_labels = _labels_of(store, referenced_node_iris(payload))
            renamed = _renames(payload, known_labels)
            if renamed:
                return _rename_refused(renamed)

            uid = mint_bundle_uid()
            post_state = build_bundle_graph(uid, payload, known_labels)

            violations = validate_post_state(post_state)
            if violations:
                return _does_not_conform(violations)

            # The uniqueness check above is friendly, not sufficient: it is a
            # separate request, so two creates can both pass it. The guard here
            # is part of the write, so only one of them lands.
            token = mint_write_token()
            store.update(
                store.guarded_modification(
                    _no_bundle_has_acronym(acronym),
                    insert=post_state + version_triples(uid, FIRST_VERSION, token),
                )
            )
            if not write_applied(store, uid, token):
                # The acronym is the ONLY condition in that guard, so a miss
                # can only mean the acronym was taken in between. Binding a
                # second condition into the same WHERE would make this answer
                # wrong, so it would have to distinguish them first.
                return _acronym_conflict(acronym)
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

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

        # The graph has committed. From here nothing may turn a successful
        # write into an error -- a failure is reported alongside the success it
        # qualifies, never instead of it.
        recorded = record_write(
            bundle_uid=uid,
            verb=CREATE,
            actor=request.user,
            version_before=UNVERSIONED,
            version_after=FIRST_VERSION,
            added=post_state,
        )

        version = BundleVersion(FIRST_VERSION, token)
        body = _represent(uid, bundle_payload(post_state, uid), version)
        if not owned:
            body[READ_ONLY_CONTAINER]["ownership_recorded"] = False
        _note_history_gap(body, recorded)
        response = Response(body, status=status.HTTP_201_CREATED)
        response["Location"] = reverse("api:scenario-bundle", kwargs={"uid": uid})
        response["ETag"] = version.etag
        return response


class ScenarioBundleAPIView(APIView):
    """`GET` returns one scenario bundle, publicly. `PATCH` changes a field."""

    throttle_classes = [ScenarioBundleThrottle, ScenarioBundleUserThrottle]

    def get_permissions(self):
        # The safe methods are named and everything else is closed, rather than
        # the other way round: a verb a later slice adds is then authenticated
        # by default instead of public until somebody remembers. The price is
        # that an unsupported verb answers 401 before it can answer 405, which
        # is the cheaper of the two mistakes.
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, uid):
        # Identifiers are minted here, so anything that is not one cannot name a
        # bundle. Checked before it reaches a query, where an IRI-unsafe
        # character would raise out of rdflib as a 500 rather than a 404.
        if not is_minted_identifier(uid):
            return no_such_bundle(uid)

        store = GraphStore.from_settings()
        try:
            subgraph = _read_bundle(store, uid)
            if subgraph is None:
                return no_such_bundle(uid)
            version = read_version(store, uid)
        except GraphStoreError as error:
            return store_unavailable(error, "read")

        return _bundle_response(uid, bundle_payload(subgraph, uid), version)

    def patch(self, request, uid):
        if not is_minted_identifier(uid):
            return no_such_bundle(uid)

        serializer = ScenarioBundleSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        if not payload:
            return Response(
                {
                    "detail": (
                        "A patch has to name at least one field to change. "
                        "Read-only data is ignored on a write, so a payload "
                        f"carrying only {READ_ONLY_CONTAINER!r} changes nothing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        store = GraphStore.from_settings()
        try:
            # Existence first, as it is for the two-step delete: one order for
            # the whole API rather than one per endpoint. Reads are public, so
            # answering 404 before authorisation reveals nothing a GET would
            # not.
            pre_state = _read_bundle(store, uid)
            if pre_state is None:
                return no_such_bundle(uid)

            if not may_write_bundle(request.user, uid):
                return _not_the_owner()

            version = read_version(store, uid)
            refusal = _precondition_refusal(request, version)
            if refusal is not None:
                return refusal

            known_labels = _labels_of(store, referenced_node_iris(payload))
            renamed = _renames(payload, known_labels)
            if renamed:
                return _rename_refused(renamed)

            removed, added = bundle_delta(uid, payload, pre_state, known_labels)
            post_state = bundle_subgraph(pre_state - removed + added, uid)

            violations = validate_post_state(post_state)
            if violations:
                return _does_not_conform(violations)

            token = mint_write_token()
            store.update(
                guarded_operation(
                    store, uid, version, token, delete=removed, insert=added
                )
            )
            if not write_applied(store, uid, token):
                # The guard held nothing back that the client could have known
                # about: the bundle moved -- or went away -- after the read this
                # request had to make.
                return Response(
                    {
                        "detail": (
                            "The bundle changed while this request was being "
                            "prepared, so nothing was written. Read it again, "
                            "apply the change to what you get back, and retry."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        written = BundleVersion(version.number + 1, token)
        recorded = record_write(
            bundle_uid=uid,
            verb=UPDATE,
            actor=request.user,
            version_before=version.number,
            version_after=written.number,
            removed=removed,
            added=added,
        )
        return _bundle_response(
            uid,
            bundle_payload(post_state, uid),
            written,
            history_recorded=recorded,
        )


def _precondition_refusal(request, version: BundleVersion) -> Optional[Response]:
    """Why this request may not proceed on its precondition, if it may not."""
    named = _versions_named(request)
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
                    "nothing was written. It is at "
                    f"{version.etag}. Read it again and apply the change to "
                    "what you get back."
                )
            },
            status=status.HTTP_412_PRECONDITION_FAILED,
        )
    return None


def _versions_named(request):
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


def _read_bundle(store: GraphStore, uid: str) -> Optional[Graph]:
    """A bundle and one hop out, or ``None`` if there is no such bundle.

    One hop is the whole bundle: its fields are either literals, picked IRIs,
    or nodes carrying a type and a label. The version node is unreachable from
    here, because it points at the bundle rather than away from it -- which is
    what keeps bookkeeping out of the payload without any filtering.
    """
    subgraph = store.construct(
        "CONSTRUCT { ?s ?p ?o } WHERE { "
        f"  VALUES ?root {{ {bundle_iri(uid).n3()} }} "
        f"  ?root a {BUNDLE_CLASS.n3()} . "
        "  { ?root ?p ?o . BIND(?root AS ?s) } "
        "  UNION "
        "  { ?root ?q ?s . ?s ?p ?o } "
        "}"
    )
    if (bundle_iri(uid), None, None) not in subgraph:
        return None
    return subgraph


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

    **Asked on a create only.** A patch may still rename a bundle onto an
    acronym another one holds, so uniqueness holds from creation and not
    thereafter. That gap is deliberate and deferred: the read side is where the
    acronym becomes load-bearing, because that is where a pipeline looks a
    bundle up by it, so the check belongs with the endpoint that makes the
    promise. `PatchAcronymTest` in the tests pins the gap down as it stands.
    """
    return store.ask("ASK { %s }" % _acronym_pattern(acronym))


def _no_bundle_has_acronym(acronym: str) -> str:
    return "FILTER NOT EXISTS { %s }" % _acronym_pattern(acronym)


def _acronym_pattern(acronym: str) -> str:
    return "?bundle a %s ; %s %s" % (
        BUNDLE_CLASS.n3(),
        DC.acronym.n3(),
        Literal(acronym).n3(),
    )


def _represent(uid: str, payload: dict, version: BundleVersion) -> dict:
    """A read returns exactly what a write accepts, plus read-only data."""
    return {
        **payload,
        READ_ONLY_CONTAINER: {
            "uid": uid,
            "iri": str(bundle_iri(uid)),
            "version": version.number,
        },
    }


def _note_history_gap(body: dict, recorded: bool) -> dict:
    """Say so when the history was lost, and say nothing when it was not.

    The key appears only when it is ``False``. A client should not have to
    check something on every response to learn that the ordinary thing
    happened; it is there to name the exception.
    """
    if not recorded:
        body[READ_ONLY_CONTAINER]["history_recorded"] = False
    return body


def _bundle_response(
    uid: str,
    payload: dict,
    version: BundleVersion,
    history_recorded: bool = True,
) -> Response:
    """The body, plus the entity tag every read has to carry."""
    body = _note_history_gap(_represent(uid, payload, version), history_recorded)
    response = Response(body)
    response["ETag"] = version.etag
    return response


def _not_the_owner() -> Response:
    return Response(
        {
            "detail": (
                "Only an owner of this scenario bundle may change it. A bundle "
                "with no recorded owner can be changed by an administrator "
                "only."
            )
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _acronym_conflict(acronym: str) -> Response:
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


def _rename_refused(renamed: list) -> Response:
    return Response(
        {
            "detail": (
                "A shared node cannot be renamed through this API. Reference "
                "it by iri and send the label it already has, or omit the iri "
                "to mint a new node."
            ),
            "conflicts": renamed,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _does_not_conform(violations: list) -> Response:
    return Response(
        {
            "detail": "The bundle does not conform to the OEKG shape.",
            "violations": [violation.as_dict() for violation in violations],
        },
        status=status.HTTP_400_BAD_REQUEST,
    )
