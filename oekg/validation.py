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

from dataclasses import dataclass
from typing import List, Optional

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
