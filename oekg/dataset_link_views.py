"""Dataset links, as endpoints: `POST`, `GET` and `DELETE`, and no `PATCH`.

**Which "dataset" this is:** the OEKG input/output dataset -- a node on a
scenario factsheet recording that the scenario consumed or produced data. What
it points at is an OEP Table, an OEP Dataset, or an address somewhere else
entirely. See `oekg.dataset_links` for the full vocabulary note; the nested URL
is what keeps the three senses of the word apart in practice.

The endpoints sit one level deeper than the other sub-resources, under the
scenario they belong to, because that is where the shape hangs them. Everything
else is the bundle's: the version guarded, the ownership asked, the entity tag
returned, and the post-state validated.

**No `PATCH`, and that is the design rather than an omission.** Every triple a
link holds follows from its type, its target kind, its name and where it
points, so there is no field to change without changing what the link is. Editing one is adding a
different one and removing this one, which says plainly what happened -- and
`DELETE` is what makes that reachable, so the pair is the whole contract.

**Every read resolves.** A link is a citation with nothing enforcing it, so a
read says what the citation means now: whether the named target is still there
and, for a catalogue reference, which tables it groups today. That is computed
per read and never stored -- see `oekg.resolution` for why, and for what the
nulls mean.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse
from drf_spectacular.utils import OpenApiResponse
from rdflib import Graph
from rest_framework import status
from rest_framework.response import Response

from oekg.api_description import (
    BUNDLE_UID,
    EXPAND_LABELS,
    LINK_DID,
    SCENARIO_SID,
    CollectionSchema,
    a_page_of,
    describes_a_guarded_write,
    describes_a_public_read,
    describes_a_removal,
    json_body,
    paging,
)
from oekg.api_support import (
    OekgAPIView,
    Refused,
    shape_unavailable,
    store_unavailable,
)
from oekg.bundle_bodies import link_bodies, link_body, resolve_into
from oekg.bundles import SCENARIO, find_part
from oekg.dataset_links import (
    DIRECTION_BY_NAME,
    EXTERNAL,
    UnaddressableTarget,
    build_dataset_link_graph,
    dataset_link_nodes,
    dataset_link_payload,
    find_dataset_link,
    link_address,
    link_identity,
)
from oekg.fields import mint_identifier
from oekg.graph_store import GraphStoreError
from oekg.history import CREATE
from oekg.read_serializers import DatasetLinkReadSerializer
from oekg.serializers import DatasetLinkSerializer
from oekg.shape import ShapeUnavailable
from oekg.subresource_views import SubResourcePagination, SubResourceViewMixin
from oekg.writes import BundleWrite, open_bundle

# Said once and spent by all three link responses, because all three resolve.
RESOLUTION = (
    "Every link reports what it points at **now**: `_meta.resolvable` says "
    "whether the named target is still on this platform, and `_meta.tables` "
    "names the one table for `ref: table` or the catalogue entry's current "
    "members for `ref: dataset`. That is computed per read and never stored. "
    "Both read `null` -- never `false` -- when the stored address is not a "
    "page on this platform, because `false` would claim the target had been "
    "deleted. **Resolution is not an expansion**: a reader needs it to tell a "
    "live citation from a dead one, so it is never opt-in."
)


class DatasetLinkViewMixin(SubResourceViewMixin):
    """What both endpoints need: the scenario these links hang off."""

    def scenario_of(self, write: BundleWrite, sid: str):
        """The scenario named by the URL, or a `404`. Raises ``Refused``.

        Raised rather than returned, as everywhere else in this API: a helper
        that handed back either a value or a refusal would make every call site
        test which it got, and one forgotten test is a refusal ignored.
        """
        node = find_part(write.pre_state, write.uid, SCENARIO, sid)
        if node is None:
            raise Refused(
                Response(
                    {"detail": f"No scenario {sid} in this bundle."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            )
        return node

    def link_response(
        self,
        write: BundleWrite,
        sid: str,
        did: str,
        code: int = status.HTTP_200_OK,
    ) -> Response:
        state = self.state_of(write)
        scenario = find_part(state, write.uid, SCENARIO, sid)
        direction, node = find_dataset_link(state, scenario, did)
        body = link_body(state, node, direction, write.uid, sid, self.resolving())
        resolve_into(state, [(node, body)])
        return self.represented(body, write, code)


class DatasetLinkCollectionAPIView(DatasetLinkViewMixin, OekgAPIView):
    """`GET` lists a scenario's dataset links. `POST` adds one."""

    schema = CollectionSchema()

    @describes_a_public_read(
        a_page_of(
            DatasetLinkReadSerializer,
            "A page of this scenario's dataset links. " + RESOLUTION,
        ),
        parameters=[
            BUNDLE_UID,
            SCENARIO_SID,
            EXPAND_LABELS,
            *paging(SubResourcePagination),
        ],
    )
    def get(self, request, uid, sid):
        """List this scenario's links to data on this platform."""
        try:
            write = open_bundle(request, uid)
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        scenario = self.scenario_of(write, sid)
        return self.paginated(
            request,
            link_bodies(write.pre_state, scenario, write.uid, sid, self.resolving()),
            write,
        )

    @describes_a_guarded_write(
        {
            201: OpenApiResponse(
                response=DatasetLinkReadSerializer,
                description=(
                    "Created. `Location` names the link's URL and `ETag` the "
                    "bundle's new version. " + RESOLUTION
                ),
            )
        },
        request=DatasetLinkSerializer,
        parameters=[BUNDLE_UID, SCENARIO_SID, EXPAND_LABELS],
        responses={
            400: json_body(
                "The payload named a key this link does not have, or a `type` "
                "or `ref` outside the two values each allows -- or the target "
                "named cannot be addressed on this platform. Nothing was "
                "written."
            ),
            409: json_body(
                "This scenario already links that target in that direction, "
                "or the bundle moved while this write was being prepared. A "
                "duplicate is refused rather than silently skipped: two nodes "
                "saying one thing would leave a later `DELETE` ambiguous, and "
                "a caller unable to tell *added* from *already there*."
            ),
        },
    )
    def post(self, request, uid, sid):
        """Record that this scenario consumed or produced some data.

        Four keys and no more: `type` (`input` or `output`), `ref` (`table`,
        `dataset` or `external`), the target's `name`, and `url` where the
        client says where it points rather than letting the router derive it.
        Everything the shape stores follows from them, which is the same fact
        that gives a link no `PATCH`.

        **`ref: external` is an address this platform has no route for** -- a
        databus entry, say. It is not a lesser citation: the address is stored
        exactly as sent, and a read reports that this server cannot say whether
        it still resolves rather than claiming it was deleted. A link naming a
        platform target may send its `url` too, and then `ref` has to be the
        kind that address actually is.

        **The target is not checked.** A link may outlive what it points at --
        a bundle is a published research record, so *this scenario used table
        X* stays true after X is gone -- and blocking here would let one user
        make a stranger's table undeletable. Whether the citation still
        resolves is reported on every read instead.

        `ref: table` is reproducible and `ref: dataset` is current: a dataset
        reference resolves to the catalogue entry's members as they are today,
        not as they were when the link was written. Choosing between them is
        the client's call.

        A duplicate is refused rather than skipped, and what counts as a
        duplicate is not the same question for every kind: a platform target
        compares by what the client said, because the stored URL carries
        whichever host name the request arrived on, while an external link
        compares by its address, which is the only thing identifying it.
        """
        serializer = DatasetLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        did = mint_identifier()
        try:
            # The bundle, then the scenario, then the caller's right to write,
            # and only then the payload's own problems: one order for the whole
            # API, so a name that cannot be part of a URL never answers 400 for
            # a bundle that is not there.
            write = open_bundle(request, uid)
            scenario = self.scenario_of(write, sid)
            write.require_write(request)
            if _already_linked(write.pre_state, scenario, payload):
                return _duplicate(payload)
            write.apply(
                removed=Graph(),
                added=build_dataset_link_graph(
                    scenario, did, payload, link_address(request, payload)
                ),
                verb=CREATE,
                resource_type=_direction_of(payload).node_class,
                resource_uuid=did,
            )
        except UnaddressableTarget as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        response = self.link_response(write, sid, did, status.HTTP_201_CREATED)
        response["Location"] = reverse(
            "api:scenario-bundle-dataset-link",
            kwargs={"uid": uid, "sid": sid, "did": did},
        )
        return response


