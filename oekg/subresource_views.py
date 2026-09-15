"""What every endpoint below a bundle shares.

A scenario factsheet, a study report and a dataset link are three different
resources, but everything about *being addressed below a bundle* is the same
for all of them, and getting any of it wrong is a bug that would not look like
one:

- **Reads are public, writes are not**, named by the safe methods rather than
  by listing the unsafe ones -- so a verb a later slice adds is authenticated
  by default instead of public until somebody remembers.
- **The entity tag returned is the bundle's**, always. A sub-resource has no
  version of its own, and a write to one bumps the bundle's, so handing out
  anything else here would guarantee a `412` on the very next call.
- **A write's response describes the post-state**, a read's the pre-state, and
  a lost history entry is named beside the success it qualifies rather than
  instead of it.
- **No collection has an unbounded mode.** These are public endpoints.
- **A delete answers with a body, not a `204`.** The typed containment walk can
  decide that a node something else still cites is unlinked rather than
  deleted, and no status code can say that.

`part_views` builds the two addressable *parts* of a bundle on top of this;
`dataset_link_views` builds the links that hang off a scenario, which are not
parts and have no `PATCH`, but are addressed below a bundle just the same.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rdflib import Graph, URIRef
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from oekg.history import DELETE
from oekg.removal import plan_removal
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.writes import BundleWrite

# Written once and applied to every delete, so the description a client reads
# cannot drift from the one `removed` actually implements.
describes_a_removal = extend_schema(
    responses={
        200: OpenApiResponse(
            description=(
                "Removed. The body names what was deleted and what was only "
                "unlinked, which no status code can say."
            )
        )
    }
)


class SubResourcePagination(PageNumberPagination):
    """A ceiling, not a default: no public collection has an unbounded mode."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class SubResourceViewMixin:
    """Permissions, the entity tag, and which state a response describes."""

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def state_of(self, write: BundleWrite) -> Graph:
        """The graph a response should be built from.

        The post-state after a write and the pre-state otherwise, so a `POST`
        answers with what it just created and a `GET` with what is there.
        """
        return write.post_state if write.post_state is not None else write.pre_state

    def represented(
        self, body: dict, write: BundleWrite, code: int = status.HTTP_200_OK
    ) -> Response:
        """One sub-resource, carrying the bundle's entity tag."""
        body[READ_ONLY_CONTAINER].update(write.gaps)
        response = Response(body, status=code)
        response["ETag"] = write.version.etag
        return response

    def removed(
        self,
        write: BundleWrite,
        node: URIRef,
        *,
        resource_type: URIRef,
        resource_uuid: str,
        **meta,
    ) -> Response:
        """Remove ``node`` from its bundle, and answer with what that came to.

        The whole of a delete after the caller has been checked, because every
        endpoint below a bundle does it identically: plan the typed containment
        walk, apply it through the shared write path under the bundle's version
        *and* the plan's own guard, and report both halves of the outcome. A
        view is left with the part that differs -- which node the URL names.

        The answer is `200` with a body rather than `204`, and that is the
        reason it lives here rather than in the views. The guard clause can
        decide that a node something else still cites is unlinked rather than
        deleted, and no status code can say that; a body is the only place it
        fits, so no endpoint may quietly answer `204` instead.

        Only the **downgraded** nodes are listed as unlinked. Every delete also
        unlinks the shared nodes its subject pointed at -- regions, authors,
        contacts, ontology terms -- and listing those would bury the one line
        that is news under the rule that always applies.
        """
        removal = plan_removal(write.store, write.pre_state, node)
        write.apply(
            removed=removal.removed,
            added=Graph(),
            verb=DELETE,
            guard=removal.guard,
            resource_type=resource_type,
            resource_uuid=resource_uuid,
        )
        return self.represented(
            {
                "deleted": list(removal.deleted),
                "unlinked": list(removal.unlinked),
                READ_ONLY_CONTAINER: {
                    "bundle": write.uid,
                    "resource": {"type": str(resource_type), "uid": resource_uuid},
                    **meta,
                },
            },
            write,
        )

    def paginated(self, request, bodies: list, write: BundleWrite) -> Response:
        """A collection, paginated, carrying the bundle's entity tag.

        Paginated even though these collections are bounded by their bundle:
        this is a public endpoint, and "no unbounded mode" is the rule for all
        of them. The nested form inside a bundle read is the exception, and it
        is one on purpose -- that one has to be complete, because a client
        sends it back.
        """
        paginator = SubResourcePagination()
        page = paginator.paginate_queryset(bodies, request, view=None)
        response = paginator.get_paginated_response(page)
        response["ETag"] = write.version.etag
        return response
