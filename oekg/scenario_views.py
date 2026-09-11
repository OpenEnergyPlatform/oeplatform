"""Scenario factsheets: their own URLs, inside their bundle's guard.

A scenario is a sub-resource because the shape says so -- it carries its own
has-uuid, and that rule is checkable against the shape rather than negotiated
per class. What follows from being one:

- **It is addressable.** `POST` to the collection adds one, `GET` reads one,
  `PATCH` changes one without touching its siblings.
- **It is still part of its bundle for everything else.** The version guarded
  is the bundle's, the ownership asked is the bundle's, the entity tag returned
  is the bundle's, and the post-state validated is the whole bundle with this
  scenario in it. A scenario has no independent existence to version or own.

The last of those is not a convenience: every constraint in the shape is
bundle-local, so a scenario alone is not a unit the shape can judge. Validating
one on its own would pass vacuously in the places that matter.

Writes are identified by the containing bundle's version, so two clients
editing two different scenarios of one bundle do conflict. That is the price of
one version per bundle, chosen deliberately: conflict granularity follows the
aggregate root, and a scenario is not one.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse
from rdflib import Graph
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from oekg.api_support import (
    ScenarioBundleThrottle,
    ScenarioBundleUserThrottle,
    shape_unavailable,
    store_unavailable,
)
from oekg.bundles import (
    SCENARIO_CLASS,
    SCENARIO_FIELDS,
    build_scenario_graph,
    bundle_iri,
    find_scenario,
    mint_scenario_uid,
    referenced_node_iris,
    resource_delta,
    scenario_nodes,
    scenario_payload,
    scenario_uid,
)
from oekg.graph_store import GraphStoreError
from oekg.history import CREATE, UPDATE
from oekg.serializers import READ_ONLY_CONTAINER, ScenarioSerializer
from oekg.shape import ShapeUnavailable
from oekg.writes import BundleWrite, Refused, open_write


class ScenarioCollectionAPIView(APIView):
    """`GET` lists a bundle's scenarios. `POST` adds one."""

    throttle_classes = [ScenarioBundleThrottle, ScenarioBundleUserThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, uid):
        try:
            write = open_write(request, uid, read_only=True)
        except Refused as refusal:
            return refusal.response
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        return _listing(write)

    def post(self, request, uid):
        serializer = ScenarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sid = mint_scenario_uid()
        try:
            write = open_write(request, uid)
            known_labels = write.labels_of(
                referenced_node_iris(serializer.validated_data, SCENARIO_FIELDS)
            )
            write.apply(
                removed=Graph(),
                added=build_scenario_graph(
                    bundle_iri(uid), sid, serializer.validated_data, known_labels
                ),
                verb=CREATE,
                resource_type=SCENARIO_CLASS,
                resource_uuid=sid,
            )
        except Refused as refusal:
            return refusal.response
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        response = _represented(write, sid, status.HTTP_201_CREATED)
        response["Location"] = _location(uid, sid)
        return response


class ScenarioAPIView(APIView):
    """`GET` reads one scenario. `PATCH` changes the keys it names."""

    throttle_classes = [ScenarioBundleThrottle, ScenarioBundleUserThrottle]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, uid, sid):
        try:
            write = open_write(request, uid, read_only=True)
        except Refused as refusal:
            return refusal.response
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        if find_scenario(write.pre_state, uid, sid) is None:
            return _no_such_scenario(sid)
        return _represented(write, sid)

    def patch(self, request, uid, sid):
        serializer = ScenarioSerializer(data=request.data, partial=True)
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
            write = open_write(request, uid)
            node = find_scenario(write.pre_state, uid, sid)
            if node is None:
                return _no_such_scenario(sid)

            known_labels = write.labels_of(
                referenced_node_iris(payload, SCENARIO_FIELDS)
            )
            removed, added = resource_delta(
                node, SCENARIO_FIELDS, payload, write.pre_state, known_labels
            )
            write.apply(
                removed=removed,
                added=added,
                verb=UPDATE,
                resource_type=SCENARIO_CLASS,
                resource_uuid=sid,
            )
        except Refused as refusal:
            return refusal.response
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        return _represented(write, sid)


def scenario_bodies(graph: Graph, uid: str) -> list:
    """Every scenario of this bundle, in the form a write accepts them nested."""
    bodies = [_scenario_body(graph, node, uid) for node in scenario_nodes(graph, uid)]
    bodies.sort(key=lambda body: body["acronym"] or "")
    return bodies


def _listing(write: BundleWrite) -> Response:
    scenarios = scenario_bodies(write.pre_state, write.uid)
    response = Response({"count": len(scenarios), "results": scenarios})
    response["ETag"] = write.version.etag
    return response


def _represented(
    write: BundleWrite, sid: str, code: int = status.HTTP_200_OK
) -> Response:
    """One scenario, carrying the **bundle's** entity tag.

    Its own, because a sub-resource write bumps the bundle's version and the
    next write has to send that back -- handing out anything else here would
    guarantee a `412` on the very next call.
    """
    state = write.post_state if write.post_state is not None else write.pre_state
    node = find_scenario(state, write.uid, sid)
    body = _scenario_body(state, node, write.uid)
    if not write.history_recorded:
        body[READ_ONLY_CONTAINER]["history_recorded"] = False
    response = Response(body, status=code)
    response["ETag"] = write.version.etag
    return response


def _scenario_body(graph: Graph, node, uid: str) -> dict:
    return {
        **scenario_payload(graph, node),
        READ_ONLY_CONTAINER: {
            "uid": scenario_uid(graph, node),
            "iri": str(node),
            "type": str(SCENARIO_CLASS),
            "bundle": uid,
        },
    }


def _location(uid: str, sid: str) -> str:
    return reverse("api:scenario-bundle-scenario", kwargs={"uid": uid, "sid": sid})


def _no_such_scenario(sid: str) -> Response:
    return Response(
        {"detail": f"No scenario {sid} in this bundle."},
        status=status.HTTP_404_NOT_FOUND,
    )
