"""Resolving picked ontology terms to their labels, on request.

A bundle stores the terms it picks as IRIs, because that is what they are: a
sector is `OEO_00000367`, not the word "energy". A user interface has to show
the word, and holding the ontology to look it up is not something a client
should have to do -- it is 1.3 GB.

So `?expand=labels` answers with both. Three things about how:

- **Opt-in, and in `_meta`.** The default representation is exactly what a
  write accepts, and a resolved label is not writable. Putting the resolution
  in the read-only container keeps the round trip intact: a client sends back
  what it read without stripping anything.
- **From the label subset, never from the ontology.** Validation already needs
  a 192 KB subset of `rdfs:label` for the terms the shape picks from, fetched
  beside the shape. This reads the same artifact -- one mechanism, one fetch,
  and no request path that parses the full ontology.
- **Every term asked about is a key.** A term the subset has no label for maps
  to ``null`` rather than being absent, so a client never has to tell "no label
  for this term" from "labels were not resolved".

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from rdflib import URIRef

from oekg.fields import ENUM
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.shape import labels_by_term

# The one expansion a resource read offers.
LABELS = "labels"


def labelled(body: dict, fields: tuple, expand: frozenset) -> dict:
    """Add this body's resolved labels to its read-only container, if asked.

    Takes the whole set of expansions rather than a flag, so a second one is
    added where it is answered rather than by widening six signatures that
    thread a boolean from the view down to here.

    ``fields`` is the resource's own field table, so what counts as a picked
    term is decided by the same table that writes it -- a field the shape later
    enumerates is resolved without anything here changing. A resource with no
    enumerated fields, a dataset link among them, answers with an empty map
    rather than refusing: "resolve the picked terms" is a sensible thing to ask
    of a resource that picks none.
    """
    if LABELS in expand:
        body[READ_ONLY_CONTAINER][LABELS] = term_labels(picked_terms(body, fields))
    return body


def picked_terms(body: dict, fields: tuple) -> list:
    """Every ontology term this body picks, once each, in a stable order."""
    picked = []
    for field in fields:
        if field.kind != ENUM:
            continue
        for iri in body.get(field.name) or []:
            if iri not in picked:
                picked.append(iri)
    return sorted(picked)


def term_labels(iris: list) -> dict:
    """The label the subset holds for each of these terms, ``None`` if none."""
    if not iris:
        return {}
    subset = labels_by_term()
    return {iri: _label(subset.get(URIRef(iri))) for iri in iris}


def _label(labels):
    """The one label a term has. The artifact holds exactly one per term."""
    return str(labels[0]) if labels else None
