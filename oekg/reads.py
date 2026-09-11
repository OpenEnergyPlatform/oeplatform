"""Reading a bundle out of the graph.

**Bounded depth, not a transitive closure.** A bundle reaches its scenarios in
one hop, a scenario's study regions in two, and a region's reference in three --
which is the longest chain the shape allows, so three hops see a whole bundle
and fewer do not. A closure would also be correct today and would stop needing
thought; it would also be an unbounded walk on a public endpoint, reachable by
anyone who can put a triple in the graph.

The version node is unreachable from here, because it points *at* the bundle
rather than away from it. That is what keeps bookkeeping out of every payload
without a single line of filtering.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import Optional

from rdflib import RDFS, Graph, URIRef

from oekg.bundles import BUNDLE_CLASS, BUNDLE_DEPTH, bundle_iri
from oekg.graph_store import GraphStore


def read_bundle(store: GraphStore, uid: str) -> Optional[Graph]:
    """A bundle and everything reachable from it, or ``None`` if there is none."""
    subgraph = store.construct(_query(uid))
    if (bundle_iri(uid), None, None) not in subgraph:
        return None
    return subgraph


def _query(uid: str) -> str:
    branches = ["{ ?root ?p ?o . BIND(?root AS ?s) }"]
    for depth in range(1, BUNDLE_DEPTH + 1):
        # ?root -> ?n1 -> ... -> ?s, then everything ?s says.
        hops = ["?root"] + [f"?n{step}" for step in range(1, depth)] + ["?s"]
        steps = " ".join(
            f"{hops[step]} ?q{step} {hops[step + 1]} ." for step in range(depth)
        )
        branches.append(f"{{ {steps} ?s ?p ?o }}")
    return (
        "CONSTRUCT { ?s ?p ?o } WHERE { "
        f"  VALUES ?root {{ {bundle_iri(uid).n3()} }} "
        f"  ?root a {BUNDLE_CLASS.n3()} . " + " UNION ".join(branches) + " }"
    )


def labels_of(store: GraphStore, iris: list, known: Optional[Graph] = None) -> dict:
    """The label each of these nodes already carries, for the ones that exist.

    A write consults this so a referenced node keeps its own label and never
    gains a second one -- which would violate the shape for every bundle citing
    it, not just the one being written.

    ``known`` is a graph already in hand; anything answered from it costs no
    query, so a request that has read its bundle asks the store only about
    nodes outside it.
    """
    if not iris:
        return {}
    found, missing = {}, []
    for iri in iris:
        label = known.value(URIRef(iri), RDFS.label) if known is not None else None
        if label is None:
            missing.append(iri)
        else:
            found[iri] = str(label)
    if missing:
        values = " ".join(URIRef(iri).n3() for iri in missing)
        rows = store.select(
            "SELECT ?node ?label WHERE { VALUES ?node { %s } ?node %s ?label }"
            % (values, RDFS.label.n3())
        )
        found.update({row["node"]: row["label"] for row in rows})
    return found
