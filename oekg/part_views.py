"""Addressable parts of a bundle: their own URLs, inside their bundle's guard.

A scenario factsheet and a study report are sub-resources because the shape
says so -- each carries its own has-uuid, and that rule is checkable against
the shape rather than negotiated per class. What follows from being one is the
same for both, so it is written once here and configured by a `BundlePart`:

- **It is addressable.** `POST` to the collection adds one, `GET` reads one,
  `PATCH` changes one without touching its siblings, and `DELETE` removes one
  -- with what it removes bounded by `oekg.removal`, because a part's own
  children go with it and everything shared with other bundles does not.
- **It is still part of its bundle for everything else.** The version guarded
  is the bundle's, the ownership asked is the bundle's, the entity tag returned
  is the bundle's, and the post-state validated is the whole bundle with this
  part in it. A part has no independent existence to version or own.

The last of those is not a convenience: every constraint in the shape is
bundle-local, so a part alone is not a unit the shape can judge. Validating one
on its own would pass vacuously in the places that matter.

Writes are identified by the containing bundle's version, so two clients
editing two different parts of one bundle do conflict. That is the price of one
version per bundle, chosen deliberately: conflict granularity follows the
aggregate root, and a part is not one.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse
from rdflib import Graph
from rest_framework import status
from rest_framework.response import Response

from oekg.api_support import OekgAPIView, shape_unavailable, store_unavailable
from oekg.bundles import (
    BundlePart,
    build_part_graph,
    bundle_iri,
    find_part,
    part_nodes,
    part_payload,
    part_uid,
)
from oekg.fields import mint_identifier, referenced_node_iris, resource_delta
from oekg.graph_store import GraphStoreError
from oekg.history import CREATE, UPDATE
from oekg.labels import labelled
from oekg.schema import (
    EXPAND_LABELS,
    describes,
    describes_a_guarded_write,
    describes_a_public_read,
    describes_a_removal,
    paging,
)
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.shape import ShapeUnavailable
from oekg.subresource_views import SubResourcePagination, SubResourceViewMixin
from oekg.writes import BundleWrite, open_bundle, refuse_renames


class BundlePartViewMixin(SubResourceViewMixin):
    """What both endpoints of a part need: which part it is."""

    part: BundlePart = None
    serializer_class = None

    def part_response(
        self, write: BundleWrite, pid: str, code: int = status.HTTP_200_OK
    ) -> Response:
        state = self.state_of(write)
        node = find_part(state, write.uid, self.part, pid)
        return self.represented(
            part_body(state, node, write.uid, self.part, self.resolving()),
            write,
            code,
        )

    def not_found(self, pid: str) -> Response:
        return Response(
            {"detail": f"No {self.part.name} {pid} in this bundle."},
            status=status.HTTP_404_NOT_FOUND,
        )


class BundlePartCollectionAPIView(BundlePartViewMixin, OekgAPIView):
    """`GET` lists a bundle's parts of one kind. `POST` adds one."""

    @describes_a_public_read(
        describes(
            "A page of this bundle's parts of one kind, each in the form a "
            "write accepts it nested. `ETag` carries the **bundle's** version: "
            "a part has none of its own."
        ),
        parameters=[
            EXPAND_LABELS,
            *paging(
                SubResourcePagination.page_size, SubResourcePagination.max_page_size
            ),
        ],
    )
    def get(self, request, uid):
        """List this bundle's parts of one kind.

        Paginated, although the collection is bounded by its bundle: this is a
        public endpoint and no public collection here has an unbounded mode.
        The nested form inside a bundle read is the exception, and a deliberate
        one -- that one has to be complete, because a client sends it back.
        """
        try:
            write = open_bundle(request, uid)
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        return self.paginated(
            request,
            part_bodies(write.pre_state, write.uid, self.part, self.resolving()),
            write,
        )

    @describes_a_guarded_write(
        {
            201: describes(
                "Created. The body is the part as it now stands, `Location` "
                "names its URL and `ETag` the **bundle's** new version."
            )
        },
        parameters=[EXPAND_LABELS],
    )
    def post(self, request, uid):
        """Add one part to this bundle.

        The identifier is minted by the server, as everywhere in this API, and
        returned in `Location`. What is validated is the **whole bundle with
        this part in it**: every constraint in the OEKG shape is bundle-local,
        so a part on its own is not a unit the shape can judge, and validating
        one alone would pass vacuously in the places that matter.

        The version guarded, the ownership asked and the entity tag returned
        are all the bundle's. Two clients editing two different parts of one
        bundle therefore do conflict -- the price of one version per bundle,
        and deliberate: conflict granularity follows the aggregate root, and a
        part is not one.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        pid = mint_identifier()
        try:
            write = open_bundle(request, uid)
            write.require_write(request)
            known_labels = write.labels_of(
                referenced_node_iris(serializer.validated_data, self.part.fields)
            )
            refuse_renames(serializer.validated_data, known_labels, self.part.fields)
            write.apply(
                removed=Graph(),
                added=build_part_graph(
                    self.part,
                    bundle_iri(uid),
                    pid,
                    serializer.validated_data,
                    known_labels,
                ),
                verb=CREATE,
                resource_type=self.part.node_class,
                resource_uuid=pid,
            )
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        response = self.part_response(write, pid, status.HTTP_201_CREATED)
        response["Location"] = reverse(
            self.part.detail_route, kwargs={"uid": uid, "pid": pid}
        )
        return response


class BundlePartAPIView(BundlePartViewMixin, OekgAPIView):
    """`GET` reads one. `PATCH` changes the keys it names. `DELETE` removes it."""

    @describes_a_public_read(
        describes(
            "The part: what a write accepts, plus `_meta`. `ETag` carries the "
            "**bundle's** version, which is what a write to this part has to "
            "send back."
        ),
        parameters=[EXPAND_LABELS],
    )
    def get(self, request, uid, pid):
        """Read one part of a bundle, publicly."""
        try:
            write = open_bundle(request, uid)
        except GraphStoreError as error:
            return store_unavailable(error, "read")
        if find_part(write.pre_state, uid, self.part, pid) is None:
            return self.not_found(pid)
        return self.part_response(write, pid)

    @describes_a_guarded_write(
        {
            200: describes(
                "Changed. The body is the part as it now stands and `ETag` is "
                "the bundle's new version."
            )
        },
        parameters=[EXPAND_LABELS],
    )
    def patch(self, request, uid, pid):
        """Change the fields this payload names, without touching its siblings.

        A key the payload does not mention is genuinely untouched. The part's
        existence is checked **before** the precondition, so a request for a
        part that is not there hears that rather than being told its `If-Match`
        is missing for something that does not exist.

        Like every write here it is judged by what it **introduces**: a
        violation the bundle already carried is reported in
        `pre_existing_violations` and does not refuse the write.
        """
        serializer = self.serializer_class(data=request.data, partial=True)
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
            # Existence of the part before the precondition for the whole: a
            # request for a part that is not there should hear that, rather
            # than be told its If-Match is missing for something that does not
            # exist.
            node = find_part(write.pre_state, uid, self.part, pid)
            if node is None:
                return self.not_found(pid)
            write.require_write(request)

            known_labels = write.labels_of(
                referenced_node_iris(payload, self.part.fields)
            )
            refuse_renames(payload, known_labels, self.part.fields)
            removed, added = resource_delta(
                node, self.part.fields, payload, write.pre_state, known_labels
            )
            write.apply(
                removed=removed,
                added=added,
                verb=UPDATE,
                resource_type=self.part.node_class,
                resource_uuid=pid,
            )
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")

        return self.part_response(write, pid)

    @describes_a_removal
    def delete(self, request, uid, pid):
        """Remove this part, and with it what only it holds.

        The same order as a patch -- bundle, part, caller, precondition -- and
        the same write path, because a delete is a write like any other: it is
        validated against the shape, guarded on the bundle's version and
        recorded in the history. What differs is the arithmetic in front of it,
        which is `oekg.removal`'s.

        No retyped confirmation token, unlike the whole-bundle delete. Ceremony
        is proportional to blast radius: this removes one bounded part that can
        be created again, and the history says what it held.
        """
        try:
            write = open_bundle(request, uid)
            node = find_part(write.pre_state, uid, self.part, pid)
            if node is None:
                return self.not_found(pid)
            write.require_write(request)
            return self.removed(
                write,
                node,
                resource_type=self.part.node_class,
                resource_uuid=pid,
            )
        except ShapeUnavailable as error:
            return shape_unavailable(error)
        except GraphStoreError as error:
            return store_unavailable(error, "written to")


def part_bodies(graph: Graph, uid: str, part: BundlePart, labels: bool = False) -> list:
    """Every part of this kind, in the form a write accepts them nested."""
    bodies = [
        part_body(graph, node, uid, part, labels)
        for node in part_nodes(graph, uid, part)
    ]
    bodies.sort(key=lambda body: body[part.sort_field] or "")
    return bodies


def part_body(
    graph: Graph, node, uid: str, part: BundlePart, expand: frozenset = frozenset()
) -> dict:
    return labelled(
        {
            **part_payload(graph, node, part),
            READ_ONLY_CONTAINER: {
                "uid": part_uid(graph, node),
                "iri": str(node),
                "type": str(part.node_class),
                "bundle": uid,
            },
        },
        part.fields,
        expand,
    )
