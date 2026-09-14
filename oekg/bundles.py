"""A scenario bundle and its parts, as triples and as payloads.

One field table per resource drives both directions, so a read returns exactly
what a write accepts and neither can drift from the other. Each table is
traceable to the shape: every entry names the property the shape validates.

The machinery below is written against a *subject and a table*, not against the
bundle, because a scenario factsheet is the same problem one level down -- a
closed set of fields, some literal, some picked from the shape's own lists,
some minted nodes. Two tables today; study reports and dataset links make four,
and that is the point at which the machinery should probably move into a module
of its own.

Three decisions are worth stating here rather than leaving to be inferred:

- **The server mints identifiers.** No client-supplied identifier is accepted,
  so a pipeline cannot collide with, or overwrite, somebody else's bundle by
  choosing a value.
- **Minted nodes are typed.** The shape's ``sh:class`` constraints require it,
  and the user interface does not do it -- the live graph carries violations it
  produced. Writing ``rdf:type`` is one line and it is the difference between a
  bundle that validates and one that only looks valid.
- **Frameworks and models are minted per bundle.** They are fields, not
  addressable resources, so nothing outside this bundle should reference them.
  The user interface mints them globally, which is why deleting one bundle
  today strips labels from every other bundle citing the same model.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef

OEO = Namespace("https://openenergyplatform.org/ontology/oeo/")
OEKG = Namespace("https://openenergyplatform.org/ontology/oekg/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DC = Namespace("http://purl.org/dc/terms/")

BUNDLE_CLASS = OEO.OEO_00020227
SCENARIO_CLASS = OEO.OEO_00000365
HAS_PART = OBO.BFO_0000051
HAS_IRI = OEO.OEO_00390094
HAS_UUID = OEO.OEO_00390095

# How deep a resource's own graph goes. Bundle -> scenario -> study region ->
# reference is the longest chain the shape allows, so a read that goes three
# hops sees a whole bundle and a read that goes fewer does not. Bounded rather
# than a transitive closure: this is a public endpoint, and a fixed depth
# cannot be talked into walking somewhere large.
BUNDLE_DEPTH = 3

# Kinds of field, which decide how a value becomes triples and back again.
LITERAL = "literal"  # a plain string on the resource
ENUM = "enum"  # IRIs picked from one of the shape's sh:in lists
NODE = "node"  # a referenced or minted node: {iri, label}
PART = "part"  # a resource-local node reached by has-part: {label, iri}
DATES = "dates"  # a set of xsd:dateTime literals


@dataclass(frozen=True)
class ResourceField:
    name: str
    predicate: URIRef
    kind: str
    node_class: Optional[URIRef] = None
    mint_segment: str = ""


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


def mint_bundle_uid() -> str:
    """A new bundle identifier. The server's to give, never the client's."""
    return str(uuid.uuid4())


def bundle_iri(uid: str) -> URIRef:
    """The IRI a bundle lives at -- the same one the user interface reads."""
    return OEKG[uid]


def mint_scenario_uid() -> str:
    """A new scenario identifier. The server's to give, never the client's."""
    return str(uuid.uuid4())


def scenario_iri(sid: str) -> URIRef:
    """The IRI a scenario this API minted lives at.

    Derived, but **not** the identity: the identity is the has-uuid literal, so
    a scenario the user interface wrote -- whose IRI this API did not choose --
    is still reachable by the same identifier its URL carries.
    """
    return OEKG[f"scenario/{sid}"]


def scenario_nodes(graph: Graph, uid: str) -> list:
    """Every scenario factsheet hanging off this bundle, in the graph given."""
    return [
        node
        for node in graph.objects(bundle_iri(uid), HAS_PART)
        if (node, RDF.type, SCENARIO_CLASS) in graph
    ]


def scenario_uid(graph: Graph, node: URIRef) -> Optional[str]:
    """The identifier a scenario node carries, as the shape requires it to."""
    value = graph.value(node, HAS_UUID)
    return None if value is None else str(value)


def find_scenario(graph: Graph, uid: str, sid: str) -> Optional[URIRef]:
    """The scenario of this bundle with identifier ``sid``, if it has one.

    By the has-uuid literal rather than by rebuilding the IRI, so a scenario
    written before this API existed is addressable too.
    """
    for node in scenario_nodes(graph, uid):
        if scenario_uid(graph, node) == sid:
            return node
    return None


def referenced_node_iris(payload: dict, fields: tuple = BUNDLE_FIELDS) -> list:
    """Every existing node IRI this payload points at, for **this** table.

    One table, one level. Nesting is the caller's business, because only the
    caller knows which key holds what -- a table that reached for a key by name
    would keep looking for it after being handed a table that has no such key.
    """
    iris = []
    for field in fields:
        if field.kind != NODE:
            continue
        for entry in payload.get(field.name) or []:
            if entry.get("iri"):
                iris.append(entry["iri"])
    return iris


@lru_cache(maxsize=None)
def _by_name(fields: tuple) -> dict:
    """A table's lookup, built once. Cached rather than listed, so adding a
    table is adding a table and nothing else."""
    return {field.name: field for field in fields}


def field_named(fields: tuple, name: str) -> ResourceField:
    """The one entry in ``fields`` called ``name``."""
    return _by_name(fields)[name]


def resource_triples(
    subject: URIRef,
    node_class: URIRef,
    fields: tuple,
    payload: dict,
    known_labels: dict = None,
) -> Graph:
    """Assemble the triples one resource's payload means.

    The result is the post-state to validate and, unchanged, the thing to
    write: nothing is added between validating and writing.

    ``known_labels`` maps an already-existing node IRI to the label it already
    carries. Shared IRIs stay shared -- that is the point of a graph -- so a
    referenced node keeps its own label and this never writes a second one onto
    it. Without that, an additive write would leave a contact other bundles
    cite carrying two labels, violating sh:maxCount 1 for all of them.
    """
    graph = Graph()
    graph.add((subject, RDF.type, node_class))
    for field in fields:
        if field.name in payload:
            graph += field_triples(subject, field, payload[field.name], known_labels)
    return graph


def build_bundle_graph(uid: str, payload: dict, known_labels: dict = None) -> Graph:
    """A whole bundle, including any scenarios nested in the payload.

    Nesting is accepted here and nowhere else on the write path: a bundle
    `POST` builds its scenarios with it, while a bundle `PATCH` cannot reach
    one. That asymmetry is what lets a pipeline create a whole bundle in one
    call without giving any call the power to drop its parts by omission.
    """
    graph = resource_triples(
        bundle_iri(uid), BUNDLE_CLASS, BUNDLE_FIELDS, payload, known_labels
    )
    for scenario in payload.get("scenarios") or []:
        graph += build_scenario_graph(
            bundle_iri(uid), mint_scenario_uid(), scenario, known_labels
        )
    return graph


def build_scenario_graph(
    bundle: URIRef, sid: str, payload: dict, known_labels: dict = None
) -> Graph:
    """One scenario factsheet, linked to its bundle and carrying its identity.

    The uuid goes in twice on purpose: once as the literal the shape requires
    and the URL names, and once inside the minted IRI. The literal is the
    identity -- a scenario the user interface wrote has an IRI this API did not
    choose, and a lookup by literal finds it anyway.
    """
    node = scenario_iri(sid)
    graph = resource_triples(
        node, SCENARIO_CLASS, SCENARIO_FIELDS, payload, known_labels
    )
    graph.add((bundle, HAS_PART, node))
    graph.add((node, HAS_UUID, Literal(sid)))
    return graph


def field_triples(
    subject: URIRef, field: ResourceField, value, known_labels: dict = None
) -> Graph:
    """The triples one field's value means, and nothing else.

    A create needs every field's triples at once; a patch needs exactly the
    named field's, so that a field nobody mentioned is genuinely untouched
    rather than deleted and rewritten identically. Both ask here, so the two
    directions cannot come to disagree about what a field is.
    """
    known_labels = known_labels or {}
    graph = Graph()
    if field.kind == LITERAL:
        if value is not None and value != "":
            graph.add((subject, field.predicate, Literal(value)))
    elif field.kind == ENUM:
        for iri in value:
            graph.add((subject, field.predicate, URIRef(iri)))
    elif field.kind == DATES:
        for moment in value:
            graph.add((subject, field.predicate, Literal(moment)))
    elif field.kind == NODE:
        for entry in value:
            iri = entry.get("iri")
            node = URIRef(iri) if iri else _minted(field)
            graph.add((subject, field.predicate, node))
            graph.add((node, RDF.type, field.node_class))
            if iri and iri in known_labels:
                # An existing shared node is referenced, never rewritten. Its
                # label comes from the graph so the post-state is complete for
                # validation, and the write adds nothing to a node other
                # bundles depend on.
                graph.add((node, RDFS.label, Literal(known_labels[iri])))
            else:
                graph.add((node, RDFS.label, Literal(entry["label"])))
    elif field.kind == PART:
        for entry in value:
            node = _minted(field)
            graph.add((subject, field.predicate, node))
            graph.add((node, RDF.type, field.node_class))
            graph.add((node, RDFS.label, Literal(entry["label"])))
            if entry.get("iri"):
                # has-iri is a STRING on these nodes, per the shape: it points
                # at a factsheet page, it is not the node's identity.
                graph.add((node, HAS_IRI, Literal(entry["iri"])))
    return graph


def linked_field_triples(graph: Graph, subject: URIRef, field: ResourceField) -> Graph:
    """The triples that currently attach ``field``'s values to ``subject``.

    What a patch of that field removes -- **the links only.** A referenced
    contact, organisation or funder is shared with other bundles, and a
    framework or model is on the same "unlink, never delete" footing: nothing
    here reaches into a node's own triples, so no patch can strip a label that
    another bundle is displaying.

    The cost of that rule is an unlinked node left in the graph. It is
    unreachable from the bundle, so no read returns it and no shape is asked
    about it, and deciding which nodes may actually be removed is the typed
    containment walk's job -- a whole slice of its own, because the allowlist
    was already wrong once while it was being drafted. Unlinking fails safe;
    guessing does not.

    Frameworks and models share the has-part predicate, so the type is what
    tells them apart. Deleting by predicate alone would take both.
    """
    triples = Graph()
    for obj in graph.objects(subject, field.predicate):
        if field.kind == PART and (obj, RDF.type, field.node_class) not in graph:
            continue
        triples.add((subject, field.predicate, obj))
    return triples


def resource_delta(
    subject: URIRef,
    fields: tuple,
    payload: dict,
    pre_state: Graph,
    known_labels: dict = None,
) -> tuple:
    """What a patch of ``payload`` removes and what it adds. Nothing else.

    Per named field, so a field the payload does not mention contributes to
    neither side and is genuinely untouched -- not deleted and rewritten
    identically, which would churn every minted node in the bundle.

    A set-valued field that *is* named is replaced whole: its links go and the
    payload's take their place. Emptying such a field is therefore a real
    change, which the shape then judges -- an empty list on a field the shape
    requires is a rejection, never a silent wipe.
    """
    removed, added = Graph(), Graph()
    for name, value in payload.items():
        field = field_named(fields, name)
        removed += linked_field_triples(pre_state, subject, field)
        added += field_triples(subject, field, value, known_labels)
    return removed, added


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


def resource_payload(graph: Graph, subject: URIRef, fields: tuple) -> dict:
    """Read one resource's triples back into exactly what a write would accept."""
    payload = {}
    for field in fields:
        if field.kind == LITERAL:
            value = graph.value(subject, field.predicate)
            payload[field.name] = None if value is None else str(value)
        elif field.kind in (ENUM, DATES):
            payload[field.name] = sorted(
                str(obj) for obj in graph.objects(subject, field.predicate)
            )
        elif field.kind == NODE:
            payload[field.name] = sorted(
                (
                    {
                        "iri": str(node),
                        "label": str(graph.value(node, RDFS.label) or ""),
                    }
                    for node in graph.objects(subject, field.predicate)
                ),
                key=lambda entry: entry["label"],
            )
        elif field.kind == PART:
            # Frameworks and models share has-part; their type tells them apart.
            payload[field.name] = sorted(
                (
                    {
                        "label": str(graph.value(node, RDFS.label) or ""),
                        "iri": _optional(graph.value(node, HAS_IRI)),
                    }
                    for node in graph.objects(subject, field.predicate)
                    if (node, RDF.type, field.node_class) in graph
                ),
                key=lambda entry: entry["label"],
            )
    return payload


def bundle_payload(graph: Graph, uid: str) -> dict:
    """A bundle's own fields. **Scenarios are not in here.**

    They have their own URLs, so a bundle read names them rather than nesting
    them -- the same asymmetry as the write side, from the other direction. The
    view adds that naming; keeping it out of this function is what lets a read
    be sent straight back to `POST`, where `scenarios` means *create these*.
    """
    return resource_payload(graph, bundle_iri(uid), BUNDLE_FIELDS)


def scenario_payload(graph: Graph, node: URIRef) -> dict:
    """One scenario factsheet's fields."""
    return resource_payload(graph, node, SCENARIO_FIELDS)


def _minted(field: ResourceField) -> URIRef:
    return OEKG[f"{field.mint_segment}/{uuid.uuid4()}"]


def _optional(node) -> Optional[str]:
    return None if node is None else str(node)
