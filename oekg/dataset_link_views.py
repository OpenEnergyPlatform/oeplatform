"""Dataset links, as endpoints: `POST`, `GET` and `DELETE`, and no `PATCH`.

**Which "dataset" this is:** the OEKG input/output dataset -- a node on a
scenario factsheet recording that the scenario consumed or produced data. What
it points at is an OEP Table or an OEP Dataset. See `oekg.dataset_links` for the
full vocabulary note; the nested URL is what keeps the three apart in practice.

The endpoints sit one level deeper than the other sub-resources, under the
scenario they belong to, because that is where the shape hangs them. Everything
else is the bundle's: the version guarded, the ownership asked, the entity tag
returned, and the post-state validated.

**No `PATCH`, and that is the design rather than an omission.** Every triple a
link holds is derived from its type, its target kind and its name, so there is
no field to change without changing what the link is. Editing one is adding a
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
    EXPAND_LABELS,
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
from oekg.bundles import SCENARIO, find_part
from oekg.dataset_links import (
    DIRECTION_BY_NAME,
    UnaddressableTarget,
    build_dataset_link_graph,
    dataset_link_nodes,
    dataset_link_payload,
    dataset_link_uid,
    find_dataset_link,
    reference_target,
    stored_iri,
    target_iri,
)
from oekg.fields import mint_identifier
from oekg.graph_store import GraphStoreError
from oekg.history import CREATE
from oekg.labels import labelled
from oekg.read_serializers import DatasetLinkReadSerializer
from oekg.resolution import resolve
from oekg.serializers import READ_ONLY_CONTAINER, DatasetLinkSerializer
from oekg.shape import ShapeUnavailable
from oekg.subresource_views import SubResourcePagination, SubResourceViewMixin
from oekg.writes import BundleWrite, open_bundle

# A dataset link has no field table, because it has no fields: everything it
# holds follows from its type, its target and its name. That is the same fact
# that gives it no `PATCH`, and it is why resolving its picked ontology terms
# is an empty answer rather than a refusal.
NO_PICKED_TERMS = ()

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
        body = _link_body(state, node, direction, write.uid, sid, self.resolving())
        _resolve_into(state, [(node, body)])
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
            _link_bodies(write.pre_state, scenario, write.uid, sid, self.resolving()),
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
        parameters=[EXPAND_LABELS],
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
        """Link this scenario to a table or dataset on this platform.

        Three keys and no more: `type` (`input` or `output`), `ref` (`table`
        or `dataset`) and the target's `name`. Everything the shape stores
        follows from them, which is the same fact that gives a link no `PATCH`.

        **The target is not checked.** A link may outlive what it points at --
        a bundle is a published research record, so *this scenario used table
        X* stays true after X is gone -- and blocking here would let one user
        make a stranger's table undeletable. Whether the citation still
        resolves is reported on every read instead.

        `ref: table` is reproducible and `ref: dataset` is current: a dataset
        reference resolves to the catalogue entry's members as they are today,
        not as they were when the link was written. Choosing between them is
        the client's call.
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
                    scenario, did, payload, target_iri(request, payload)
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
        parameters=[EXPAND_LABELS],
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

    @describes_a_removal
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


def _link_bodies(
    graph: Graph, scenario, uid: str, sid: str, expand: frozenset = frozenset()
) -> list:
    pairs = [
        (node, _link_body(graph, node, direction, uid, sid, expand))
        for direction, node in dataset_link_nodes(graph, scenario)
    ]
    pairs.sort(key=lambda pair: (pair[1]["type"], pair[1]["name"]))
    _resolve_into(graph, pairs)
    return [body for _, body in pairs]


def _resolve_into(graph: Graph, pairs: list) -> None:
    """Say, for every one of these links, what it points at right now.

    Done to the whole list at once and never to one link at a time: resolution
    costs a fixed few relational queries for any number of links, and a
    per-link version of this would put a query per citation on a public
    endpoint. A single link is simply a list of one.

    What is looked up comes from each link's stored **URL**, not from the
    `name` in its body. The two agree for every link this API wrote, because
    the URL was built from the name -- but the existing route takes them as two
    separate values from a client, so a legacy link can carry a real table's
    URL beside a human-readable title. Resolving by that title would report a
    table that is plainly there as deleted.
    """
    resolutions = resolve(
        [reference_target(stored_iri(graph, node) or "") for node, _ in pairs]
    )
    for (_, body), resolution in zip(pairs, resolutions):
        body[READ_ONLY_CONTAINER].update(resolution.as_meta())


def _link_body(
    graph: Graph, node, direction, uid: str, sid: str, expand: frozenset = frozenset()
) -> dict:
    """One link: the three keys a write accepts, and the rest read-only.

    ``target_iri`` is in `_meta` rather than in the payload because a client
    does not send it -- it is derived. It is there because it is the only thing
    that stays true when `ref` comes back null: a link written before this API
    existed can point at an address this platform has no route for, and then
    the writable payload genuinely cannot express it. Saying where it points is
    better than leaving a reader with a name and no target.
    """
    return labelled(
        {
            **dataset_link_payload(graph, node, direction),
            READ_ONLY_CONTAINER: {
                "uid": dataset_link_uid(graph, node),
                "iri": str(node),
                "type": str(direction.node_class),
                "target_iri": stored_iri(graph, node),
                "bundle": uid,
                "scenario": sid,
            },
        },
        NO_PICKED_TERMS,
        expand,
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

    Compared on the three answers a link *is*, not on the URL they produce: the
    stored URL carries the host the request arrived on, so two links written
    through different names for this platform would otherwise both be kept.
    """
    wanted = {key: payload[key] for key in ("type", "ref", "name")}
    return any(
        dataset_link_payload(graph, node, direction) == wanted
        for direction, node in dataset_link_nodes(graph, scenario)
    )


def _duplicate(payload: dict) -> Response:
    return Response(
        {
            "detail": (
                f"This scenario already links the {payload['ref']} "
                f"{payload['name']!r} as {payload['type']}. A dataset link is "
                "added or removed, never duplicated."
            )
        },
        status=status.HTTP_409_CONFLICT,
    )
