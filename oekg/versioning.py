"""A bundle's version: what it is, where it lives, and how a write guards on it.

Two writers on the same field is the failure no amount of shape validation
catches -- a perfectly valid change silently destroying one made a second
earlier -- and a programmatic API makes it likelier than the user interface
does, because scripts retry, run in parallel and do not look at the screen
first.

The version is a **monotonic counter**, not an opaque token, because two other
parts of this API need it to be one: the two-step delete uses it as its
confirmation, and the history uses it as the natural key of "which change
produced this state".

**The triple points at the bundle, not away from it.** The bundle's shape is
``sh:closed`` with only ``rdf:type`` ignored, so ``<bundle> oekg:version 17``
would make every bundle this API writes invalid. ``sh:closed`` constrains a
focus node's *outgoing* properties, so the bundle as an *object* is untouched,
and nothing in the shape targets the version node: it is untyped, and
``oekg:versionOf`` is not one of the predicates whose objects the shape
validates. The guard therefore works without editing the shape -- and the
version triples stay out of a read for free, because a read walks outward from
the bundle and these point inward.

The version node's IRI is **derived** from the bundle's, so a compare-and-set
can address it in the same request that tests it, with no lookup first.

**Why a write token.** SPARQL's ``DELETE/INSERT/WHERE`` guard applies only when
its pattern matches, but the store answers ``200`` and changes nothing when it
does not, so the write itself carries no signal. Reading the version back is
not enough either: two writers guarding on version 17 both intend 18, so
finding 18 afterwards does not tell a loser from a winner. Each write therefore
stamps a token only its own writer could have chosen, and reads that back. It
costs no extra round trip -- the token comes back with the version the write
already has to read -- and it is the difference between reporting a conflict
and reporting a success that did not happen.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import uuid
from dataclasses import dataclass
from typing import Optional

from rdflib import Graph, Literal, URIRef

from oekg.bundles import BUNDLE_CLASS, OEKG, bundle_iri
from oekg.graph_store import GraphStore

VERSION = OEKG.version
VERSION_OF = OEKG.versionOf
WRITE_TOKEN = OEKG.writeToken

# What a bundle written before this API existed reports. The first write
# through the API creates the node and takes it to FIRST_VERSION.
UNVERSIONED = 0
FIRST_VERSION = UNVERSIONED + 1


@dataclass(frozen=True)
class BundleVersion:
    """The version a read saw, and the token the write before it left behind.

    Both come from one query, because a write needs both: the number to guard
    on, and the token to clear so the next read-back stays unambiguous.
    """

    number: int
    token: Optional[str] = None

    @property
    def etag(self) -> str:
        return f'"{self.number}"'


def version_iri(uid: str) -> URIRef:
    """The version node for a bundle -- derived, never looked up."""
    return OEKG[f"version/{uid}"]


def version_triples(uid: str, number: int, token: Optional[str] = None) -> Graph:
    """The version node as triples, at ``number``."""
    triples = Graph()
    node = version_iri(uid)
    triples.add((node, VERSION_OF, bundle_iri(uid)))
    triples.add((node, VERSION, Literal(int(number))))
    if token is not None:
        triples.add((node, WRITE_TOKEN, Literal(token)))
    return triples


def read_version(store: GraphStore, uid: str) -> BundleVersion:
    """The version a bundle is at. ``UNVERSIONED`` if it has no version node."""
    node = version_iri(uid)
    rows = store.select(
        "SELECT ?number ?token WHERE { %s %s ?number "
        "OPTIONAL { %s %s ?token } }"
        % (node.n3(), VERSION.n3(), node.n3(), WRITE_TOKEN.n3())
    )
    if not rows:
        return BundleVersion(UNVERSIONED)
    return BundleVersion(int(rows[0]["number"]), rows[0].get("token"))


def mint_write_token() -> str:
    """A value no competing writer would choose, so a read-back can tell."""
    return str(uuid.uuid4())


def guarded_operation(
    store: GraphStore,
    uid: str,
    version: BundleVersion,
    token: str,
    delete: Optional[Graph] = None,
    insert: Optional[Graph] = None,
    also_require: Optional[str] = None,
) -> str:
    """One update operation that applies ``delete``/``insert`` at ``version``.

    The version bump rides in the same operation as the change, so the two
    cannot come apart: one request is one transaction, and the guard is the
    request's own ``WHERE``.

    ``also_require`` is a further pattern the write must satisfy, for a
    condition the version cannot express. Uniqueness is one: two bundles being
    patched at the same moment each satisfy their own version guard, so an
    acronym they both claim has to be tested in the same request that takes it.
    """
    node = version_iri(uid)
    bundle = bundle_iri(uid)
    # Copies: the version bookkeeping is added here, and a caller's own delta
    # graph should not come back carrying it.
    to_delete = _copy(delete)
    to_insert = _copy(insert)

    if version.number == UNVERSIONED:
        # Bootstrapping a bundle the user interface wrote. The guard is the
        # absence of a version node, so two first writes cannot both see it
        # missing and both apply.
        where = "%s a %s . FILTER NOT EXISTS { ?node %s %s }" % (
            bundle.n3(),
            BUNDLE_CLASS.n3(),
            VERSION_OF.n3(),
            bundle.n3(),
        )
    else:
        where = "%s %s %s ; %s %s ." % (
            node.n3(),
            VERSION_OF.n3(),
            bundle.n3(),
            VERSION.n3(),
            Literal(version.number).n3(),
        )
        to_delete.add((node, VERSION, Literal(version.number)))
        if version.token is not None:
            # Left behind, the previous writer's token would accumulate one
            # triple per write and make the next read-back ambiguous the other
            # way round.
            to_delete.add((node, WRITE_TOKEN, Literal(version.token)))

    if also_require:
        where = f"{where} {also_require}"

    to_insert += version_triples(uid, version.number + 1, token)
    return store.guarded_modification(where, delete=to_delete, insert=to_insert)


def stamped(store: GraphStore, uid: str, token: str) -> bool:
    """Whether the write that stamped ``token`` is the one that applied.

    The signal the guarded update cannot give. ``False`` means the bundle moved
    between the read the validation needed and the write -- or vanished
    entirely -- so nothing of this request was applied.
    """
    return store.ask(
        "ASK { %s %s %s }"
        % (version_iri(uid).n3(), WRITE_TOKEN.n3(), Literal(token).n3())
    )


def _copy(triples: Optional[Graph]) -> Graph:
    copied = Graph()
    if triples is not None:
        copied += triples
    return copied
