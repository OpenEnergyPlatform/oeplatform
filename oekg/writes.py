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

So the sequence lives here once rather than in each view. `open_bundle` does 1,
`require_write` does 2 and 3, and `apply` does 4 and 5 and records the history.
They are three calls rather than one so a sub-resource view can check that
*its* part exists between the first and the second, and keep the same order
one level down. A view is then only the part that differs: which triples change.

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
from rest_framework.exceptions import APIException

from oekg.api_support import bundle_exists
from oekg.bundles import BUNDLE_CLASS, NODE, bundle_subgraph
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


class Refused(APIException):
    """A refusal, raised where it is decided and rendered by the framework.

    An ``APIException`` rather than a plain one so that no view needs a clause
    to catch it: the framework turns it into the response it already carries.
    A helper that *returned* a refusal would make every call site test which of
    the two things it got, and one forgotten test is a refusal silently
    ignored.
    """

    def __init__(self, detail, status_code: int):
        self.status_code = status_code
        super().__init__(detail)


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

    def require_write(self, request) -> None:
        """Refuse unless this caller may write, and said which version.

        Raises ``Refused`` with a `403`, a `428` or a `412`.
        """
        if not may_write_bundle(request.user, self.uid):
            raise Refused(
                {
                    "detail": (
                        "Only an owner of this scenario bundle may change it. "
                        "A bundle with no recorded owner can be changed by an "
                        "administrator only."
                    )
                },
                status.HTTP_403_FORBIDDEN,
            )
        refusal = precondition_refusal(request, self.version)
        if refusal is not None:
            raise Refused(refusal.data, refusal.status_code)

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
        if the guard did not hold. Nothing is written in either case, and
        nothing on this object is updated either -- a caller that catches a
        refusal must not find a post-state describing a write that did not
        happen.
        """
        if self.post_state is not None:
            raise RuntimeError(
                "This bundle has already been written. A second write needs a "
                "fresh read: this one still holds the state from before the "
                "first, and would silently undo it."
            )

        post_state = bundle_subgraph(self.pre_state - removed + added, self.uid)
        violations = validate_post_state(post_state)
        if violations:
            raise Refused(
                {
                    "detail": "The bundle does not conform to the OEKG shape.",
                    "violations": [v.as_dict() for v in violations],
                },
                status.HTTP_400_BAD_REQUEST,
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
                {
                    "detail": (
                        "The bundle changed while this request was being "
                        "prepared, so nothing was written. Read it again, "
                        "apply the change to what you get back, and retry."
                    )
                },
                status.HTTP_409_CONFLICT,
            )

        # Only now: everything above could still have refused, and a refusal
        # must leave this object describing the bundle as it still is.
        self.post_state = post_state
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


def open_bundle(request, uid: str) -> BundleWrite:
    """Read a bundle, or refuse with a `404`. Raises ``Refused``.

    **Existence first**, as it is for the two-step delete: one order for the
    whole API rather than one per endpoint. Reads are public, so answering 404
    before authorisation reveals nothing a `GET` would not -- and a request for
    something that is not there should hear that, rather than being told its
    precondition is missing for a resource that does not exist.

    Separate from ``require_write`` so a sub-resource view can check that *its*
    part exists in between, and keep the same order one level down.
    """
    if not bundle_exists(uid):
        raise Refused(
            {"detail": f"No scenario bundle {uid}."}, status.HTTP_404_NOT_FOUND
        )

    store = GraphStore.from_settings()
    pre_state = read_bundle(store, uid)
    if pre_state is None:
        raise Refused(
            {"detail": f"No scenario bundle {uid}."}, status.HTTP_404_NOT_FOUND
        )

    return BundleWrite(
        uid=uid,
        store=store,
        pre_state=pre_state,
        version=read_version(store, uid),
        actor=getattr(request, "user", None),
    )


def refuse_renames(payload: dict, known_labels: dict, fields: tuple) -> None:
    """Refuse a payload that gives an existing node a different label.

    **The API offers no rename.** Shared IRIs stay shared -- that is the point
    of a graph -- but a shared contact, organisation, funder or region is cited
    by other bundles, so letting one payload rewrite its label would change
    every one of them. Referencing such a node is allowed; renaming it is not,
    and the difference is the label sent alongside the iri.

    Driven by the field table rather than by a list of field names, because a
    list stops covering a table the moment that table gains a node field, and
    the refusal then quietly passes writes it should refuse.
    """
    conflicts = [
        {
            "iri": entry["iri"],
            "stored_label": known_labels[entry["iri"]],
            "sent_label": entry["label"],
        }
        for field in fields
        if field.kind == NODE
        for entry in (payload.get(field.name) or [])
        if entry.get("iri") in known_labels
        and entry["label"] != known_labels[entry["iri"]]
    ]
    if conflicts:
        raise Refused(
            {
                "detail": (
                    "A shared node cannot be renamed through this API. "
                    "Reference it by iri and send the label it already has, or "
                    "omit the iri to mint a new node."
                ),
                "conflicts": conflicts,
            },
            status.HTTP_400_BAD_REQUEST,
        )
