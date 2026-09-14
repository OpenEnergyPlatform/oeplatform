"""What a delete of one part actually removes, and what it only unlinks.

This is the most dangerous piece of arithmetic in the API, so it is written
down on its own rather than inside a view.

**The bound is `rdf:type` against a closed list, walked recursively.** Today's
browser delete follows one predicate one hop, and that bound is wrong in both
directions at once: it reaches shared nodes and destroys them -- a model minted
globally, so deleting one bundle strips the label off every other bundle citing
PyPSA -- while never reaching a scenario's own dataset links, which it leaves
behind unreachable from anything. Typing the walk fixes the first; making it
recursive fixes the second.

**Everything else reachable is unlinked, never deleted.** Regions, authors,
contacts, organisations, funders, cited documents and every ontology term
picked from an `sh:in` list keep all their own triples; only the edge into them
goes. Anything untyped or not on the list is treated the same way, which is the
conservative answer for the data this API did not write -- and that is most of
the graph.

**And a guard clause underneath, because a closed list is a claim about the
data.** Before a node is deleted, the store is asked whether anything that
survives this delete still points at it; if so the node is kept and only
unlinked, and the caller is told. This exists because the allowlist was wrong
once while it was being drafted: two classes believed bundle-local turned out to
be shared by every bundle on the platform. The list decides what is a
*candidate*; the guard can only ever downgrade a delete to an unlink, so being
wrong about the list costs an orphan rather than somebody else's data.

The guard also settles the descent: a node that is kept is still reachable, so
its children are still reachable, and they are kept with it -- which falls out
of the fixpoint below rather than needing a rule of its own.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass

from rdflib import RDF, Graph, URIRef

from oekg.bundles import SCENARIO_CLASS, STUDY_REPORT_CLASS
from oekg.dataset_links import DIRECTION_BY_NAME
from oekg.graph_store import GraphStore

# The closed list: the classes this API mints *inside* one bundle, and nothing
# else. Written out rather than derived from `BUNDLE_PARTS` and `DIRECTIONS`,
# because being addressable does not make a resource bundle-local -- the region
# wrapper carries a label and an IRI like a part and is shared by every bundle
# in the platform. A class joins this list by somebody deciding it should, and
# a test in `oekg/tests/test_subresource_delete.py` fails until they do.
BUNDLE_LOCAL_CLASSES = frozenset(
    {
        SCENARIO_CLASS,  # scenario factsheet
        STUDY_REPORT_CLASS,  # study report
        DIRECTION_BY_NAME["input"].node_class,  # input dataset link
        DIRECTION_BY_NAME["output"].node_class,  # output dataset link
    }
)


@dataclass(frozen=True)
class Removal:
    """What a delete comes to: the triples to drop, and the account of them.

    `deleted` and `unlinked` are both reported because the difference is
    visible to the caller and not inferable from the status code: a client that
    asked for a part to go needs to know when the node survived because
    somebody else still cites it.

    `guard` is the same question the plan already answered, in the form the
    write itself can ask -- see `plan_removal`.
    """

    removed: Graph
    deleted: tuple
    unlinked: tuple
    guard: str


def plan_removal(store: GraphStore, subgraph: Graph, target: URIRef) -> Removal:
    """Work out what deleting ``target`` removes from ``subgraph``.

    ``subgraph`` is the bundle as a read returns it -- the caller has it
    already, and it is bounded at the depth the shape allows, which is deeper
    than any bundle-local node sits. Nothing here reads further.

    One query to the store, for the references that ``subgraph`` cannot show:
    a bundle's own subgraph says nothing about who *else* points into it.

    **The plan is read first and asserted again inside the write.** Reading is
    what lets the response say which nodes were kept, which a guard bound into
    the update cannot report -- the store answers `200` whether its pattern
    matched or not. But a read on its own leaves a window: another bundle can
    start citing a node between the plan and the write, and the delete would go
    ahead and take it. So the conclusion travels with the write as `guard`,
    and if it has stopped being true nothing is written and the caller gets a
    `409`. The bundle's own version cannot cover this: a write to *another*
    bundle does not move it.
    """
    candidates = _candidates(subgraph, target)
    incoming = _incoming_references(store, candidates)
    unlink = _links_into(subgraph, target)

    doomed = set(candidates)
    while True:
        removed = _removed_triples(subgraph, doomed, unlink)
        # Shrinking `doomed` shrinks `removed`, so a node can only ever move
        # from deleted to kept -- the loop is monotone and terminates.
        kept = {
            node
            for node in doomed
            if any(triple not in removed for triple in incoming if triple[2] == node)
        }
        if not kept:
            break
        doomed -= kept

    return Removal(
        removed=removed,
        deleted=_described(subgraph, doomed),
        unlinked=_described(subgraph, set(candidates) - doomed),
        guard=_still_unreferenced(doomed, removed),
    )


def _candidates(subgraph: Graph, target: URIRef) -> tuple:
    """``target`` and every bundle-local node reachable from it.

    Optimistic: this is what *could* be deleted if nothing else cited it. The
    guard decides what actually is.
    """
    found, frontier = [], [target]
    seen = set()
    while frontier:
        node = frontier.pop()
        if node in seen:
            continue
        seen.add(node)
        if _is_bundle_local(subgraph, node):
            found.append(node)
            frontier.extend(
                obj
                for obj in subgraph.objects(node, None)
                if isinstance(obj, URIRef) and obj not in seen
            )
    return tuple(found)


def _is_bundle_local(subgraph: Graph, node: URIRef) -> bool:
    return any(
        node_class in BUNDLE_LOCAL_CLASSES
        for node_class in subgraph.objects(node, RDF.type)
    )


def _incoming_references(store: GraphStore, candidates: tuple) -> set:
    """Every triple in the store pointing at one of these nodes.

    Asked of the store rather than of the bundle's subgraph, because the whole
    question is who points in from outside it. One query for all candidates:
    the guard is a property of the set, not of each node in turn.
    """
    if not candidates:
        return set()
    values = " ".join(node.n3() for node in candidates)
    rows = store.select(
        "SELECT ?s ?p ?node WHERE { VALUES ?node { %s } ?s ?p ?node }" % values
    )
    # A blank-node subject comes back as its label and will not compare equal
    # to anything being removed, so it reads as an outside reference. That is
    # the safe way round.
    return {(URIRef(row["s"]), URIRef(row["p"]), URIRef(row["node"])) for row in rows}


def _still_unreferenced(doomed: set, removed: Graph) -> str:
    """The plan's own conclusion, as a pattern the update can test.

    One clause per node about to be deleted: *nothing points at this that this
    write is not itself removing*. If a reference appeared after the plan was
    read, the clause fails, the update matches nothing and the read-back
    reports a conflict -- which is a retry, and the retry sees the reference
    and unlinks instead.

    Written as an exclusion rather than a count so it says what it means: the
    edges this write removes are named, and any other edge disqualifies the
    delete.
    """
    clauses = []
    for index, node in enumerate(sorted(doomed)):
        subject, predicate = f"?ref{index}", f"?refp{index}"
        pattern = f"{subject} {predicate} {node.n3()}"
        removing = [(s, p) for s, p, obj in removed if obj == node]
        if removing:
            ours = " || ".join(
                f"({subject} = {s.n3()} && {predicate} = {p.n3()})"
                for s, p in sorted(removing)
            )
            pattern = f"{pattern} FILTER(!({ours}))"
        clauses.append(f"FILTER NOT EXISTS {{ {pattern} }}")
    return " ".join(clauses)


def _links_into(subgraph: Graph, target: URIRef) -> Graph:
    """The edges that attach ``target`` to the bundle. Always removed.

    Even when the node itself is kept: the request was to remove this part from
    this bundle, and that much is always honoured.
    """
    links = Graph()
    for subject, predicate in subgraph.subject_predicates(target):
        links.add((subject, predicate, target))
    return links


def _removed_triples(subgraph: Graph, doomed: set, unlink: Graph) -> Graph:
    """The triples a delete of ``doomed`` drops, links into the target included.

    A deleted node's outgoing triples go whole, which is what unlinks every
    shared node it pointed at: the edge is the deleted node's, the node at the
    far end keeps everything of its own.
    """
    removed = Graph()
    removed += unlink
    for node in doomed:
        for predicate, obj in subgraph.predicate_objects(node):
            removed.add((node, predicate, obj))
    return removed


def _described(subgraph: Graph, nodes: set) -> tuple:
    """Nodes as a client reads them back: an address and a class."""
    return tuple(
        sorted(
            ({"iri": str(node), "type": _type_of(subgraph, node)} for node in nodes),
            key=lambda entry: entry["iri"],
        )
    )


def _type_of(subgraph: Graph, node: URIRef):
    for node_class in subgraph.objects(node, RDF.type):
        if node_class in BUNDLE_LOCAL_CLASSES:
            return str(node_class)
    return None
