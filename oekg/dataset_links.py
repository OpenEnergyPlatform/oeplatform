"""A scenario's input and output datasets: what they are, and what they point at.

**Vocabulary first, because "dataset" means three different things here.** This
module is about the *OEKG input/output dataset*: a node hanging off a scenario
factsheet, saying that the scenario consumed or produced some data. What that
node points AT is one of the other two -- an **OEP Table** (a table in the
platform's database) or an **OEP Dataset** (the catalogue entity that groups
several of them). The nested URL disambiguates the endpoint; this docstring
disambiguates the code.

A dataset link has no fields of its own to edit. Everything it holds follows
from what a client says it is -- which direction it is (`type`), what kind of
thing it points at (`ref`), which one (`name`) and, where the client says so
rather than letting it be derived, where (`url`) -- so it is only ever added
or removed. That is why there is no `PATCH`: there is no partial update of one
whose meaning anybody would have to reason about.

**A link is never checked against its target, and never blocked by it.** A
bundle is a published research record: "this scenario used table X" stays true
after X is deleted, so the link outlives the thing it cites and a read says
whether it still resolves -- `oekg.resolution` is where that answer is worked
out. Writing a link therefore touches no table and no
catalogue entry, and a table's owner can still delete it while somebody else's
bundle cites it.

The two platform reference kinds are not equivalent, and the difference is the
client's to choose knowingly: **`ref: table` is the reproducible reference,
`ref: dataset` the current one** -- a catalogue entry's members can change after
a bundle cites it, and that currency is the point of allowing the coarser
reference at all.

**A third kind, `ref: external`, points somewhere this platform has no route
for** -- the live graph holds databus URLs written long before this API. It is
not a shape change: `ref` is never stored, only the address is, in
`oeo:has_iri` as a string, so an external link writes exactly the triples
`ex:DatasetShape` already allows. It exists because a link that cannot be
*expressed* cannot be sent back, and the replace endpoint deletes what a
payload does not mention -- so a kind missing from the payload is a kind
`replace` destroys.

**The address is a payload key of its own (`url`), for every kind.** A link
this API wrote derives it from the name, so a client sending `type`, `ref` and
`name` need not know it; but the existing route takes the label and the address
as two independent values from a client, so a legacy link can carry a real
table's address beside a human-readable title. Reporting only the label would
make such a link round-trip into a *different* link -- one pointing wherever
the title happens to spell -- which is the same silent loss `ref: external`
exists to prevent. So a read always says where a link points, and a write that
says it is believed, checked against the kind it claims.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass
from typing import Optional
from urllib.parse import unquote, urlsplit

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

# The kind for an address this platform has no route for. Deliberately NOT a
# `LinkTarget`: a target is something `oekg.resolution` can look up, and this
# one is by definition not on this platform. Keeping it out of `TARGETS` is
# what leaves `RESOLVERS` complete -- an external link resolves to "this server
# cannot say", which is the honest answer and the one `Resolution.UNKNOWABLE`
# already gives.
EXTERNAL = "external"

#: What a client may write in `ref`, in the order a reader should meet them.
REFERENCE_KINDS = tuple(target.name for target in TARGETS) + (EXTERNAL,)


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


def link_address(request, payload: dict) -> Optional[str]:
    """The address this link points at, as it will be stored.

    Three cases, and the payload decides which:

    - **The payload says where it points** (`url`). Stored verbatim. That is
      the only way an external address can be written at all, and it is also
      what makes a read of *any* link round-trippable: a link the existing
      route wrote can carry a real table's address beside an unrelated title,
      and deriving the address from that title would move the citation.
    - **It names a platform target** (`ref` plus `name`). Derived from the
      router, absolute because the graph is read by things that are not this
      server -- as the platform already does for a table's own identifier, so a
      deployment under another name says its own name.
    - **It names no target at all** (`ref: null`). The shape allows a link with
      no address, so this API can express one; nothing is stored.

    The consequence of building from the request is that the stored URL is not
    the link's identity: two links to the same table written through two host
    names differ as strings. Identity is `link_identity`, which is why it
    compares the answers a client gave and not the string they produced.
    """
    if payload.get("url"):
        return payload["url"]
    if payload["ref"] is None or payload["ref"] == EXTERNAL:
        return None
    return request.build_absolute_uri(target_path(payload["ref"], payload["name"]))


def link_identity(payload: dict) -> tuple:
    """What makes two dataset links the same link.

    **Not the stored URL, except for an external link, where it is the only
    thing.** For a platform target the URL carries whichever host name the
    request arrived on, so comparing it would keep two links written through
    two names for this platform. An external address is not derived from the
    name and no host is being normalised away: it *is* the target, so two
    databus links sharing a human-readable label are two different links, and
    comparing them by that label would refuse the second as a duplicate of the
    first.
    """
    if payload["ref"] == EXTERNAL:
        return (payload["type"], EXTERNAL, payload.get("url"))
    return (payload["type"], payload["ref"], payload["name"])


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
    return reference_target(iri)[0]


def reference_target(iri: str) -> tuple:
    """Which kind of thing a stored link points at, and *which one*.

    The name comes from the URL and never from the label, and that is the
    whole reason this exists beside `reference_kind`. For a link this API
    wrote the two agree, because the URL was built from the name. For a link
    the existing route wrote they are independent values a client supplied
    separately -- the label is a human-readable title and the URL is the
    pointer -- so resolving by label would report a table that is plainly
    there as deleted, which is the fabrication this module refuses everywhere
    else.

    ``(None, None)`` when the path is not one of these pages at all, a URL
    reaching past a target's own page (a table's permissions page, say)
    included: a link to a page *about* a table is not a link to the table.
    """
    path = urlsplit(iri).path
    for target in TARGETS:
        prefix = _prefix(target)
        if path.startswith(prefix):
            name = unquote(path[len(prefix) :])
            return (target.name, name) if name and "/" not in name else (None, None)
    return None, None


def build_dataset_link_graph(
    scenario: URIRef,
    did: str,
    payload: dict,
    iri: Optional[str],
    node: Optional[URIRef] = None,
) -> Graph:
    """The triples one dataset link means.

    Four of them on the node, exactly what the shape's DatasetShape allows: the
    type that says which direction it is, the label, the URL, and the uuid its
    own URL carries. ``oekg:has_id`` is allowed too and deliberately not
    written -- it would be a copy of a database key that nothing keeps in step,
    and a link is resolved by name on read instead.

    ``node`` names an existing link this is rewriting, for the one caller that
    has one: a replace matches a link by the identifier its `_meta` carries,
    and a link the browser wrote lives at an IRI this API did not choose. The
    identity is the uuid either way, which is why the address can differ from
    the one this function would have derived.
    """
    direction = DIRECTION_BY_NAME[payload["type"]]
    node = dataset_link_iri(did) if node is None else node
    graph = Graph()
    graph.add((scenario, direction.predicate, node))
    graph.add((node, RDF.type, direction.node_class))
    graph.add((node, RDFS.label, Literal(payload["name"])))
    # has-iri is a STRING here, per the shape -- it is where the link points
    # and is not the node's identity. Absent for a link that names no target:
    # the shape allows at most one, not at least one.
    if iri is not None:
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
    """One link, in exactly the keys a write accepts.

    ``ref`` is read out of the stored address rather than stored beside it: the
    shape's DatasetShape is closed and has no field for it. An address this
    platform has no route for reads back ``external`` -- honest, and expressible
    on a write, which is what lets a bundle holding one be sent back whole.
    ``ref`` is ``None`` only for a link that stores no address at all, which the
    shape permits and this API can therefore express too.

    ``url`` is the address exactly as stored, on every kind. A client that just
    names a platform target may leave it out and let the router derive it; a
    client sending back what it read keeps the citation exactly where it was.
    """
    iri = stored_iri(graph, node)
    return {
        "type": direction.name,
        "ref": None if iri is None else (reference_kind(iri) or EXTERNAL),
        "name": str(graph.value(node, RDFS.label) or ""),
        "url": iri,
    }


def _prefix(target: LinkTarget) -> str:
    """The path every link of this kind starts with, asked of the router."""
    sentinel = "x"
    path = reverse(target.route, kwargs={target.route_kwarg: sentinel})
    return path[: -len(sentinel)]
