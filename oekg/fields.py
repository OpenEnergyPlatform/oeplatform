"""One field table per resource, driving triples in both directions.

A resource in this API -- a bundle, a scenario factsheet, a study report -- is
a closed set of fields, some literal, some picked from one of the shape's own
lists, some minted nodes. That is the same problem at every level, so the
machinery is written against a **subject and a table** rather than against any
one resource: give it the subject to hang triples off and the table saying what
the fields are, and it can build a create, a patch's delta, and the read that
sends either back.

Writing it once is what makes a read return exactly what a write accepts.
Neither direction can drift from the other, because there is only one place
that says what a field is.

Each table entry names the property the shape validates, so every field is
traceable to the shape rather than to a convention somebody remembered.

**The server mints identifiers**, everywhere and without exception, so a
pipeline cannot collide with -- or overwrite -- somebody else's resource by
choosing a value. And **minted nodes are typed**: the shape's ``sh:class``
constraints require it, the user interface does not do it, and the live graph
carries the violations that produced.

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

HAS_PART = OBO.BFO_0000051
# Both of these are strings per the shape, not IRIs: has-iri points at a page
# somewhere on the platform and is not the node's identity, and has-uuid is the
# identity a sub-resource's URL carries.
HAS_IRI = OEO.OEO_00390094
HAS_UUID = OEO.OEO_00390095

# Kinds of field, which decide how a value becomes triples and back again.
LITERAL = "literal"  # a plain string on the resource
ENUM = "enum"  # IRIs picked from one of the shape's sh:in lists
NODE = "node"  # a referenced or minted node: {iri, label}
PART = "part"  # a resource-local node reached by has-part: {label, iri}
DATES = "dates"  # a set of xsd:dateTime literals
DATE = "date"  # a single xsd:dateTime literal
LINK = "link"  # a URL that IS the node, typed and pointed at


@dataclass(frozen=True)
class ResourceField:
    name: str
    predicate: URIRef
    kind: str
    node_class: Optional[URIRef] = None
    mint_segment: str = ""


def referenced_node_iris(payload: dict, fields: tuple) -> list:
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
    elif field.kind == DATE:
        if value is not None:
            graph.add((subject, field.predicate, Literal(value)))
    elif field.kind == LINK:
        if value:
            # The URL is the node. Nothing else is written onto it: no shape
            # asks a reference for a label, and minting a second node to hold
            # one would leave the bundle pointing at something that is not the
            # document it cites.
            graph.add((subject, field.predicate, URIRef(value)))
            graph.add((URIRef(value), RDF.type, field.node_class))
    elif field.kind == NODE:
        for entry in value:
            iri = entry.get("iri")
            node = URIRef(iri) if iri else minted(field)
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
            node = minted(field)
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
    contact, organisation, funder or author is shared with other bundles, and a
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
        elif field.kind in (DATE, LINK):
            payload[field.name] = optional(graph.value(subject, field.predicate))
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
                        "iri": optional(graph.value(node, HAS_IRI)),
                    }
                    for node in graph.objects(subject, field.predicate)
                    if (node, RDF.type, field.node_class) in graph
                ),
                key=lambda entry: entry["label"],
            )
    return payload


def mint_identifier() -> str:
    """A new identifier for anything this API creates.

    One function rather than one per resource: **no client supplies an
    identifier anywhere in this API**, and that rule is easier to keep true
    where there is a single place it is expressed.
    """
    return str(uuid.uuid4())


def minted(field: ResourceField) -> URIRef:
    """A new IRI for a node this API is creating, under the field's segment."""
    return OEKG[f"{field.mint_segment}/{mint_identifier()}"]


def optional(node) -> Optional[str]:
    return None if node is None else str(node)
