"""Every name the platform serves under `/ontology/`, and what kind it is.

Until this module existed, nothing under `/ontology/` validated the name. The
only source of truth was the filesystem -- `ontologies/oeo` and
`ontologies/oeo_ext` -- and each route consulted it differently, so an unknown
name got three different answers and none of them was a 404: the React shell
rendered a term page for nothing, the search page searched nothing, and
`OntologyStaticsView` raised `FileNotFoundError` out of `os.listdir`.

A filesystem cannot be that source of truth anyway, because **not everything
served here is a directory**. The OEKG lives in Fuseki. That is the whole
reason this is a registry rather than three sprinkled `404`s.

**The kind is not decoration -- it decides who resolves the address.** A
file-backed name is served from `ONTOLOGY_ROOT` by `OntologyStaticsView` and
the React views; a store-backed name is resolved against the graph store by its
own routes, registered ahead of the ontology catch-all in `ontology/urls.py`.
A kind with nothing behind it is the dangerous state, which is why the tests
fail on one: a vocabulary that silently resolved to nothing would read exactly
like data that had been deleted.

**Why a knowledge graph sits under `/ontology/` at all.** It is arguably wrong:
the OEKG is a store of scenario data, not a vocabulary, and nothing about it is
an ontology. It is here because its IRIs were minted here and cannot move --
`https://openenergyplatform.org/ontology/oekg/<uuid>` is the subject of nearly
every triple of every bundle and is embedded in the JSON-LD diffs in
`OEKG_Modifications`, so re-minting would break every external citation in
order to fix a routing bug. **A new knowledge graph should not copy this
prefix.** The decision is recorded here so it is inherited deliberately rather
than by imitation.

This module holds data and imports nothing, the same bargain `api/api_tags.py`
strikes. It is read from `ontology/urls.py` at URLConf-import time and from
`oekg/`, where the standing rule is that nothing on a request path may reach
`factsheet/oekg/connection.py` -- which parses the full ontology at import. A
registry that imported Django, or looked at the disk, would make that rule a
matter of luck.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass
from typing import Optional

#: Served as files from ``ONTOLOGY_ROOT``: releases, imports, a glossary, and
#: the React pages that read them.
ONTOLOGY = "ontology"

#: Served from the graph store. Has no directory, no releases and no glossary;
#: its addresses are resolved by querying the graph.
KNOWLEDGE_GRAPH = "knowledge-graph"

#: Every kind something knows how to resolve. A name carrying anything else is
#: a name nothing serves, and the tests say so.
KINDS = frozenset({ONTOLOGY, KNOWLEDGE_GRAPH})


@dataclass(frozen=True)
class Vocabulary:
    """One name under `/ontology/`, and what the platform does with it."""

    name: str
    kind: str
    title: str
    description: str


VOCABULARIES = (
    Vocabulary(
        name="oeo",
        kind=ONTOLOGY,
        title="Open Energy Ontology",
        description=(
            "The platform's domain ontology. Its terms are the picks every "
            "scenario bundle and every table's metadata select from."
        ),
    ),
    Vocabulary(
        name="oeo_ext",
        kind=ONTOLOGY,
        title="Open Energy Ontology, extended",
        description=(
            "Terms held beside the ontology proper, served from the same "
            "release layout."
        ),
    ),
    Vocabulary(
        name="oekg",
        kind=KNOWLEDGE_GRAPH,
        title="Open Energy Knowledge Graph",
        description=(
            "The scenario bundles, in Fuseki rather than on disk. An address "
            "here names a bundle or one of its scenarios and dereferences to "
            "the page or the API representation of it; see oekg/iri_views.py "
            "for what resolves and what deliberately does not."
        ),
    ),
)

_BY_NAME = {vocabulary.name: vocabulary for vocabulary in VOCABULARIES}


def kind_of(name: Optional[str]) -> Optional[str]:
    """What kind of thing ``name`` is, or ``None`` if we do not serve it.

    ``None`` in, ``None`` out: the oeo-initializer route makes the name
    optional, so a missing one reaches this lookup and has to be an answer
    rather than a ``TypeError``.
    """
    vocabulary = _BY_NAME.get(name)
    return vocabulary.kind if vocabulary else None


def is_file_backed(name: Optional[str]) -> bool:
    """Whether ``name`` is served from ``ONTOLOGY_ROOT``.

    The question the file-backed views ask, and the only one they should: it is
    false both for a name nobody serves and for one served from a store, and
    those two failures look identical from inside a view that lists a
    directory.

    It says nothing about whether the files are actually there. A registered
    name whose directory is missing is a deployment fault, and the view checks
    for it separately.
    """
    return kind_of(name) == ONTOLOGY


def names_of_kind(kind: str) -> list:
    """The registered names of one kind, in registration order."""
    return [vocabulary.name for vocabulary in VOCABULARIES if vocabulary.kind == kind]
