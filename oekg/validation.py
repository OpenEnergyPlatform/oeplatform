"""Shape validation for scenario bundles, in one function.

**The post-state is what gets validated** -- the bundle as it would be after
the write, assembled in memory, before anything is sent to the store. Not the
diff: a diff carries no ``rdf:type``, so no shape targets it and it conforms
vacuously. That would not be weak validation, it would be a confident false
pass.

The whole graph is unnecessary. The shape has no cross-bundle constraint, so
one bundle's post-state is a complete unit.

The label subset is merged in for the same reason it exists: ``ex:CommonShape``
requires exactly one ``rdfs:label`` on every OEO term a bundle picks, and the
payload carries labels only for the nodes it mints. Only the labels of terms
the post-state actually names are merged -- see ``_with_the_labels_it_names``.

One seam, one function: post-state graph in, violations out. The engine behind
it is then swappable -- the fallback if the library ever stalls is Jena's own
SHACL engine, which this stack already deploys.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from collections import Counter
from dataclasses import dataclass
from typing import List, Optional, Tuple

from pyshacl import validate as pyshacl_validate
from rdflib import RDF, Graph
from rdflib.namespace import RDFS, SH

from oekg.shape import labels_by_term, message_for, shape_graph


@dataclass(frozen=True)
class ShapeViolation:
    """One thing the shape objects to, in the shape's own words."""

    message: str
    focus_node: Optional[str] = None
    path: Optional[str] = None
    value: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "message": self.message,
            "focus_node": self.focus_node,
            "path": self.path,
            "value": self.value,
        }


def validate_post_state(post_state: Graph) -> List[ShapeViolation]:
    """Validate a bundle subgraph. An empty list means it conforms."""
    shape = shape_graph()
    conforms, report, _ = pyshacl_validate(
        _with_the_labels_it_names(post_state),
        shacl_graph=shape,
        advanced=True,
        inference="none",
    )
    if conforms:
        return []

    violations = [
        _violation(report, result)
        for result in report.subjects(RDF.type, SH.ValidationResult)
    ]
    # Sorted so the same invalid payload always reports in the same order:
    # pyshacl walks the report graph, whose iteration order is not stable.
    return sorted(violations, key=lambda v: (v.path or "", v.message))


def introduced_violations(before: Graph, after: Graph) -> Tuple[List, int]:
    """What ``after`` violates that ``before`` did not, and how many it inherited.

    A write is judged by what it **adds**. The alternative -- the post-state must
    conform, full stop -- sounds stricter and is, but it makes an existing defect
    unfixable through this API: the fields most often missing are the ones a
    person would supply by patching, and the patch would be refused for the very
    thing it came to fix. The promise that matters survives either way, because
    nothing invalid is written *by this API*.

    Compared as a **multiset**, so a bundle already missing one required field
    may not come out missing two. And by violation identity -- message, focus
    node, path and value together -- so swapping one violation for another
    counts as introducing one, which comparing counts alone would miss.

    Both graphs must be assembled the same way. Hand this the pruned pre-state,
    not the raw read, or the two differ by how they were built rather than by
    what the write did, and that shows up as violations nobody introduced.
    """
    inherited = Counter(validate_post_state(before))
    arrived = Counter(validate_post_state(after))
    return list((arrived - inherited).elements()), sum(inherited.values())


def _with_the_labels_it_names(post_state: Graph) -> Graph:
    """A fresh graph: the post-state, plus the labels of the terms it names.

    The whole 2,054-triple subset used to be merged into every validation. A
    bundle picks a handful of terms out of it, and the rest is inert: the
    subset holds nothing but ``rdfs:label`` on IRI subjects, so a term the
    post-state never names -- in **any** position -- can be neither a target
    nor a value. Every shape here targets a class, which needs an ``rdf:type``
    the subset does not carry, or the objects of a predicate, which only the
    post-state supplies; and no constraint in it counts or scans across the
    graph. Merging the whole subset was the second largest cost in this app's
    test suite, and leaving out what it never names changes no verdict.

    "Any position" rather than "the objects a shape could target" on purpose:
    the wider rule needs no argument about which nodes a shape can reach, so
    it cannot be invalidated by a shape that grows a new target.

    The argument does rest on one fact about the shape as it stands, and
    ``ShapeTargetsTest`` fails if it stops holding: every target in it is
    ``sh:targetClass`` or ``sh:targetObjectsOf``, and it carries no
    ``sh:targetNode``, ``sh:sparql`` or ``sh:rule`` -- each of which could
    select or read a node the post-state never mentions.

    The filter has to be the referenced IRIs exactly, because ``ex:CommonShape``
    checks the datatype **and the cardinality** of ``rdfs:label`` on every term
    a bundle picks. Dropping one label turns a conforming bundle into a
    violation of a rule nobody broke.

    Freshly built, and the caller's graph is never written to: the merged
    result is handed to the validator and then dropped, so nothing one
    validation adds can reach the next one or the cached artifact.
    """
    graph = Graph()
    labels = labels_by_term()
    named = set()
    for triple in post_state:
        graph.add(triple)
        named.update(node for node in triple if node in labels)
    for term in named:
        for label in labels[term]:
            graph.add((term, RDFS.label, label))
    return graph


def _violation(report: Graph, result) -> ShapeViolation:
    source_shape = report.value(result, SH.sourceShape)
    # The shape's own wording where it has one, the engine's only as a
    # fallback: the API and the shape must never phrase the same rule twice.
    message = message_for(source_shape) or str(
        report.value(result, SH.resultMessage) or "The bundle does not conform."
    )
    return ShapeViolation(
        message=message,
        focus_node=_text(report.value(result, SH.focusNode)),
        path=_text(report.value(result, SH.resultPath)),
        value=_text(report.value(result, SH.value)),
    )


def _text(node) -> Optional[str]:
    return None if node is None else str(node)
