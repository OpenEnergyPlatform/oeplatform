"""Dataset links, as endpoints: `POST` to add one, `GET` to read, and no `PATCH`.

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
different one and removing this one, which says plainly what happened.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse
from rdflib import Graph
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from oekg.api_support import OekgAPIView, shape_unavailable, store_unavailable
from oekg.bundles import SCENARIO, find_part
from oekg.dataset_links import (
    DIRECTION_BY_NAME,
    UnaddressableTarget,
    build_dataset_link_graph,
    dataset_link_nodes,
    dataset_link_payload,
    dataset_link_uid,
    find_dataset_link,
    mint_dataset_link_uid,
    target_path,
)
from oekg.fields import HAS_IRI
from oekg.graph_store import GraphStoreError
from oekg.history import CREATE
from oekg.part_views import SubResourcePagination
from oekg.serializers import READ_ONLY_CONTAINER, DatasetLinkSerializer
from oekg.shape import ShapeUnavailable
from oekg.writes import BundleWrite, open_bundle


class DatasetLinkViewMixin:
    """What both endpoints need: the scenario, and who may write through it."""

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def scenario_or_404(self, write: BundleWrite, sid: str):
        node = find_part(write.pre_state, write.uid, SCENARIO, sid)
        if node is None:
            return None, Response(
                {"detail": f"No scenario {sid} in this bundle."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return node, None

    def represented(
        self,
        write: BundleWrite,
        sid: str,
        did: str,
        code: int = status.HTTP_200_OK,
    ) -> Response:
        """One link, carrying the **bundle's** entity tag.

        The bundle's, because writing a link bumps the bundle's version and the
        next write has to send that back.
        """
        state = write.post_state if write.post_state is not None else write.pre_state
        scenario = find_part(state, write.uid, SCENARIO, sid)
        direction, node = find_dataset_link(state, scenario, did)
        body = _link_body(state, node, direction, write.uid, sid)
        if not write.history_recorded:
            body[READ_ONLY_CONTAINER]["history_recorded"] = False
        response = Response(body, status=code)
        response["ETag"] = write.version.etag
        return response


class DatasetLinkCollectionAPIView(DatasetLinkViewMixin, OekgAPIView):
    """`GET` lists a scenario's dataset links. `POST` adds one."""

    def get(self, request, uid, sid):
        try:
            write = open_bundle(request, uid)
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        scenario, refusal = self.scenario_or_404(write, sid)
        if refusal is not None:
            return refusal

        paginator = SubResourcePagination()
        page = paginator.paginate_queryset(
            _link_bodies(write.pre_state, scenario, write.uid, sid), request, view=None
        )
        response = paginator.get_paginated_response(page)
        response["ETag"] = write.version.etag
        return response

    def post(self, request, uid, sid):
        serializer = DatasetLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        did = mint_dataset_link_uid()
        try:
            iri = request.build_absolute_uri(
                target_path(payload["ref"], payload["name"])
            )
        except UnaddressableTarget as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            write = open_bundle(request, uid)
            scenario, refusal = self.scenario_or_404(write, sid)
            if refusal is not None:
                return refusal
            write.require_write(request)
            if _already_linked(write.pre_state, scenario, payload, iri):
                return _duplicate(payload)
            write.apply(
                removed=Graph(),
                added=build_dataset_link_graph(scenario, did, payload, iri),
                verb=CREATE,
                resource_type=_direction_of(payload).node_class,
                resource_uuid=did,
            )
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        response = self.represented(write, sid, did, status.HTTP_201_CREATED)
        response["Location"] = reverse(
            "api:scenario-bundle-dataset-link",
            kwargs={"uid": uid, "sid": sid, "did": did},
        )
        return response


class DatasetLinkAPIView(DatasetLinkViewMixin, OekgAPIView):
    """`GET` reads one dataset link. There is no `PATCH`: see the module note."""

    def get(self, request, uid, sid, did):
        try:
            write = open_bundle(request, uid)
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        scenario, refusal = self.scenario_or_404(write, sid)
        if refusal is not None:
            return refusal
        _, node = find_dataset_link(write.pre_state, scenario, did)
        if node is None:
            return Response(
                {"detail": f"No dataset link {did} on this scenario."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return self.represented(write, sid, did)


def _link_bodies(graph: Graph, scenario, uid: str, sid: str) -> list:
    bodies = [
        _link_body(graph, node, direction, uid, sid)
        for direction, node in dataset_link_nodes(graph, scenario)
    ]
    bodies.sort(key=lambda body: (body["type"], body["name"]))
    return bodies


def _link_body(graph: Graph, node, direction, uid: str, sid: str) -> dict:
    return {
        **dataset_link_payload(graph, node, direction),
        READ_ONLY_CONTAINER: {
            "uid": dataset_link_uid(graph, node),
            "iri": str(node),
            "type": str(direction.node_class),
            "bundle": uid,
            "scenario": sid,
        },
    }


def _direction_of(payload: dict):
    return DIRECTION_BY_NAME[payload["type"]]


def _already_linked(graph: Graph, scenario, payload: dict, iri: str) -> bool:
    """Whether this scenario already links that target in that direction.

    A second identical link would be two nodes saying one thing, and the
    remove-only contract gives no way to tell which of them a later `DELETE`
    took. Refused rather than silently skipped, so a client learns what
    happened -- the existing route's answer of `200` with a "skipped" list
    leaves a pipeline unable to distinguish "added" from "already there".
    """
    direction = _direction_of(payload)
    return any(
        found is direction and _iri_of(graph, node) == iri
        for found, node in dataset_link_nodes(graph, scenario)
    )


def _iri_of(graph: Graph, node):
    value = graph.value(node, HAS_IRI)
    return None if value is None else str(value)


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
