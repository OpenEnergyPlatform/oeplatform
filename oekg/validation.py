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
payload carries labels only for the nodes it mints.

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
from rdflib.namespace import SH

from oekg.shape import label_graph, message_for, shape_graph


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
        post_state + label_graph(),
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
