"""A scenario's input and output datasets: what they are, and what they point at.

**Vocabulary first, because "dataset" means three different things here.** This
module is about the *OEKG input/output dataset*: a node hanging off a scenario
factsheet, saying that the scenario consumed or produced some data. What that
node points AT is one of the other two -- an **OEP Table** (a table in the
platform's database) or an **OEP Dataset** (the catalogue entity that groups
several of them). The nested URL disambiguates the endpoint; this docstring
disambiguates the code.

A dataset link has no fields of its own to edit. Everything it holds is derived
from three things a client sends -- which direction it is (`type`), what kind of
thing it points at (`ref`), and which one (`name`) -- so it is only ever added
or removed. That is why there is no `PATCH`: there is no partial update of one
whose meaning anybody would have to reason about.

**A link is never checked against its target, and never blocked by it.** A
bundle is a published research record: "this scenario used table X" stays true
after X is deleted, so the link outlives the thing it cites and a read says
whether it still resolves -- `oekg.resolution` is where that answer is worked
out. Writing a link therefore touches no table and no
catalogue entry, and a table's owner can still delete it while somebody else's
bundle cites it.

The two reference kinds are not equivalent, and the difference is the client's
to choose knowingly: **`ref: table` is the reproducible reference, `ref: dataset`
the current one** -- a catalogue entry's members can change after a bundle cites
it, and that currency is the point of allowing the coarser reference at all.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit

from django.urls import NoReverseMatch, reverse
from rdflib import RDF, RDFS, Graph, Literal, URIRef

from oekg.fields import HAS_IRI, HAS_UUID, OEKG, OEO


@dataclass(frozen=True)
class LinkDirection:
    """Which way data flowed, as the shape says it: a predicate and a class."""

    name: str
    predicate: URIRef
    node_class: URIRef


# has information input -> exogenous data, and has information output ->
# endogenous data. Both are the shortcut predicates the shape's DatasetShape
# targets the objects of; the existing manage-datasets route uses RO_0002233 /
# RO_0002234 instead, which the shape never sees.
DIRECTIONS = (
    LinkDirection("input", OEO.OEO_00020437, OEO.OEO_00030029),
    LinkDirection("output", OEO.OEO_00020436, OEO.OEO_00030030),
)
DIRECTION_BY_NAME = {direction.name: direction for direction in DIRECTIONS}


@dataclass(frozen=True)
class LinkTarget:
    """A kind of thing a link can point at, and the route that addresses it."""

    name: str
    route: str
    route_kwarg: str


TARGETS = (
    # An OEP Table: one table in the platform's database.
    LinkTarget("table", "dataedit:view", "table"),
    # An OEP Dataset: the catalogue entity grouping several tables.
    LinkTarget("dataset", "dataedit:dataset-detail", "dataset_name"),
)
TARGET_BY_NAME = {target.name: target for target in TARGETS}


class UnaddressableTarget(Exception):
    """The name given cannot be part of a URL for this kind of target."""


def dataset_link_iri(did: str) -> URIRef:
    """The IRI a dataset link this API minted lives at.

    Derived, but not the identity: the identity is the has-uuid literal, so a
    link written before this API existed is addressable by the same identifier
    its URL carries -- if it has one at all. The existing route writes none,
    which is one of the reasons it is superseded rather than extended.
    """
    return OEKG[f"dataset/{did}"]


def target_iri(request, payload: dict) -> str:
    """The address this link points at, as it will be stored.

    Absolute, because the graph is read by things that are not this server --
    and built from the request, as the platform already does for a table's own
    identifier, so a deployment under another name says its own name. The
    consequence is that the stored URL is not the link's identity: two links to
    the same table written through two host names differ as strings. Identity
    is the three answers a client gives, and everything that compares links
    compares those.
    """
    return request.build_absolute_uri(target_path(payload["ref"], payload["name"]))


def target_path(ref: str, name: str) -> str:
    """The platform path this link points at, from the router rather than a format
    string -- so a route change moves the link with it.

    Raises ``UnaddressableTarget`` when the name cannot appear in such a URL.
    The platform's own routes decide that: a table name is restricted to the
    characters Postgres identifiers use, and no name may contain a slash.
    """
    target = TARGET_BY_NAME[ref]
    try:
        return reverse(target.route, kwargs={target.route_kwarg: name})
    except NoReverseMatch as error:
        raise UnaddressableTarget(
            f"{name!r} is not a possible OEP {ref} name, so there is no page "
            "on this platform for a link to point at."
        ) from error


def reference_kind(iri: str) -> Optional[str]:
    """Which kind of thing a stored link points at, read back out of its URL.

    The URL is all there is: the shape's DatasetShape is closed and carries no
    field saying which kind a link is, so the kind is inferred from the path
    the platform itself would have built. Taken from the router, not from a
    hard-coded segment, so the two cannot drift apart.

    ``None`` for a link pointing somewhere else entirely -- an external URL, or
    one written before these routes existed. That is reported as it is rather
    than guessed at.
    """
    path = urlsplit(iri).path
    for target in TARGETS:
        if path.startswith(_prefix(target)):
            return target.name
    return None


def build_dataset_link_graph(
    scenario: URIRef, did: str, payload: dict, iri: str
) -> Graph:
    """The triples one dataset link means.

    Four of them on the node, exactly what the shape's DatasetShape allows: the
    type that says which direction it is, the label, the URL, and the uuid its
    own URL carries. ``oekg:has_id`` is allowed too and deliberately not
    written -- it would be a copy of a database key that nothing keeps in step,
    and a link is resolved by name on read instead.
    """
    direction = DIRECTION_BY_NAME[payload["type"]]
    node = dataset_link_iri(did)
    graph = Graph()
    graph.add((scenario, direction.predicate, node))
    graph.add((node, RDF.type, direction.node_class))
    graph.add((node, RDFS.label, Literal(payload["name"])))
    # has-iri is a STRING here, per the shape -- it points at a page on the
    # platform and is not the node's identity.
    graph.add((node, HAS_IRI, Literal(iri)))
    graph.add((node, HAS_UUID, Literal(did)))
    return graph


def dataset_link_nodes(graph: Graph, scenario: URIRef) -> list:
    """Every dataset link of this scenario, as (direction, node) pairs."""
    return [
        (direction, node)
        for direction in DIRECTIONS
        for node in graph.objects(scenario, direction.predicate)
    ]


def stored_iri(graph: Graph, node: URIRef) -> Optional[str]:
    """The address this link actually points at, as stored."""
    value = graph.value(node, HAS_IRI)
    return None if value is None else str(value)


def dataset_link_uid(graph: Graph, node: URIRef) -> Optional[str]:
    """The identifier a link node carries, as the shape requires it to."""
    value = graph.value(node, HAS_UUID)
    return None if value is None else str(value)


def find_dataset_link(graph: Graph, scenario: URIRef, did: str):
    """This scenario's link with identifier ``did``, as (direction, node)."""
    for direction, node in dataset_link_nodes(graph, scenario):
        if dataset_link_uid(graph, node) == did:
            return direction, node
    return None, None


def dataset_link_payload(graph: Graph, node: URIRef, direction: LinkDirection) -> dict:
    """One link, in exactly the three keys a write accepts.

    ``ref`` can come back ``None`` for a link this API did not write; that is
    honest rather than a guess, and the name and direction are still true.
    """
    iri = stored_iri(graph, node)
    return {
        "type": direction.name,
        "ref": None if iri is None else reference_kind(iri),
        "name": str(graph.value(node, RDFS.label) or ""),
    }


def _prefix(target: LinkTarget) -> str:
    """The path every link of this kind starts with, asked of the router."""
    sentinel = "x"
    path = reverse(target.route, kwargs={target.route_kwarg: sentinel})
    return path[: -len(sentinel)]
