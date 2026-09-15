"""The OEKG scenario-bundle API: create one, read one, change it, delete it.

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

A patch that renames a bundle answers for the acronym's uniqueness the same
way a create does, and for the same reason: the acronym is how a stateless
pipeline finds its bundle again, so two bundles sharing one is not untidy, it
is a pipeline writing into a stranger's record. See `oekg/acronyms.py`.

A patch touches only the keys it names. A key that is absent is untouched --
not read and rewritten, genuinely untouched -- which is also what stops an
unrelated patch from re-minting every framework and model in the bundle.

A delete is deliberately awkward, because it is the one irreversible thing this
API does. It takes **two steps**: the read a client needs anyway, which returns
the version and the acronym, and then the delete carrying both. They guard
different accidents -- the version catches a bundle that moved since it was
read, the retyped acronym catches the wrong bundle entirely -- and the second
is the one a version cannot give, because a pipeline looping over identifiers
holds the correct current version of the wrong bundle. What a delete actually
removes is bounded by type, in `oekg.removal`, so a bundle's delete can never
destroy what another bundle shares with it.

Reads need no authentication: the SPARQL endpoint already serves the same data,
so requiring a token here would protect nothing while making public research
records awkward to read. A read also serves the bundle's subgraph as RDF on
`Accept: text/turtle` or `application/ld+json` -- the lossless form, and nearly
free, because the read has constructed that subgraph anyway.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging

from django.db import DatabaseError
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse
from rdflib import Graph
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from factsheet.models import ScenarioBundleAccessControl
from oekg.acronyms import acronym_conflict, acronym_is_free, acronym_taken
from oekg.api_support import (
    OekgAPIView,
    is_minted_identifier,
    is_safe,
    no_such_bundle,
    shape_unavailable,
    store_unavailable,
)
from oekg.bundles import (
    BUNDLE_FIELDS,
    BUNDLE_PARTS,
    build_bundle_graph,
    bundle_delta,
    bundle_iri,
    bundle_payload,
)
from oekg.fields import mint_identifier, referenced_node_iris
from oekg.graph_store import GraphStore, GraphStoreError
from oekg.history import CREATE, UPDATE, record_write
from oekg.labels import LABELS, labelled
from oekg.part_views import part_bodies
from oekg.preconditions import CONFIRM
from oekg.reads import labels_of, read_bundle
from oekg.renderers import RDF_FORMATS, RDF_RENDERERS
from oekg.schema import (
    ALWAYS,
    EXPAND_LABELS,
    describes,
    describes_a_creation,
    describes_a_guarded_write,
    describes_a_public_read,
    paging,
)
from oekg.serializers import (
    READ_ONLY_CONTAINER,
    ScenarioBundleCreateSerializer,
    ScenarioBundleSerializer,
)
from oekg.shape import ShapeUnavailable
from oekg.summaries import (
    LISTING_FILTERS,
    BundleSummaries,
    ScenarioBundlePagination,
    SummaryFilters,
)
from oekg.validation import validate_post_state
from oekg.versioning import (
    FIRST_VERSION,
    UNVERSIONED,
    BundleVersion,
    mint_write_token,
    read_version,
    version_triples,
    write_applied,
)
from oekg.writes import open_bundle, refuse_renames

logger = logging.getLogger("oeplatform")


class ScenarioBundleCollectionAPIView(OekgAPIView):
    """`GET` lists scenario bundles as summaries. `POST` creates one."""

    # Nothing, and the refusal says so rather than ignoring the parameter.
    # Expanding a listing is the thing a summary exists not to be: the
    # expensive path would then live on the public, unauthenticated endpoint
    # and eventually be pointed at the whole corpus. A resource read is where
    # a term gets resolved.
    offers_expansions = ()

    def get_permissions(self):
        if is_safe(self.request):
            return [AllowAny()]
        return [IsAuthenticated()]

    # Named, because a collection read and a detail read would otherwise both
    # generate `scenario_bundles_retrieve` and the description would resolve
    # the collision with a numeral -- a name no reader could map back.
    @describes_a_public_read(
        describes(
            "A page of summaries. Each carries the two fields a human "
            "recognises a bundle by at the top level -- `label` and `acronym` "
            "-- and everything a client cannot write in `_meta`: the "
            "identifier, the version, and the number of scenarios and study "
            "reports the bundle holds."
        ),
        operation_id="scenario_bundles_list",
        parameters=[
            *LISTING_FILTERS,
            *paging(
                ScenarioBundlePagination.page_size,
                ScenarioBundlePagination.max_page_size,
            ),
        ],
        # No `404`: a filter matching nothing is an empty page, not a missing
        # collection. No entity tag either -- a listing is not one bundle's
        # state, and each summary carries its own version in `_meta` instead.
        refusals=(400, *ALWAYS),
        entity_tag=False,
    )
    def get(self, request):
        """A page of summaries: identifier, acronym, label, version and counts.

        Not bundles. A listing that returned whole bundles would carry every
        client the whole corpus, and would drag the relational resolution a
        dataset link needs across every link of every bundle on a public
        endpoint -- which is how the two listings next door on this platform
        became unusable.

        `?acronym=` is the filter the contract depends on: it is how a pipeline
        holding no state between runs finds its own bundle again, and the
        `_meta` it gets back carries the version its next write must send.
        """
        filters = SummaryFilters.from_query(request.query_params)
        paginator = ScenarioBundlePagination()
        try:
            summaries = BundleSummaries(GraphStore.from_settings(), filters)
            page = paginator.paginate_queryset(summaries, request, view=self)
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        return paginator.get_paginated_response(page)

    @describes_a_creation(
        {
            201: describes(
                "Created. The body is the bundle as it now stands -- exactly "
                "what a write accepts, plus `_meta`. `Location` names its URL "
                "and `ETag` the version the next write has to send back."
            )
        },
        request=ScenarioBundleCreateSerializer,
        responses={
            409: describes(
                "Another bundle already has this acronym, so nothing was "
                "written. The acronym is how a stateless pipeline finds its "
                "own bundle again, so two bundles sharing one is not untidy: "
                "it is a pipeline writing into a stranger's record."
            )
        },
    )
    def post(self, request):
        """Create a whole scenario bundle, its scenarios and study reports with it.

        Nothing is written until the payload has been checked for structure,
        the acronym for uniqueness and the assembled **post-state** against the
        OEKG shape -- so an invalid payload leaves the graph untouched, not
        mostly untouched. The write itself is one request, which the store
        makes one transaction, and the acronym check is bound inside it: two
        concurrent creates cannot both take an acronym they both found free.

        **The server mints the identifier.** A client sends none anywhere in
        this API, and `uid` is a rejected key rather than an ignored one. A
        pipeline that keeps no state re-identifies its bundle afterwards with
        `GET /api/v0/scenario-bundles/?acronym=...`.

        Nested `scenarios` and `study_reports` are accepted here and **only**
        here: a `PATCH` refuses them, so no single call can drop a bundle's
        parts by omitting them. Dataset links are not accepted -- they hang off
        a scenario and have their own endpoint.

        Unlike every other write, a create is judged strictly: there is no
        pre-state, so there is nothing it can have inherited and every
        violation of the shape is its own.
        """
        serializer = ScenarioBundleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        store = GraphStore.from_settings()
        # One value, checked and stored. The serializer has already trimmed
        # it, so the check and the write cannot compare different things --
        # which is the whole of the user interface's bug.
        acronym = payload["acronym"]
        try:
            if acronym_taken(store, acronym):
                return acronym_conflict(acronym)

            known_labels = labels_of(store, _all_referenced_iris(payload))
            refuse_renames(payload, known_labels, BUNDLE_FIELDS)
            for part in BUNDLE_PARTS:
                for nested in payload.get(part.payload_key) or []:
                    refuse_renames(nested, known_labels, part.fields)

            uid = mint_identifier()
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

            # The uniqueness check above is friendly, not sufficient: it is a
            # separate request, so two creates can both pass it. The guard here
            # is part of the write, so only one of them lands.
            token = mint_write_token()
            store.update(
                store.guarded_modification(
                    acronym_is_free(acronym),
                    insert=post_state + version_triples(uid, FIRST_VERSION, token),
                )
            )
            if not write_applied(store, uid, token):
                # The acronym is the ONLY condition in that guard, so a miss
                # can only mean the acronym was taken in between. A patch
                # cannot answer this precisely, because its guard carries the
                # version too -- see there.
                return acronym_conflict(acronym)
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
        body = _represent(uid, post_state, version)
        if not owned:
            body[READ_ONLY_CONTAINER]["ownership_recorded"] = False
        _note_history_gap(body, recorded)
        response = Response(body, status=status.HTTP_201_CREATED)
        response["Location"] = reverse("api:scenario-bundle", kwargs={"uid": uid})
        response["ETag"] = version.etag
        return response


class ScenarioBundleAPIView(OekgAPIView):
    """`GET` reads one, publicly. `PATCH` changes a field. `DELETE` removes it."""

    offers_expansions = (LABELS,)

    def get_permissions(self):
        if is_safe(self.request):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_renderers(self):
        """RDF is offered on reads only.

        A write is structured data because the serializers are the validation
        layer, so a `PATCH` asking for turtle gets a `406` -- which is the
        truthful answer, rather than a write whose response silently arrives in
        a form its request could not have been sent in.
        """
        renderers = super().get_renderers()
        if is_safe(self.request):
            renderers += [renderer() for renderer in RDF_RENDERERS]
        return renderers

    @describes_a_public_read(
        OpenApiResponse(
            # Not a JSON schema: this one response is served in three forms,
            # two of them text. `Accept: text/turtle` or `application/ld+json`
            # returns the bundle's subgraph as it is stored -- lossless, and
            # nearly free, because the read has constructed that subgraph
            # anyway. The structured form is canonical for writes, because the
            # serializers are this API's validation layer.
            response=OpenApiTypes.ANY,
            description=(
                "The bundle: exactly what a write accepts, plus `_meta`, with "
                "its scenarios and study reports nested so that a client can "
                "send back what it read without stripping anything. `ETag` "
                "carries the version the next write has to send. On `Accept: "
                "text/turtle` or `application/ld+json` the same bundle comes "
                "back as its stored subgraph instead; `expand` has nothing to "
                "do there, because triples are already what they are."
            ),
        ),
        parameters=[EXPAND_LABELS],
    )
    def get(self, request, uid):
        """Read one bundle, publicly.

        Dataset links are **not** in this body: they hang off a scenario and
        are read at their own endpoint.
        """
        # Identifiers are minted here, so anything that is not one cannot name a
        # bundle. Checked before it reaches a query, where an IRI-unsafe
        # character would raise out of rdflib as a 500 rather than a 404.
        if not is_minted_identifier(uid):
            return no_such_bundle(uid)

        store = GraphStore.from_settings()
        try:
            subgraph = read_bundle(store, uid)
            if subgraph is None:
                return no_such_bundle(uid)
            version = read_version(store, uid)
        except GraphStoreError as error:
            return store_unavailable(error, "read")

        if request.accepted_renderer.format in RDF_FORMATS:
            # The stored form, served as stored. `expand` has nothing to do
            # here: resolution is a property of the structured representation,
            # and the triples a bundle holds are already what they are.
            response = Response(subgraph)
            response["ETag"] = version.etag
            return response
        return _bundle_response(uid, subgraph, version, expand=self.expand)

    @describes_a_guarded_write(
        {
            200: describes(
                "Changed. The body is the bundle as it now stands and `ETag` "
                "is its new version -- so a pipeline chains writes without "
                "reading again."
            )
        },
        request=ScenarioBundleSerializer,
        parameters=[EXPAND_LABELS],
        responses={
            409: describes(
                "Either the bundle moved between the read this write was "
                "prepared from and the write itself, or -- on a rename -- "
                "another bundle took the acronym. The guard carries both "
                "conditions, so this refusal names neither; the advice is the "
                "same for both. Nothing was written."
            )
        },
    )
    def patch(self, request, uid):
        """Change the fields this payload names, and no others.

        A key the payload does not mention is **genuinely untouched** -- not
        read and written back -- which is also what stops an unrelated patch
        from re-minting every framework and model in the bundle. An empty list
        is how a multi-valued key is cleared, which is why omission cannot
        mean the same thing.

        Sub-resources are not accepted here, though a read nests them: a
        `PATCH` is partial by nature and nobody sends a whole read to one, so
        accepting `scenarios` would give a single call the power to drop a
        bundle's parts by omitting them. They have their own endpoints.

        A rename answers for the acronym's uniqueness the same way a create
        does, and for the same reason. A shared node -- a contact, an
        organisation, a funder, a region -- may be referenced by `iri` but
        never renamed: other bundles cite it, and one payload may not rewrite
        their labels.

        **This write is judged by what it introduces.** Most bundles in the
        graph were written by the browser and do not conform to the shape; a
        violation this payload did not add is not this caller's to answer for,
        and `pre_existing_violations` reports how many were found. Refusing
        them would make the missing fields -- which are what a human would add
        by patching -- unfixable through this API.
        """
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

        try:
            write = open_bundle(request, uid)
            write.require_write(request)

            # A rename is a write that can change an acronym, so it answers for
            # uniqueness like a create does -- asked here for a message that
            # names the acronym, and bound into the write below for the answer
            # that cannot be overtaken. A bundle never counts against itself,
            # so sending back what was read is not refused by its own value.
            renaming = "acronym" in payload
            if renaming and acronym_taken(write.store, payload["acronym"], uid):
                return acronym_conflict(payload["acronym"])

            known_labels = write.labels_of(referenced_node_iris(payload, BUNDLE_FIELDS))
            refuse_renames(payload, known_labels, BUNDLE_FIELDS)

            removed, added = bundle_delta(uid, payload, write.pre_state, known_labels)
            write.apply(
                removed=removed,
                added=added,
                verb=UPDATE,
                # Unlike a create, this guard also carries the version, so a
                # miss has two possible causes and the refusal names neither.
                # That is the right advice for both: read it again and retry.
                guard=acronym_is_free(payload["acronym"], uid) if renaming else "",
            )
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        return _bundle_response(
            uid,
            write.post_state,
            write.version,
            history_recorded=write.history_recorded,
        )

    @describes_a_guarded_write(
        {
            200: describes(
                "Deleted. The body names what was **deleted** and what was "
                "only **unlinked**, which no status code can say: a node "
                "another bundle still cites is kept and detached rather than "
                "destroyed. No `ETag`, because there is no bundle left to have "
                "a version. The bundle's history survives and stays readable "
                "at its own URL -- one line saying who removed it, when, and "
                "under which acronym."
            )
        },
        # No entity tag on the response, for the reason the body gives.
        entity_tag=False,
        parameters=[
            OpenApiParameter(
                name=CONFIRM,
                required=True,
                description=(
                    "The bundle's acronym, retyped. It guards the accident the "
                    "version cannot: right verb, wrong identifier. Compared "
                    "**exactly** -- normalising it away would let `api-test` "
                    "confirm the deletion of `API-TEST`, which is the "
                    "confusion the check exists to catch."
                ),
            )
        ],
        responses={
            400: describes(
                "The confirmation was missing, or was not this bundle's "
                "acronym, so nothing was deleted. `400` rather than `412`: "
                "nothing here is a precondition on the bundle's state, and it "
                "is exactly as the caller last read it. A bundle with no "
                "acronym at all cannot be confirmed and so cannot be deleted "
                "through this API -- give it one with a `PATCH` first."
            ),
            404: describes(
                "No such scenario bundle. A **repeated** delete answers this, "
                "and a client may treat it as success. `204` instead would "
                "swallow the wrong-identifier delete: a bundle that is gone "
                "has no acronym left to check a confirmation against, so a "
                "blanket success would confirm anything."
            ),
            409: describes(
                "The bundle moved between the read this delete was prepared "
                "from and the delete itself, or something outside it started "
                "citing a node this delete was about to remove. Nothing was "
                "deleted. Read it again, check it is still the one you meant, "
                "and retry."
            ),
        },
    )
    def delete(self, request, uid):
        """Delete this bundle, in the second of two steps.

        The first step is the read a client needs anyway: it returns the
        version to guard on and the acronym to retype. This step requires both,
        and they defend different accidents -- the version catches a bundle
        that changed since it was read, the acronym catches the wrong bundle
        entirely, which is the realistic failure for a pipeline looping over
        identifiers and the one a version cannot see.

        **The order of the refusals is the contract**, not an implementation
        detail: existence, then ownership, then the version, then the
        confirmation. A repeated delete therefore answers `404`, and a client
        may treat that as success. Answering `204` to it instead would swallow
        the wrong-identifier delete -- a bundle that is gone has no acronym
        left to check a confirmation against, so a blanket success would
        confirm anything.

        `200` with a body rather than `204`, as for a part: the typed
        containment walk can decide that a node another bundle still cites is
        unlinked rather than deleted, and no status code can say that.
        """
        try:
            write = open_bundle(request, uid)
            write.require_write(request)
            acronym = write.confirm_deletion(request)
            version_before = write.version.number
            removal = write.destroy(acronym)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        return Response(
            {
                "deleted": list(removal.deleted),
                "unlinked": list(removal.unlinked),
                READ_ONLY_CONTAINER: {
                    "uid": uid,
                    "iri": str(bundle_iri(uid)),
                    "acronym": acronym,
                    "version_before": version_before,
                    **write.gaps,
                },
            }
        )


def _all_referenced_iris(payload: dict) -> list:
    """Existing node IRIs a create points at, its nested parts included."""
    iris = referenced_node_iris(payload, BUNDLE_FIELDS)
    for part in BUNDLE_PARTS:
        for nested in payload.get(part.payload_key) or []:
            iris += referenced_node_iris(nested, part.fields)
    return iris


def _represent(
    uid: str,
    graph: Graph,
    version: BundleVersion,
    expand: frozenset = frozenset(),
) -> dict:
    """A read returns exactly what a write accepts, plus read-only data.

    **Sub-resources are nested here and rejected on `PATCH`.** That looks
    inconsistent until you notice which write each is for: a read sent back to
    `POST` copies the whole bundle, scenarios and study reports included, and
    later the replace endpoint takes exactly this shape -- while a `PATCH` is
    partial by nature and nobody sends a whole read to one. Nesting on read is
    what lets a client send back what it read without stripping anything.
    """
    body = labelled(
        {
            **bundle_payload(graph, uid),
            READ_ONLY_CONTAINER: {
                "uid": uid,
                "iri": str(bundle_iri(uid)),
                "version": version.number,
            },
        },
        BUNDLE_FIELDS,
        expand,
    )
    for part in BUNDLE_PARTS:
        body[part.payload_key] = part_bodies(graph, uid, part, expand)
    return body


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
    graph: Graph,
    version: BundleVersion,
    history_recorded: bool = True,
    expand: frozenset = frozenset(),
) -> Response:
    """The body, plus the entity tag every read has to carry."""
    body = _note_history_gap(_represent(uid, graph, version, expand), history_recorded)
    response = Response(body)
    response["ETag"] = version.etag
    return response
