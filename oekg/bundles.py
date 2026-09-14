"""A scenario bundle and its parts, as triples and as payloads.

The field tables live here; the machinery that drives them lives in
`oekg.fields`, because it is the same problem at every level and there are now
three tables playing it: the bundle, the scenario factsheet and the study
report. Each entry names the property the shape validates, so every field is
traceable to the shape.

What is a **part** and what is a **field** is not a judgement call: the shape
decides it. A thing carrying its own has-uuid is addressable and therefore a
part with its own URL; a set of IRIs with labels stays a field on its parent.
Scenario factsheets and study reports carry one, frameworks and models do not.

Two decisions worth stating here rather than leaving to be inferred:

- **The server mints identifiers.** No client-supplied identifier is accepted,
  so a pipeline cannot collide with, or overwrite, somebody else's bundle by
  choosing a value.
- **Frameworks and models are minted per bundle.** They are fields, not
  addressable resources, so nothing outside this bundle should reference them.
  The user interface mints them globally, which is why deleting one bundle
  today strips labels from every other bundle citing the same model.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass
from typing import Optional

from rdflib import RDF, RDFS, Graph, Literal, URIRef

from oekg.fields import (
    DATE,
    DATES,
    DC,
    ENUM,
    HAS_PART,
    HAS_UUID,
    LINK,
    LITERAL,
    NODE,
    OEKG,
    OEO,
    PART,
    ResourceField,
    mint_identifier,
    resource_delta,
    resource_payload,
    resource_triples,
)

BUNDLE_CLASS = OEO.OEO_00020227
SCENARIO_CLASS = OEO.OEO_00000365
STUDY_REPORT_CLASS = OEO.OEO_00020012
# The object of has-reference: the cited document itself, whose IRI is the URL.
REFERENCE_CLASS = OEO.OEO_00000353

# How deep a resource's own graph goes. Bundle -> scenario -> study region ->
# reference is the longest chain the shape allows, so a read that goes three
# hops sees a whole bundle and a read that goes fewer does not. Bounded rather
# than a transitive closure: this is a public endpoint, and a fixed depth
# cannot be talked into walking somewhere large.
BUNDLE_DEPTH = 3

# The closed bundle field set: these and nothing else.
BUNDLE_FIELDS = (
    ResourceField("label", RDFS.label, LITERAL),
    ResourceField("acronym", DC.acronym, LITERAL),
    ResourceField("abstract", DC.abstract, LITERAL),
    ResourceField("descriptors", OEO.OEO_00390071, ENUM),
    ResourceField("sector_divisions", OEO.OEO_00390079, ENUM),
    ResourceField("sectors", OEO.OEO_00020439, ENUM),
    ResourceField("technologies", OEO.OEO_00020438, ENUM),
    ResourceField("energy_carriers", OEO.OEO_00020432, ENUM),
    ResourceField("contacts", OEO.OEO_00000508, NODE, OEO.OEO_00000107, "contact"),
    ResourceField(
        "organisations", OEO.OEO_00000510, NODE, OEO.OEO_00030022, "organisation"
    ),
    ResourceField("funders", OEO.OEO_00000509, NODE, OEO.OEO_00090001, "funder"),
    ResourceField("frameworks", HAS_PART, PART, OEO.OEO_00000172, "framework"),
    ResourceField("models", HAS_PART, PART, OEO.OEO_00000277, "model"),
)

# The closed scenario-factsheet field set. A scenario carries its own has-uuid,
# which is what makes it addressable rather than a field of its parent -- and
# that uuid is the server's to mint, so it is not in this table: no client
# supplies an identifier anywhere in this API.
SCENARIO_FIELDS = (
    ResourceField("label", RDFS.label, LITERAL),
    ResourceField("acronym", DC.acronym, LITERAL),
    ResourceField("abstract", DC.abstract, LITERAL),
    ResourceField("scenario_types", OEO.OEO_00390073, ENUM),
    ResourceField("study_regions", OEO.OEO_00020220, NODE, OEO.OEO_00020032, "region"),
    ResourceField(
        "interacting_regions", OEO.OEO_00020222, NODE, OEO.OEO_00020036, "region"
    ),
    ResourceField("years", OEO.OEO_00020440, DATES),
)

# The closed study-report field set. A study report is the publication a bundle
# is written up in; it carries its own has-uuid, so it is addressable for the
# same reason a scenario is.
#
# `reference` is singular because the shape allows at most one, and it is a
# LINK rather than a NODE: the cited document's URL *is* the node's IRI, so
# there is nothing to mint and nothing to label.
STUDY_REPORT_FIELDS = (
    ResourceField("label", RDFS.label, LITERAL),
    ResourceField("doi", OEO.OEO_00390098, LITERAL),
    ResourceField("publication_date", OEO.OEO_00390096, DATE),
    ResourceField("authors", OEO.OEO_00000506, NODE, OEO.OEO_00000064, "author"),
    ResourceField("reference", OEO.OEO_00390078, LINK, REFERENCE_CLASS),
)


@dataclass(frozen=True)
class BundlePart:
    """An addressable part of a bundle: what it is, and what it is made of.

    One of these per resource the shape gives its own has-uuid. Everything that
    differs between a scenario factsheet and a study report is in here, which is
    what lets one implementation of the endpoints serve both -- and what makes
    adding the next such resource a table rather than a module.
    """

    name: str  # how a refusal names it to a client
    node_class: URIRef
    fields: tuple
    mint_segment: str  # the IRI segment this API mints under
    payload_key: str  # the key it nests under on a bundle create
    detail_route: str  # the named URL of one of them
    sort_field: str  # the field a listing is ordered by


SCENARIO = BundlePart(
    name="scenario",
    node_class=SCENARIO_CLASS,
    fields=SCENARIO_FIELDS,
    mint_segment="scenario",
    payload_key="scenarios",
    detail_route="api:scenario-bundle-scenario",
    sort_field="acronym",
)

STUDY_REPORT = BundlePart(
    name="study report",
    node_class=STUDY_REPORT_CLASS,
    fields=STUDY_REPORT_FIELDS,
    mint_segment="study-report",
    payload_key="study_reports",
    detail_route="api:scenario-bundle-study-report",
    sort_field="label",
)

# Every part a bundle can carry, in the order a create builds them.
BUNDLE_PARTS = (SCENARIO, STUDY_REPORT)


def bundle_iri(uid: str) -> URIRef:
    """The IRI a bundle lives at -- the same one the user interface reads."""
    return OEKG[uid]


def part_iri(part: BundlePart, pid: str) -> URIRef:
    """The IRI a sub-resource this API minted lives at.

    Derived, but **not** the identity: the identity is the has-uuid literal, so
    a part the user interface wrote -- whose IRI this API did not choose -- is
    still reachable by the same identifier its URL carries.
    """
    return OEKG[f"{part.mint_segment}/{pid}"]


def part_nodes(graph: Graph, uid: str, part: BundlePart) -> list:
    """Every part of this kind hanging off this bundle, in the graph given."""
    return [
        node
        for node in graph.objects(bundle_iri(uid), HAS_PART)
        if (node, RDF.type, part.node_class) in graph
    ]


def part_uid(graph: Graph, node: URIRef) -> Optional[str]:
    """The identifier a part node carries, as the shape requires it to."""
    value = graph.value(node, HAS_UUID)
    return None if value is None else str(value)


def find_part(graph: Graph, uid: str, part: BundlePart, pid: str) -> Optional[URIRef]:
    """The part of this bundle with identifier ``pid``, if it has one.

    By the has-uuid literal rather than by rebuilding the IRI, so a part
    written before this API existed is addressable too.
    """
    for node in part_nodes(graph, uid, part):
        if part_uid(graph, node) == pid:
            return node
    return None


def build_part_graph(
    part: BundlePart,
    bundle: URIRef,
    pid: str,
    payload: dict,
    known_labels: dict = None,
) -> Graph:
    """One sub-resource, linked to its bundle and carrying its identity.

    The uuid goes in twice on purpose: once as the literal the shape requires
    and the URL names, and once inside the minted IRI. The literal is the
    identity -- a part the user interface wrote has an IRI this API did not
    choose, and a lookup by literal finds it anyway.
    """
    node = part_iri(part, pid)
    graph = resource_triples(node, part.node_class, part.fields, payload, known_labels)
    graph.add((bundle, HAS_PART, node))
    graph.add((node, HAS_UUID, Literal(pid)))
    return graph


def build_bundle_graph(uid: str, payload: dict, known_labels: dict = None) -> Graph:
    """A whole bundle, including any parts nested in the payload.

    Nesting is accepted here and nowhere else on the write path: a bundle
    `POST` builds its scenarios and study reports with it, while a bundle
    `PATCH` cannot reach one. That asymmetry is what lets a pipeline create a
    whole bundle in one call without giving any call the power to drop its
    parts by omission.
    """
    graph = resource_triples(
        bundle_iri(uid), BUNDLE_CLASS, BUNDLE_FIELDS, payload, known_labels
    )
    for part in BUNDLE_PARTS:
        for nested in payload.get(part.payload_key) or []:
            graph += build_part_graph(
                part, bundle_iri(uid), mint_identifier(), nested, known_labels
            )
    return graph


def bundle_delta(
    uid: str, payload: dict, pre_state: Graph, known_labels: dict = None
) -> tuple:
    """``resource_delta`` for a bundle."""
    return resource_delta(
        bundle_iri(uid), BUNDLE_FIELDS, payload, pre_state, known_labels
    )


def bundle_subgraph(graph: Graph, uid: str) -> Graph:
    """``graph`` narrowed to the bundle, as deep as a read goes.

    Applied to a patch's post-state, this is what makes "validate the
    post-state" mean the state that will actually read back: a node a patch
    unlinked is no longer part of the bundle, so it is no longer part of what
    the shape is asked about.

    It walks to the same depth the read query does, because the two have to
    agree: the post-state validated must be the state a subsequent read
    returns, and a pruner that stopped shorter would hide a scenario's regions
    from the validator.
    """
    narrowed = Graph()
    reached = {bundle_iri(uid)}
    frontier = {bundle_iri(uid)}
    for _ in range(BUNDLE_DEPTH + 1):
        beyond = set()
        for subject in frontier:
            for predicate, obj in graph.predicate_objects(subject):
                narrowed.add((subject, predicate, obj))
                if isinstance(obj, URIRef) and obj not in reached:
                    reached.add(obj)
                    beyond.add(obj)
        frontier = beyond
    return narrowed


def bundle_payload(graph: Graph, uid: str) -> dict:
    """A bundle's own fields. **Sub-resources are not in here.**

    They have their own URLs, so a bundle read names them rather than nesting
    them -- the same asymmetry as the write side, from the other direction. The
    view adds that naming; keeping it out of this function is what lets a read
    be sent straight back to `POST`, where `scenarios` and `study_reports` mean
    *create these*.
    """
    return resource_payload(graph, bundle_iri(uid), BUNDLE_FIELDS)


def part_payload(graph: Graph, node: URIRef, part: BundlePart) -> dict:
    """One sub-resource's fields."""
    return resource_payload(graph, node, part.fields)
