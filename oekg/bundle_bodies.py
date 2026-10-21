"""How everything in a bundle reads back: one body shape per resource.

Extracted when the bundle read stopped being assembled from one source. A
bundle body is now its own fields, its parts, and each scenario's dataset
links -- three modules' worth of knowledge, needed by four view modules and by
the replace endpoint -- so the assembly lives here and the views ask for it.

**A bundle read is round-trippable, and the dataset links are why that had to
change.** A read used to name a bundle's scenarios and study reports and stay
silent about their dataset links, which have their own URLs. That was
defensible until `replace` arrived: its payload declares the whole bundle and
anything absent from it is removed, so a citation the payload could not
mention was a citation every re-import destroyed. Links therefore nest under
each scenario, on the read and on the nested create, and a client sends back
what it read without losing what it cites. Issue #2473 is where that was
decided.

Two rules shape every body here, both from WF-12:

- **A read returns exactly what a write accepts, plus `_meta`.** The top level
  maps one-to-one onto the closed shape, which is what keeps that check
  structural instead of an exception list.
- **Everything read-only is under `_meta`** -- the identifier, the address, the
  resolved labels, and what a citation resolves to today.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from rdflib import Graph, URIRef
from rest_framework.response import Response

from oekg.bundles import (
    BUNDLE_FIELDS,
    BUNDLE_PARTS,
    BundlePart,
    bundle_iri,
    bundle_payload,
    part_nodes,
    part_payload,
    part_uid,
)
from oekg.dataset_links import (
    dataset_link_nodes,
    dataset_link_payload,
    dataset_link_uid,
    reference_target,
    stored_iri,
)
from oekg.labels import labelled
from oekg.resolution import resolve
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.versioning import BundleVersion

# A dataset link has no field table, because it has no fields: everything it
# holds follows from its type, its target and its name. That is the same fact
# that gives it no `PATCH`, and it is why resolving its picked ontology terms
# is an empty answer rather than a refusal.
NO_PICKED_TERMS = ()


def part_bodies(
    graph: Graph, uid: str, part: BundlePart, expand: frozenset = frozenset()
) -> list:
    """Every part of this kind, in the form a write accepts them nested."""
    bodies = [
        part_body(graph, node, uid, part, expand)
        for node in part_nodes(graph, uid, part)
    ]
    bodies.sort(key=lambda body: body[part.sort_field] or "")
    return bodies


def part_body(
    graph: Graph,
    node,
    uid: str,
    part: BundlePart,
    expand: frozenset = frozenset(),
) -> dict:
    return labelled(
        {
            **part_payload(graph, node, part),
            READ_ONLY_CONTAINER: {
                "uid": part_uid(graph, node),
                "iri": str(node),
                "type": str(part.node_class),
                "bundle": uid,
            },
        },
        part.fields,
        expand,
    )


def nested_part_bodies(
    graph: Graph, uid: str, part: BundlePart, expand: frozenset = frozenset()
) -> list:
    """The same parts, as they appear *inside* a bundle body.

    Which is the same thing plus the links a scenario carries. Separate from
    `part_bodies` because the part's own collection endpoint is not the place
    for them -- there a link has its own URL, and add-and-remove is its whole
    contract.
    """
    bodies = part_bodies(graph, uid, part, expand)
    if not part.nested_links:
        return bodies
    for body in bodies:
        # The node is read back out of the body rather than walked again, so
        # the ordering `part_bodies` settled is the one the links hang off --
        # a second walk would have to repeat that sort to stay in step.
        node = URIRef(body[READ_ONLY_CONTAINER]["iri"])
        body[part.nested_links] = link_bodies(
            graph, node, uid, body[READ_ONLY_CONTAINER]["uid"], expand
        )
    return bodies


def link_bodies(
    graph: Graph, scenario, uid: str, sid: str, expand: frozenset = frozenset()
) -> list:
    pairs = [
        (node, link_body(graph, node, direction, uid, sid, expand))
        for direction, node in dataset_link_nodes(graph, scenario)
    ]
    pairs.sort(key=lambda pair: (pair[1]["type"], pair[1]["name"]))
    resolve_into(graph, pairs)
    return [body for _, body in pairs]


def resolve_into(graph: Graph, pairs: list) -> None:
    """Say, for every one of these links, what it points at right now.

    Done to the whole list at once and never to one link at a time: resolution
    costs a fixed few relational queries for any number of links, and a
    per-link version of this would put a query per citation on a public
    endpoint. A single link is simply a list of one.

    What is looked up comes from each link's stored **URL**, not from the
    `name` in its body. The two agree for every link this API wrote, because
    the URL was built from the name -- but the existing route takes them as two
    separate values from a client, so a legacy link can carry a real table's
    URL beside a human-readable title. Resolving by that title would report a
    table that is plainly there as deleted.
    """
    resolutions = resolve(
        [reference_target(stored_iri(graph, node) or "") for node, _ in pairs]
    )
    for (_, body), resolution in zip(pairs, resolutions):
        body[READ_ONLY_CONTAINER].update(resolution.as_meta())


def link_body(
    graph: Graph,
    node,
    direction,
    uid: str,
    sid: str,
    expand: frozenset = frozenset(),
) -> dict:
    """One link: the keys a write accepts, and the rest read-only.

    ``_meta.target_iri`` repeats the payload's own `url`, and is kept because
    it is what a client written against the earlier shape reads. The payload is
    where the address belongs now: `url` is what a write sends back, and
    `_meta` is by definition what a write ignores.
    """
    return labelled(
        {
            **dataset_link_payload(graph, node, direction),
            READ_ONLY_CONTAINER: {
                "uid": dataset_link_uid(graph, node),
                "iri": str(node),
                "type": str(direction.node_class),
                "target_iri": stored_iri(graph, node),
                "bundle": uid,
                "scenario": sid,
            },
        },
        NO_PICKED_TERMS,
        expand,
    )


def represent_bundle(
    uid: str,
    graph: Graph,
    version: BundleVersion,
    expand: frozenset = frozenset(),
) -> dict:
    """A read returns exactly what a write accepts, plus read-only data.

    **Sub-resources are nested here and rejected on `PATCH`.** That looks
    inconsistent until you notice which write each is for: a read sent back to
    `POST` or to `replace` copies the whole bundle -- scenarios, study reports
    and the dataset links each scenario cites -- while a `PATCH` is partial by
    nature and nobody sends a whole read to one. Nesting on read is what lets a
    client send back what it read without stripping anything, and `replace`
    is the endpoint that turns that property into a requirement: what its
    payload does not mention, it removes.
    """
    body = labelled(
        {
            **bundle_payload(graph, uid),
            READ_ONLY_CONTAINER: {
                "uid": uid,
                "iri": str(bundle_iri(uid)),
                "version": version.number,
            },
        },
        BUNDLE_FIELDS,
        expand,
    )
    for part in BUNDLE_PARTS:
        body[part.payload_key] = nested_part_bodies(graph, uid, part, expand)
    return body


def note_history_gap(body: dict, recorded: bool) -> dict:
    """Say so when the history was lost, and say nothing when it was not.

    The key appears only when it is ``False``. A client should not have to
    check something on every response to learn that the ordinary thing
    happened; it is there to name the exception.
    """
    if not recorded:
        body[READ_ONLY_CONTAINER]["history_recorded"] = False
    return body


def bundle_response(
    uid: str,
    graph: Graph,
    version: BundleVersion,
    history_recorded: bool = True,
    expand: frozenset = frozenset(),
    meta: dict = None,
) -> Response:
    """The body, plus the entity tag every read has to carry.

    ``meta`` is what this particular answer knows and a read does not -- the
    replace endpoint's account of what it removed. It goes in `_meta` rather
    than beside the fields, because the top level of a bundle body is exactly
    what a write accepts and nothing else.
    """
    body = note_history_gap(
        represent_bundle(uid, graph, version, expand), history_recorded
    )
    body[READ_ONLY_CONTAINER].update(meta or {})
    response = Response(body)
    response["ETag"] = version.etag
    return response
