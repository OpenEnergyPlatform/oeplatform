"""What a write leaves behind, and how it reads back.

Two rules, and the second is the one that is easy to get wrong.

**Every write records.** Not "every write that destroys information" -- the
judgement call is what makes an audit trail patchy, and "no entry" would then
be ambiguous between *created* and *never touched*. So the rule is flat: the
history is the log of writes.

**The graph commits first, and a failed history write does not fail the
request.** The two stores cannot share a transaction. The data is the truth and
the history is the note about it, so answering `500` for a write that succeeded
would provoke exactly the retry that creates duplicates. The price is a
possible gap in the audit trail, and it is **named rather than hidden** -- in
the response, and in one structured log line -- because a phantom entry would
be worse: it looks like truth.

What is stored is the changed triples, **losslessly and untranslated**. No
field names, no serializer vocabulary, nothing that a later shape change could
re-interpret. Field names are computed here at read time instead, from the same
field table that builds the triples, so a rendering can never drift from what
was stored -- it is derived from it on every read.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
import logging
from typing import Optional

from django.db import transaction
from rdflib import RDF, Graph, URIRef

from factsheet.models import EMPTY_LEGACY_PAYLOAD, OEKG_Modifications
from oekg.bundles import (
    BUNDLE_CLASS,
    FIELDS_BY_CLASS,
    PART_BY_CLASS,
    bundle_iri,
    part_iri,
)
from oekg.fields import PART

logger = logging.getLogger("oeplatform.oekg_history")

CREATE = "POST"
UPDATE = "PATCH"
# A partial delete records its triples; a whole-bundle delete deliberately
# records none -- see `record_bundle_deletion`. Both are this verb: what differs
# is what the row holds, not what happened.
DELETE = "DELETE"
VERBS = (CREATE, UPDATE, DELETE)


def record_write(
    *,
    bundle_uid: str,
    verb: str,
    actor,
    version_before: int,
    version_after: int,
    removed: Optional[Graph] = None,
    added: Optional[Graph] = None,
    resource_type=BUNDLE_CLASS,
    resource_uuid: Optional[str] = None,
) -> bool:
    """Record one write. Returns whether it was recorded.

    **Never raises**, and that is load-bearing rather than polite: the caller's
    graph write has already committed, so there is nothing left to undo and
    nothing useful to tell the client beyond the fact that this note was lost.
    Anything raised from here would become a 500 for a write that succeeded --
    the one outcome the whole ordering exists to avoid -- so the net is cast
    around every failure and not only around the database's.
    """
    if verb not in VERBS:
        # Not a runtime guard against clients -- they cannot reach this. It
        # catches a caller inventing a verb the readers will not understand.
        raise ValueError(f"{verb!r} is not one of {', '.join(VERBS)}.")
    try:
        # The savepoint keeps a rejected insert from poisoning the surrounding
        # transaction. Without it a real database error would be caught here
        # and then raised again by the next query -- which would produce the
        # same 500 by a slower route.
        with transaction.atomic():
            OEKG_Modifications.objects.create(
                bundle_id=bundle_uid,
                user=actor if getattr(actor, "is_authenticated", False) else None,
                verb=verb,
                resource_type=str(resource_type) if resource_type else None,
                resource_uuid=resource_uuid,
                version_before=version_before,
                version_after=version_after,
                removed=_as_json(removed),
                added=_as_json(added),
                # Not null: the user interface's diff viewer reads these two
                # and would throw on one, taking its whole page down.
                old_state=EMPTY_LEGACY_PAYLOAD,
                new_state=EMPTY_LEGACY_PAYLOAD,
            )
    except Exception:
        # Deliberately every exception, not just the database's: serialising
        # the diff runs in here too, and an rdflib failure would otherwise
        # escape and undo the guarantee this function's contract makes.
        #
        # One structured line, the house format, so the gap is greppable. It is
        # the only place this becomes visible: there is no Django admin on this
        # platform to inspect the table through.
        logger.error(
            "oekg_history bundle=%s verb=%s user=%s version=%s->%s "
            "outcome=not_recorded",
            bundle_uid,
            verb,
            getattr(actor, "name", None) or "-",
            version_before,
            version_after,
            exc_info=True,
        )
        return False
    return True


def record_bundle_deletion(
    *,
    bundle_uid: str,
    acronym: str,
    actor,
    version_before: int,
) -> bool:
    """Record that a bundle was deleted, and prune what it used to hold.

    **One event-only line, and no payload.** Every other write stores the
    triples it changed, because a reader needs to know what the change was. A
    whole-bundle delete stores none, because the triples it removed are the
    whole bundle: a diff would make the ledger a copy of the thing that was
    deleted, and deleting would not delete. So the line records that it
    happened -- who, when, which identifier, which acronym, from which version
    -- and nothing about what was in it.

    **And the same reasoning reaches backwards.** The bundle's earlier entries
    keep their structured columns, so the record of *how it changed* survives,
    but their payloads go: a history that kept them would let anyone rebuild a
    deleted bundle from the account of its own deletion. Legacy rows are pruned
    too, and they are the ones that matter most -- a browser write stored the
    bundle's whole state, not a diff.

    Pruning and the event line are one transaction, because a pruned bundle
    with no line saying why reads as tampering, and a line with the payloads
    still under it has not deleted anything.

    **Never raises**, for the same reason `record_write` does not: the graph
    write has already committed, and there is nothing left to undo.
    """
    try:
        with transaction.atomic():
            entries = OEKG_Modifications.objects.filter(bundle_id=bundle_uid)
            entries.update(
                removed=None,
                added=None,
                old_state=EMPTY_LEGACY_PAYLOAD,
                new_state=EMPTY_LEGACY_PAYLOAD,
            )
            OEKG_Modifications.objects.create(
                bundle_id=bundle_uid,
                user=actor if getattr(actor, "is_authenticated", False) else None,
                verb=DELETE,
                resource_type=str(BUNDLE_CLASS),
                acronym=acronym,
                version_before=version_before,
                # There is no version after: the node counting them went with
                # the bundle. NULL says that; 0 would claim a version.
                version_after=None,
                old_state=EMPTY_LEGACY_PAYLOAD,
                new_state=EMPTY_LEGACY_PAYLOAD,
            )
    except Exception:
        logger.error(
            "oekg_history bundle=%s verb=%s user=%s acronym=%s version=%s->gone "
            "outcome=not_recorded",
            bundle_uid,
            DELETE,
            getattr(actor, "name", None) or "-",
            acronym,
            version_before,
            exc_info=True,
        )
        return False
    return True


def changed_fields(
    uid: str,
    removed: Graph,
    added: Graph,
    resource_type=None,
    resource_uuid: Optional[str] = None,
) -> list:
    """The diff, in the vocabulary a client writes in.

    Computed on every read rather than stored, so it cannot drift from the
    triples it describes and a shape change never re-interprets an old row.

    ``resource_type`` and ``resource_uuid`` are the class and identifier the
    write was about, both of which the entry already records. Together they say
    **which** vocabulary to render in and **which** subject in the diff is the
    thing being described: a change to a study report is named in the study
    report's field names, not in the bundle's, and the two tables share `label`
    while agreeing about almost nothing else. An entry naming no class is read
    as a bundle write, which is what every row written before sub-resources
    existed is.

    A triple this cannot attribute to a field -- the type and label a minted
    contact brings with it, say -- is reported with a ``None`` field rather
    than dropped. Dropping it would make the summary look complete when it is
    not, which is the one thing a history must not do.

    **Every change names its predicate**, attributed or not. Without it an
    unattributed entry would be a list of bare values with nothing saying what
    they were values of, which is only marginally better than dropping them.
    """
    node_class = URIRef(resource_type) if resource_type else BUNDLE_CLASS
    fields = FIELDS_BY_CLASS.get(node_class, ())
    subject_of = _subjects(uid, node_class, resource_uuid)
    changes = {}
    for side, graph in (("removed", removed), ("added", added)):
        for subject, predicate, obj in graph:
            key = (
                _field_name(subject, predicate, obj, graph, subject_of, fields),
                str(predicate),
            )
            entry = changes.setdefault(key, {"removed": [], "added": []})
            entry[side].append(str(obj))
    return [
        {
            "field": name,
            "predicate": predicate,
            "removed": sides["removed"],
            "added": sides["added"],
        }
        for (name, predicate), sides in sorted(
            changes.items(), key=lambda item: (item[0][0] or "", item[0][1])
        )
    ]


def _field_name(subject, predicate, obj, graph, subject_of, fields):
    """Which field of the written resource a triple belongs to, if any.

    Two predicates in the bundle's table are shared between fields --
    frameworks and models both hang off has-part -- so the object's type
    decides. An added part carries its type in the same diff; a removed one
    does not, because a patch unlinks and never deletes, and then the field is
    honestly unknown.
    """
    if not fields or not subject_of(subject, graph):
        return None
    candidates = [field for field in fields if field.predicate == URIRef(predicate)]
    if len(candidates) == 1:
        return candidates[0].name
    for field in candidates:
        if field.kind == PART and (obj, RDF.type, field.node_class) in graph:
            return field.name
    return None


def _subjects(uid: str, node_class, resource_uuid: Optional[str]):
    """A test for whether a triple is the written resource's own.

    It has to be a test and not a guess, because `label` is a field name on the
    bundle, on a scenario and on a study report, while a minted contact, region
    or author carries an `rdfs:label` of its own into the very same diff.
    Attributing one of those would say a report was renamed when an author was
    added.

    So a subject counts only when it is positively identified, by one of three
    exact routes, and never by elimination:

    - the bundle is the bundle's IRI;
    - a part a write **created** carries its own `rdf:type` in the same diff;
    - a part a write **changed** brings no type with it, but the entry records
      which part it was, and this API mints a part's IRI from that identifier.

    What that last route does not reach is a patch of a part the user interface
    wrote, whose IRI this API did not choose. Those render as unattributed,
    which is what the history has always done when it cannot know.
    """
    if node_class == BUNDLE_CLASS:
        return lambda subject, graph: subject == bundle_iri(uid)

    part = PART_BY_CLASS.get(node_class)
    minted = part_iri(part, resource_uuid) if part and resource_uuid else None
    return lambda subject, graph: (
        subject == minted or (subject, RDF.type, node_class) in graph
    )


def _as_json(graph: Optional[Graph]):
    """JSON-LD as structured data, not as a string inside a JSON column."""
    if graph is None or not len(graph):
        return None
    return json.loads(graph.serialize(format="json-ld"))