class DatasetLinkAPIView(DatasetLinkViewMixin, OekgAPIView):
    """`GET` reads one dataset link, `DELETE` removes it. No `PATCH`.

    Add and remove is the whole contract, so the remove is the other half of
    the design rather than an extra: with no way to edit a link, a client that
    got one wrong has nothing else to reach for.
    """

    @describes_a_public_read(
        OpenApiResponse(
            response=DatasetLinkReadSerializer,
            description="One dataset link. " + RESOLUTION,
        ),
        parameters=[BUNDLE_UID, SCENARIO_SID, LINK_DID, EXPAND_LABELS],
    )
    def get(self, request, uid, sid, did):
        """Read one dataset link, publicly.

        `_meta.target_iri` is the address actually stored. It is there because
        it is the only thing that stays true when `ref` comes back `null`: a
        link written before this API existed can point at an address this
        platform has no route for, and the writable payload then genuinely
        cannot express it.
        """
        try:
            write = open_bundle(request, uid)
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        scenario = self.scenario_of(write, sid)
        _, node = find_dataset_link(write.pre_state, scenario, did)
        if node is None:
            return _no_such_link(did)
        return self.link_response(write, sid, did)

    @describes_a_removal(BUNDLE_UID, SCENARIO_SID, LINK_DID)
    def delete(self, request, uid, sid, did):
        """Remove one link. Its target is not touched and never was.

        A link is the only removable thing in this API with no children and
        nothing shared beneath it -- what it points at is an OEP table or
        dataset, which lives in Postgres and which no graph write may reach. It
        still goes through the typed walk, because the guard clause is what
        decides whether *this* node is only claimed by this scenario, and that
        is not a question the class alone answers.
        """
        try:
            write = open_bundle(request, uid)
            scenario = self.scenario_of(write, sid)
            direction, node = find_dataset_link(write.pre_state, scenario, did)
            if node is None:
                return _no_such_link(did)
            write.require_write(request)
            return self.removed(
                write,
                node,
                resource_type=direction.node_class,
                resource_uuid=did,
                scenario=sid,
            )
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")


