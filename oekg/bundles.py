"""A scenario bundle, as triples and as a payload.

One field table drives both directions, so a read returns exactly what a write
accepts and neither can drift from the other. The table is traceable to the
shape: every entry names the property the shape validates.

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
from typing import Optional

from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef

OEO = Namespace("https://openenergyplatform.org/ontology/oeo/")
OEKG = Namespace("https://openenergyplatform.org/ontology/oekg/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DC = Namespace("http://purl.org/dc/terms/")

BUNDLE_CLASS = OEO.OEO_00020227
HAS_PART = OBO.BFO_0000051
HAS_IRI = OEO.OEO_00390094

# Kinds of field, which decide how a value becomes triples and back again.
LITERAL = "literal"  # a plain string on the bundle
ENUM = "enum"  # IRIs picked from one of the shape's sh:in lists
NODE = "node"  # a referenced or minted node: {iri, label}
PART = "part"  # a bundle-local node reached by has-part: {label, iri}


@dataclass(frozen=True)
class BundleField:
    name: str
    predicate: URIRef
    kind: str
    node_class: Optional[URIRef] = None
    mint_segment: str = ""


# The closed bundle field set: these and nothing else.
BUNDLE_FIELDS = (
    BundleField("label", RDFS.label, LITERAL),
    BundleField("acronym", DC.acronym, LITERAL),
    BundleField("abstract", DC.abstract, LITERAL),
    BundleField("descriptors", OEO.OEO_00390071, ENUM),
    BundleField("sector_divisions", OEO.OEO_00390079, ENUM),
    BundleField("sectors", OEO.OEO_00020439, ENUM),
    BundleField("technologies", OEO.OEO_00020438, ENUM),
    BundleField("energy_carriers", OEO.OEO_00020432, ENUM),
    BundleField("contacts", OEO.OEO_00000508, NODE, OEO.OEO_00000107, "contact"),
    BundleField(
        "organisations", OEO.OEO_00000510, NODE, OEO.OEO_00030022, "organisation"
    ),
    BundleField("funders", OEO.OEO_00000509, NODE, OEO.OEO_00090001, "funder"),
    BundleField("frameworks", HAS_PART, PART, OEO.OEO_00000172, "framework"),
    BundleField("models", HAS_PART, PART, OEO.OEO_00000277, "model"),
)

_FIELDS_BY_NAME = {field.name: field for field in BUNDLE_FIELDS}


def mint_bundle_uid() -> str:
    """A new bundle identifier. The server's to give, never the client's."""
    return str(uuid.uuid4())


def bundle_iri(uid: str) -> URIRef:
    """The IRI a bundle lives at -- the same one the user interface reads."""
    return OEKG[uid]


def referenced_node_iris(payload: dict) -> list:
    """Every existing node IRI the payload points at, across all node fields."""
    iris = []
    for field in BUNDLE_FIELDS:
        if field.kind != NODE:
            continue
        for entry in payload.get(field.name) or []:
            if entry.get("iri"):
                iris.append(entry["iri"])
    return iris


def bundle_field(name: str) -> BundleField:
    """The one entry in the field table called ``name``."""
    return _FIELDS_BY_NAME[name]


def build_bundle_graph(uid: str, payload: dict, known_labels: dict = None) -> Graph:
    """Assemble the triples a bundle payload means.

    The result is the post-state to validate and, unchanged, the thing to
    write: nothing is added between validating and writing.

    ``known_labels`` maps an already-existing node IRI to the label it already
    carries. Shared IRIs stay shared -- that is the point of a graph -- so a
    referenced node keeps its own label and this never writes a second one onto
    it. Without that, an additive write would leave a contact other bundles
    cite carrying two labels, violating sh:maxCount 1 for all of them.
    """
    graph = Graph()
    graph.add((bundle_iri(uid), RDF.type, BUNDLE_CLASS))
    for field in BUNDLE_FIELDS:
        if field.name in payload:
            graph += field_triples(uid, field, payload[field.name], known_labels)
    return graph


def field_triples(
    uid: str, field: BundleField, value, known_labels: dict = None
) -> Graph:
    """The triples one field's value means, and nothing else.

    A create needs every field's triples at once; a patch needs exactly the
    named field's, so that a field nobody mentioned is genuinely untouched
    rather than deleted and rewritten identically. Both ask here, so the two
    directions cannot come to disagree about what a field is.
    """
    known_labels = known_labels or {}
    graph = Graph()
    subject = bundle_iri(uid)
    if field.kind == LITERAL:
        if value is not None and value != "":
            graph.add((subject, field.predicate, Literal(value)))
    elif field.kind == ENUM:
        for iri in value:
            graph.add((subject, field.predicate, URIRef(iri)))
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


def linked_field_triples(graph: Graph, uid: str, field: BundleField) -> Graph:
    """The triples that currently attach ``field``'s values to the bundle.

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
    subject = bundle_iri(uid)
    triples = Graph()
    for obj in graph.objects(subject, field.predicate):
        if field.kind == PART and (obj, RDF.type, field.node_class) not in graph:
            continue
        triples.add((subject, field.predicate, obj))
    return triples


def bundle_subgraph(graph: Graph, uid: str) -> Graph:
    """``graph`` narrowed to the bundle and one hop out, as a read returns it.

    Applied to a patch's post-state, this is what makes "validate the
    post-state" mean the state that will actually read back: a node a patch
    unlinked is no longer part of the bundle, so it is no longer part of what
    the shape is asked about.
    """
    subject = bundle_iri(uid)
    narrowed = Graph()
    for predicate, obj in graph.predicate_objects(subject):
        narrowed.add((subject, predicate, obj))
        if isinstance(obj, URIRef):
            for node_predicate, node_object in graph.predicate_objects(obj):
                narrowed.add((obj, node_predicate, node_object))
    return narrowed


def bundle_payload(graph: Graph, uid: str) -> dict:
    """Read a bundle subgraph back into exactly what a write would accept."""
    subject = bundle_iri(uid)
    payload = {}
    for field in BUNDLE_FIELDS:
        if field.kind == LITERAL:
            value = graph.value(subject, field.predicate)
            payload[field.name] = None if value is None else str(value)
        elif field.kind == ENUM:
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


def _minted(field: BundleField) -> URIRef:
    return OEKG[f"{field.mint_segment}/{uuid.uuid4()}"]


def _optional(node) -> Optional[str]:
    return None if node is None else str(node)
