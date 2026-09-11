"""One write to a bundle, whatever part of it the request names.

Every mutating endpoint in this API does the same five things in the same
order, and gets them wrong in the same ways if it does them itself:

1. the bundle has to exist, or there is nothing to write to;
2. the caller has to own it;
3. the caller has to say which version it is editing;
4. the **whole bundle** with the change in it has to satisfy the shape --
   every constraint in the shape is bundle-local, so a part on its own is not
   a unit the shape can judge;
5. the write has to be guarded on that version from inside, and read back,
   because the store answers `200` whether or not the guard held.

So the sequence lives here once rather than in each view. `open_write` does
1-3 and hands back a bundle already read; `apply` does 4 and 5 and records the
history. A view is then only the part that differs: which triples change.

**Refusals travel as exceptions.** A helper that returns either a value or a
refusal makes every call site test which it got, and one forgotten test is a
refusal silently ignored -- so a refusal is raised and a view catches it in the
same place it already catches the store's failures.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass, field
from typing import Optional

from rdflib import Graph, URIRef
from rest_framework import status
from rest_framework.response import Response

from oekg.api_support import bundle_exists, no_such_bundle
from oekg.bundles import BUNDLE_CLASS, bundle_subgraph
from oekg.graph_store import GraphStore
from oekg.history import record_write
from oekg.permissions import may_write_bundle
from oekg.preconditions import precondition_refusal
from oekg.reads import labels_of, read_bundle
from oekg.validation import validate_post_state
from oekg.versioning import (
    BundleVersion,
    guarded_operation,
    mint_write_token,
    read_version,
    write_applied,
)


class Refused(Exception):
    """A refusal a view should return as it stands."""

    def __init__(self, response: Response):
        super().__init__(getattr(response, "status_code", "refused"))
        self.response = response


@dataclass
class BundleWrite:
    """A bundle read, checked, and ready to be changed."""

    uid: str
    store: GraphStore
    pre_state: Graph
    version: BundleVersion
    actor: object = None
    post_state: Optional[Graph] = field(default=None)
    history_recorded: bool = True

    def labels_of(self, iris: list) -> dict:
        """Labels for referenced nodes, answered from the bundle where possible."""
        return labels_of(self.store, iris, self.pre_state)

    def apply(
        self,
        *,
        removed: Graph,
        added: Graph,
        verb: str,
        resource_type: URIRef = BUNDLE_CLASS,
        resource_uuid: Optional[str] = None,
    ) -> None:
        """Validate the post-state, write it under the guard, record it.

        Raises ``Refused`` with a `400` if the shape objects and with a `409`
        if the guard did not hold. Nothing is written in either case.
        """
        self.post_state = bundle_subgraph(self.pre_state - removed + added, self.uid)
        violations = validate_post_state(self.post_state)
        if violations:
            raise Refused(
                Response(
                    {
                        "detail": "The bundle does not conform to the OEKG shape.",
                        "violations": [v.as_dict() for v in violations],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            )

        token = mint_write_token()
        self.store.update(
            guarded_operation(
                self.store,
                self.uid,
                self.version,
                token,
                delete=removed,
                insert=added,
            )
        )
        if not write_applied(self.store, self.uid, token):
            raise Refused(
                Response(
                    {
                        "detail": (
                            "The bundle changed while this request was being "
                            "prepared, so nothing was written. Read it again, "
                            "apply the change to what you get back, and retry."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            )

        before = self.version.number
        self.version = BundleVersion(before + 1, token)
        # The graph has committed. Nothing from here may turn a successful
        # write into an error; a lost history entry is reported beside the
        # success it qualifies, never instead of it.
        self.history_recorded = record_write(
            bundle_uid=self.uid,
            verb=verb,
            actor=self.actor,
            version_before=before,
            version_after=self.version.number,
            removed=removed,
            added=added,
            resource_type=resource_type,
            resource_uuid=resource_uuid,
        )


def open_write(request, uid: str, read_only: bool = False) -> BundleWrite:
    """Read the bundle and check what a write to it needs. Raises ``Refused``.

    Existence first, as it is for the two-step delete: one order for the whole
    API rather than one per endpoint. Reads are public, so answering 404 before
    authorisation reveals nothing a `GET` would not.
    """
    if not bundle_exists(uid):
        raise Refused(no_such_bundle(uid))

    store = GraphStore.from_settings()
    pre_state = read_bundle(store, uid)
    if pre_state is None:
        raise Refused(no_such_bundle(uid))
    version = read_version(store, uid)

    if not read_only:
        if not may_write_bundle(request.user, uid):
            raise Refused(
                Response(
                    {
                        "detail": (
                            "Only an owner of this scenario bundle may change "
                            "it. A bundle with no recorded owner can be "
                            "changed by an administrator only."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            )
        refusal = precondition_refusal(request, version)
        if refusal is not None:
            raise Refused(refusal)

    return BundleWrite(
        uid=uid,
        store=store,
        pre_state=pre_state,
        version=version,
        actor=getattr(request, "user", None),
    )