def _no_such_link(did: str) -> Response:
    return Response(
        {"detail": f"No dataset link {did} on this scenario."},
        status=status.HTTP_404_NOT_FOUND,
    )


def _direction_of(payload: dict):
    return DIRECTION_BY_NAME[payload["type"]]


def _already_linked(graph: Graph, scenario, payload: dict) -> bool:
    """Whether this scenario already links that target in that direction.

    A second identical link would be two nodes saying one thing, and the
    remove-only contract gives no way to tell which of them a later `DELETE`
    took. Refused rather than silently skipped, so a client learns what
    happened -- the existing route's answer of `200` with a "skipped" list
    leaves a pipeline unable to distinguish "added" from "already there".

    What counts as the same link is `link_identity`, and it is not the same
    question for every kind: a platform target compares by what the client
    said, because the URL it produces carries whichever host name the request
    arrived on, while an external link compares by its address, because that
    address *is* the target and nothing else identifies it.
    """
    wanted = link_identity(payload)
    return any(
        link_identity(dataset_link_payload(graph, node, direction)) == wanted
        for direction, node in dataset_link_nodes(graph, scenario)
    )


def _duplicate(payload: dict) -> Response:
    # Named by what identifies it, which is the same thing the duplicate check
    # compared: a client told that its external link duplicates a *name* would
    # go looking for the wrong collision.
    cited = payload["url"] if payload["ref"] == EXTERNAL else payload["name"]
    kind = payload["ref"] or "unaddressed"
    return Response(
        {
            "detail": (
                f"This scenario already links the {kind} {cited!r} as "
                f"{payload['type']}. A dataset link is added or removed, "
                "never duplicated."
            )
        },
        status=status.HTTP_409_CONFLICT,
    )
