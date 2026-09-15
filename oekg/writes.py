"""One write to a bundle, whatever part of it the request names.

Every mutating endpoint in this API does the same five things in the same
order, and gets them wrong in the same ways if it does them itself:

1. the bundle has to exist, or there is nothing to write to;
2. the caller has to own it;
3. the caller has to say which version it is editing;
4. the **whole bundle** with the change in it has to satisfy the shape -- every
   constraint in the shape is bundle-local, so a part on its own is not a unit
   the shape can judge -- **but only as far as this write is responsible for
   it**: a violation the bundle already had is not this caller's to answer for,
   and refusing it would make an inherited defect unfixable through the API;
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
from rest_framework.response import Response

from oekg.api_support import Refused, bundle_exists
from oekg.bundles import BUNDLE_CLASS, bundle_iri, bundle_subgraph
from oekg.fields import NODE
from oekg.graph_store import GraphStore
from oekg.history import record_bundle_deletion, record_write
from oekg.permissions import forget_ownership, may_write_bundle
from oekg.preconditions import precondition_refusal
from oekg.reads import labels_of, read_bundle
from oekg.removal import Removal
from oekg.validation import introduced_violations
from oekg.versioning import (
    BundleVersion,
    guarded_operation,
    mint_write_token,
    read_version,
    version_guard,
    version_node_triples,
    write_applied,
)


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
    ownership_forgotten: bool = True

    def require_write(self, request) -> None:
        """Refuse unless this caller may write, and said which version.

        Raises ``Refused`` with a `403`, a `428` or a `412`.
        """
        if not may_write_bundle(request.user, self.uid):
            raise Refused(
                Response(
                    {
                        "detail": (
                            "Only an owner of this scenario bundle may change it. "
                            "A bundle with no recorded owner can be changed by an "
                            "administrator only."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            )
        refusal = precondition_refusal(request, self.version)
        if refusal is not None:
            raise Refused(refusal)

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
        guard: str = "",
    ) -> None:
        """Validate the post-state, write it under the guard, record it.

        ``guard`` is an extra pattern bound into the write's own ``WHERE``, for
        a condition the bundle's version cannot express -- a delete uses it to
        assert that nothing outside the bundle started citing the nodes it is
        about to remove. It shares the `409`, because the answer to either is
        the same: read again and retry.

        Raises ``Refused`` with a `400` if the shape objects **to something this
        write introduced**, and with a `409` if the guard did not hold. Nothing
        is written in either case, and nothing on this object is updated either
        -- a caller that catches a refusal must not find a post-state
        describing a write that did not happen.
        """
        if self.post_state is not None:
            raise RuntimeError(
                "This bundle has already been written. A second write needs a "
                "fresh read: this one still holds the state from before the "
                "first, and would silently undo it."
            )

        # Both sides through the same pruner: otherwise they differ by how they
        # were assembled rather than by what the write did, and that difference
        # reads as violations nobody introduced.
        post_state = bundle_subgraph(self.pre_state - removed + added, self.uid)
        introduced, inherited = introduced_violations(
            bundle_subgraph(self.pre_state, self.uid), post_state
        )
        if introduced:
            raise Refused(
                Response(
                    {
                        "detail": (
                            "This change would add violations of the OEKG shape."
                        ),
                        "violations": [v.as_dict() for v in introduced],
                        # Named rather than hidden: the bundle is not clean, and a
                        # caller should be able to learn that without being blamed
                        # for it.
                        "pre_existing_violations": inherited,
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
                condition=guard,
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

    def destroy(self, removal: Removal, acronym: str) -> None:
        """Delete this bundle, its bookkeeping and its records of ownership.

        Not `apply`, and every difference is a consequence of there being no
        bundle afterwards:

        - **Nothing to validate.** The shape judges a bundle; an absent one is
          not a worse bundle, it is no bundle.
        - **No version bump.** The version node goes with the bundle it counts.
          Leaving it is what the browser's delete does (issue #2440), and it
          leaves a node asserting that a bundle is at version 4 when there is
          no bundle -- which the next write would then guard against and match.
        - **The read-back asks whether the bundle is gone**, not whether a
          token landed. A delete's own signal is absence, and absence needs no
          token to be unambiguous: nothing else in this API can make a bundle
          stop existing, so finding it still there can only mean the guard did
          not hold.
        - **What follows the commit is different too.** The ownership rows go,
          and the history records an event rather than a diff.

        Raises ``Refused`` with a `409` if the guard did not hold -- either the
        bundle moved since it was read, or something outside it started citing
        a node this plan was about to delete. The advice is the same for both:
        read it again and retry.
        """
        if self.post_state is not None:
            raise RuntimeError(
                "This bundle has already been written. A delete after a write "
                "would guard on a version that has moved, and would be "
                "refused for a reason nobody could act on."
            )

        removed = Graph()
        removed += removal.removed
        removed += version_node_triples(self.uid, self.version)
        guard = version_guard(self.uid, self.version)
        if removal.guard:
            guard = f"{guard} {removal.guard}"

        self.store.update(self.store.guarded_modification(guard, delete=removed))
        if self.store.ask(
            "ASK { %s a %s }" % (bundle_iri(self.uid).n3(), BUNDLE_CLASS.n3())
        ):
            raise Refused(
                Response(
                    {
                        "detail": (
                            "The bundle changed while this request was being "
                            "prepared, so nothing was deleted. Read it again, "
                            "check it is still the one you meant, and retry."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            )

        # The graph has committed. Nothing from here may turn a successful
        # delete into an error; what is lost is named beside the success it
        # qualifies, never instead of it.
        self.ownership_forgotten = forget_ownership(self.uid)
        self.history_recorded = record_bundle_deletion(
            bundle_uid=self.uid,
            acronym=acronym,
            actor=self.actor,
            version_before=self.version.number,
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
            Response(
                {"detail": f"No scenario bundle {uid}."},
                status=status.HTTP_404_NOT_FOUND,
            )
        )

    store = GraphStore.from_settings()
    pre_state = read_bundle(store, uid)
    if pre_state is None:
        raise Refused(
            Response(
                {"detail": f"No scenario bundle {uid}."},
                status=status.HTTP_404_NOT_FOUND,
            )
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
            Response(
                {
                    "detail": (
                        "A shared node cannot be renamed through this API. "
                        "Reference it by iri and send the label it already has, or "
                        "omit the iri to mint a new node."
                    ),
                    "conflicts": conflicts,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        )
