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

from django.db import DatabaseError, transaction
from rdflib import RDF, Graph, URIRef

from factsheet.models import EMPTY_LEGACY_PAYLOAD, OEKG_Modifications
from oekg.bundles import BUNDLE_CLASS, BUNDLE_FIELDS, PART, bundle_iri

logger = logging.getLogger("oeplatform.oekg_history")

CREATE = "POST"
UPDATE = "PATCH"
# Deletes join this list with the slice that implements them, not before: a
# verb named here but never written would say the history records something it
# does not.
VERBS = (CREATE, UPDATE)


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

    Never raises: the caller's graph write has already committed, so there is
    nothing left to undo and nothing useful to tell the client beyond the fact
    that this note was lost.
    """
    if verb not in VERBS:
        # Not a runtime guard against clients -- they cannot reach this. It
        # catches a caller inventing a verb the readers will not understand.
        raise ValueError(f"{verb!r} is not one of {', '.join(VERBS)}.")
    try:
        # The savepoint keeps a rejected insert from poisoning the surrounding
        # transaction. Without it a real database error would be caught here
        # and then raised again by the next query -- turning a write that
        # succeeded into a 500, which is the one outcome this whole ordering
        # exists to avoid.
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
    except DatabaseError:
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


def changed_fields(uid: str, removed: Graph, added: Graph) -> list:
    """The diff, in the vocabulary a client writes in.

    Computed on every read rather than stored, so it cannot drift from the
    triples it describes and a shape change never re-interprets an old row.

    A triple this cannot attribute to a field -- the type and label a minted
    contact brings with it, say -- is reported under a ``None`` field rather
    than dropped. Dropping it would make the summary look complete when it is
    not, which is the one thing a history must not do.
    """
    fields = {}
    for side, graph in (("removed", removed), ("added", added)):
        for subject, predicate, obj in graph:
            name = _field_name(uid, subject, predicate, obj, graph)
            entry = fields.setdefault(name, {"removed": [], "added": []})
            entry[side].append(str(obj))
    return [
        {"field": name, "removed": sides["removed"], "added": sides["added"]}
        for name, sides in sorted(fields.items(), key=lambda item: (item[0] or "",))
    ]


def _field_name(uid, subject, predicate, obj, graph) -> Optional[str]:
    """Which bundle field a triple belongs to, if any.

    Two predicates in the field table are shared between fields -- frameworks
    and models both hang off has-part -- so the object's type decides. An added
    part carries its type in the same diff; a removed one does not, because a
    patch unlinks and never deletes, and then the field is honestly unknown.
    """
    if subject != bundle_iri(uid):
        return None
    candidates = [
        field for field in BUNDLE_FIELDS if field.predicate == URIRef(predicate)
    ]
    if len(candidates) == 1:
        return candidates[0].name
    for field in candidates:
        if field.kind == PART and (obj, RDF.type, field.node_class) in graph:
            return field.name
    return None


def _as_json(graph: Optional[Graph]):
    """JSON-LD as structured data, not as a string inside a JSON column."""
    if graph is None or not len(graph):
        return None
    return json.loads(graph.serialize(format="json-ld"))
