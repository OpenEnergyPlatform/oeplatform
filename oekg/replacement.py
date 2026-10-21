"""What replacing a bundle comes to: one delta, and an account of what went.

The replace endpoint is the only place in this API where **omission removes**.
Everywhere else a key a payload does not name is genuinely untouched; here the
payload is a declaration of the whole bundle, and anything the graph holds that
the declaration does not mention is taken out. That is the dangerous capability
the rest of the API was shaped to avoid, which is why it lives behind a named
endpoint and a precondition -- and why the arithmetic is written down here
rather than inside a view.

Four rules decide what a replace touches, and each of them is a boundary
somebody could reasonably have drawn elsewhere.

**It is a difference, not a rewrite.** The desired bundle is assembled and
diffed against what is stored, so a replace that declares what is already there
writes nothing at all: no triples, no version bump, no history entry. The
alternative -- remove everything and write the payload back -- is simpler by a
page and wrong in a way a pipeline pays for every run, because it re-mints
every node it touches, churns identifiers and fills the ledger with changes
nobody made.

**Identity comes from `_meta.uid`.** A nested scenario, study report or dataset
link that names the one it already is keeps its node; one that names nothing is
created. Without this a re-import would delete and recreate every part of the
bundle on every run -- which is the same churn, wearing the history's clothes.
A resource the graph holds with **no** identifier at all -- which the shape
forbids and the browser can nevertheless produce -- has nothing to send back, so
a declaration cannot name it and replaces it instead. That is stated rather than
worked around: the alternative is matching by content, which would silently
adopt a different resource whenever two of them looked alike.

**Removal goes through the typed containment walk**, exactly as a `DELETE` on
each of those resources would: a node another bundle cites is unlinked rather
than destroyed, and the guard can only ever downgrade. Omission is a different
way of *saying* which nodes go, not a different rule about what going means.

**What this API cannot express, it does not remove.** The scope of a replace is
the bundle's own field predicates and its bundle-local nodes. A shared node --
a contact, a region, an author -- is unlinked and keeps its own triples, and a
predicate on the bundle that no field table names is left where it is. A
declaration made in this API's vocabulary is a declaration about this API's
vocabulary; taking silence about a predicate nobody can send as permission to
delete it would make the endpoint destroy exactly the data it cannot show its
caller.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass
from typing import Optional

from rdflib import RDF, RDFS, Graph, URIRef
from rest_framework import status
from rest_framework.response import Response

from oekg.api_support import Refused
from oekg.bundles import (
    BUNDLE_CLASS,
    BUNDLE_FIELDS,
    BUNDLE_PARTS,
    BundlePart,
    build_part_graph,
    bundle_iri,
    find_part,
    part_iri,
)
from oekg.dataset_links import (
    build_dataset_link_graph,
    find_dataset_link,
    link_identity,
)
from oekg.fields import (
    DATE,
    DATES,
    ENUM,
    HAS_IRI,
    HAS_PART,
    LINK,
    LITERAL,
    NODE,
    PART,
    ResourceField,
    field_triples,
    linked_field_triples,
    mint_identifier,
    optional,
)
from oekg.graph_store import GraphStore
from oekg.removal import bundle_local_nodes, plan_discarded_removal
from oekg.serializers import IDENTIFIED_BY

#: What a field holds when the declaration does not mention it. This is where
#: omission becomes deletion, so it is a table rather than a default argument:
#: a field kind added without an entry here fails loudly instead of quietly
#: keeping whatever was there.
EMPTY_VALUE = {
    LITERAL: None,
    DATE: None,
    LINK: None,
    ENUM: [],
    DATES: [],
    NODE: [],
    PART: [],
}


@dataclass(frozen=True)
class Replacement:
    """The one write a replace makes, and what a client is told about it.

    ``removed`` and ``added`` are the two halves of a single guarded
    modification -- never a delete followed by a create, because one request is
    one transaction and two would leave a window in which the bundle does not
    exist.

    ``deleted`` and ``unlinked`` are the same report a `DELETE` gives, for the
    same reason: a node something else still cites is kept and detached, and no
    status code can say that. Only the **downgraded** nodes are listed as
    unlinked, as everywhere else -- the shared contacts and regions a
    declaration drops are the rule that always applies, not the news.
    """

    removed: Graph
    added: Graph
    deleted: tuple
    unlinked: tuple
    guard: str

    @property
    def changes_nothing(self) -> bool:
        """Whether the bundle already is what the payload declares.

        The second run of an idempotent pipeline. Nothing is written, so
        nothing is versioned and nothing is recorded: a history entry with an
        empty diff would say a change happened, and the point of the endpoint
        is that it did not.
        """
        return not len(self.removed) and not len(self.added)

    def as_meta(self) -> dict:
        """What the response says the replace came to."""
        return {"deleted": list(self.deleted), "unlinked": list(self.unlinked)}


def plan_replacement(
    store: GraphStore,
    pre_state: Graph,
    uid: str,
    payload: dict,
    known_labels: dict = None,
    address=None,
) -> Replacement:
    """Work out the one write that makes ``uid`` be what ``payload`` declares.

    Raises ``Refused`` with a `400` for a payload that cannot be applied at
    all: one naming a part or a link that is not in this bundle, or declaring
    the same thing twice. Those are refusals about the declaration itself, and
    they happen before anything is validated or written.
    """
    bundle = bundle_iri(uid)
    desired, scope = Graph(), Graph()
    desired.add((bundle, RDF.type, BUNDLE_CLASS))

    for field in BUNDLE_FIELDS:
        desired += _declared_field_triples(
            pre_state, bundle, field, payload, known_labels
        )
        scope += linked_field_triples(pre_state, bundle, field)

    kept = set()
    for part in BUNDLE_PARTS:
        for nested in payload.get(part.payload_key) or []:
            node, pid = _matched_part(pre_state, uid, part, nested, kept)
            desired += build_part_graph(part, bundle, pid, nested, known_labels, node)
            if node is not None:
                kept.add(node)
                scope += _own_triples(pre_state, node)
                scope.add((bundle, HAS_PART, node))
            links, linked, held = _declare_links(
                pre_state, part, node, pid, nested, address
            )
            desired += links
            scope += linked
            kept |= held

    discarded = tuple(
        node for node in bundle_local_nodes(pre_state, uid) if node not in kept
    )
    removal = plan_discarded_removal(store, pre_state, discarded, spared=tuple(kept))

    removed = Graph()
    removed += scope - desired
    removed += removal.removed
    return Replacement(
        removed=removed,
        added=desired - pre_state,
        deleted=removal.deleted,
        unlinked=removal.unlinked,
        guard=removal.guard,
    )


def _declared_field_triples(
    pre_state: Graph,
    subject: URIRef,
    field: ResourceField,
    payload: dict,
    known_labels: Optional[dict],
) -> Graph:
    """One field of the declaration, as triples -- omission included.

    A field the payload does not name is declared **empty**, which is the whole
    difference between this and a patch's delta. Everything else is the shared
    field machinery, so a replace and a create write a field identically.
    """
    value = payload.get(field.name, EMPTY_VALUE[field.kind])
    if field.kind == PART:
        return _declared_part_triples(pre_state, subject, field, value)
    return field_triples(subject, field, value, known_labels)


def _declared_part_triples(
    pre_state: Graph, subject: URIRef, field: ResourceField, value: list
) -> Graph:
    """Frameworks and models, reusing the node that already says this.

    These are the one kind of field with no identity a client can send: the
    read gives a label and a factsheet address, and the node holding them is
    minted per bundle. Minting again for a value that is already there would
    make every re-import rewrite every framework in the bundle -- a real change
    in the history, an orphan in the graph, and a different IRI for the same
    fact. So a declared entry that matches one already linked keeps its node,
    and only a genuinely new one is minted.
    """
    available = {}
    for node in pre_state.objects(subject, field.predicate):
        if (node, RDF.type, field.node_class) not in pre_state:
            continue
        key = (
            str(pre_state.value(node, RDFS.label) or ""),
            optional(pre_state.value(node, HAS_IRI)),
        )
        available.setdefault(key, []).append(node)

    graph = Graph()
    for entry in value:
        key = (entry["label"], entry.get("iri") or None)
        existing = available.get(key)
        if existing:
            node = existing.pop(0)
            graph.add((subject, field.predicate, node))
            graph += _own_triples(pre_state, node)
        else:
            graph += field_triples(subject, field, [entry])
    return graph


def _matched_part(
    pre_state: Graph, uid: str, part: BundlePart, nested: dict, kept: set
) -> tuple:
    """The existing part this declaration names, or ``None`` and a fresh id."""
    pid = nested.get(IDENTIFIED_BY)
    if pid is None:
        return None, mint_identifier()
    node = find_part(pre_state, uid, part, pid)
    if node is None:
        raise _unknown(part.name, pid)
    if node in kept:
        raise _declared_twice(part.name, pid)
    return node, pid


def _declare_links(
    pre_state: Graph,
    part: BundlePart,
    node: Optional[URIRef],
    pid: str,
    nested: dict,
    address,
) -> tuple:
    """The dataset links declared inside one part.

    Three answers, returned rather than written into graphs the caller passed
    in: the triples these links mean, the triples of theirs this write may
    therefore remove, and the existing link nodes the declaration keeps -- so
    the walk that decides what goes can leave those alone.

    A link is matched by the identifier a read gave it, exactly as a part is.
    It is also checked for being declared twice, and that check compares what
    makes two links the same link rather than their three keys -- an external
    link is its address, so two databus citations sharing a title are two
    citations.
    """
    desired, scope = Graph(), Graph()
    if not part.nested_links:
        return desired, scope, set()
    parent = node if node is not None else part_iri(part, pid)
    kept, declared = set(), set()
    for link in nested.get(part.nested_links) or []:
        identity = link_identity(link)
        if identity in declared:
            raise _link_declared_twice(link)
        declared.add(identity)
        link_node, did = _matched_link(pre_state, parent, link)
        if link_node is not None and link_node in kept:
            # Two entries naming one link and saying different things about it.
            # Caught here rather than left to the shape, which would refuse it
            # for carrying two labels -- true, and no help at all in finding
            # which entry caused it.
            raise _declared_twice("dataset link", did)
        desired += build_dataset_link_graph(
            parent, did, link, address(link) if address else None, link_node
        )
        if link_node is not None:
            kept.add(link_node)
            scope += _own_triples(pre_state, link_node)
    return desired, scope, kept


def _matched_link(pre_state: Graph, scenario: URIRef, link: dict) -> tuple:
    """The existing link this declaration names, or ``None`` and a fresh id.

    ``(node, identifier)``, the same way round as `_matched_part`: they answer
    the same question one level apart, and two orders for one answer is the
    kind of thing that reads fine and is wrong at the call site.
    """
    did = link.get(IDENTIFIED_BY)
    if did is None:
        return None, mint_identifier()
    _, node = find_dataset_link(pre_state, scenario, did)
    if node is None:
        raise _unknown("dataset link", did)
    return node, did


def _own_triples(graph: Graph, node: URIRef) -> Graph:
    """Everything ``node`` itself says. Never what anything says about it."""
    triples = Graph()
    for predicate, obj in graph.predicate_objects(node):
        triples.add((node, predicate, obj))
    return triples


def _unknown(what: str, identifier: str) -> Refused:
    return Refused(
        Response(
            {
                "detail": (
                    f"This bundle has no {what} {identifier}. A replace matches "
                    "a nested resource by the identifier in its `_meta.uid`, "
                    "and creates one that names none -- so an identifier that "
                    "is not here is a payload built from a different bundle, "
                    "not a request to create something. Nothing was written."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    )


def _declared_twice(what: str, identifier: str) -> Refused:
    return Refused(
        Response(
            {
                "detail": (
                    f"The payload declares the {what} {identifier} twice. One "
                    "resource cannot be two of the bundle's parts, and which "
                    "of the two the bundle should end up as is not something "
                    "this API may guess. Nothing was written."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    )


def _link_declared_twice(link: dict) -> Refused:
    return Refused(
        Response(
            {
                "detail": (
                    "The payload declares the same dataset link twice on one "
                    "scenario. Two nodes saying one thing would leave a later "
                    "`DELETE` ambiguous, which is why a duplicate is refused "
                    "rather than quietly collapsed. Nothing was written."
                ),
                "link": {key: link.get(key) for key in ("type", "ref", "name", "url")},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    )
