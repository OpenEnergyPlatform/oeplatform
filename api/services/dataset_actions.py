"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The Dataset action service (spec #2613): one path every action on a Dataset
takes, whoever calls it, with the table action service's contract
(``api.services.table_actions``) and its vocabulary
(``api.services.batch_actions``). Two operations:

- ``preflight(user, action, names, params)``: what would run, what is left
  out and why, and the consequences worth stating before a confirmation. It
  writes nothing.
- ``execute(user, action, names, params, via=...)``: checks again under a
  row lock and refuses the whole request if anything named is no longer
  allowed (``ActionRefused``, nothing written); otherwise writes everything
  in one transaction and logs once it has committed.

A row action is a batch of one: both operations take a list of names.

The actions:

- ``create``: the one name is the new Dataset's; ``title``, ``description``,
  an optional ``at_id`` and optional ``topics`` are parameters. It goes
  through the shared create path (``create_dataset``), so a new Dataset is a
  draft whose ``modified_at`` is its ``created_at``. A taken name is an
  ``InvalidParameters`` on ``name``.
- ``edit``: ``title``, ``description``, ``at_id`` and ``topics`` of one of
  the user's own Datasets, each only if given: a parameter left out is left
  as it is, and an empty ``at_id`` keeps the stored one (the API refuses an
  empty one before it gets here; a form may send one). **An edit that
  changes nothing writes, stamps and logs nothing.**
- ``publish``: ``DATASET_GATE`` runs live, under the lock; a Dataset failing
  it is left out by the failed check's reason (``ActionRefused.failed_checks``
  names the checks) and refuses the request. ``published_at`` becomes now. A
  Dataset already published is passed over (``ALREADY_PUBLISHED``) unless
  ``params["republish"]`` is set, which only the API sets (the dashboard
  offers no republish): then it passes the gate again and the date is
  overwritten. The preflight states the member mix (members, drafts,
  embargoed) for the dialog; it never refuses anything.
- ``unpublish``: always allowed for the creator; ``published_at`` is
  cleared. A draft is passed over (``ALREADY_DRAFT``), so unpublishing one
  succeeds and writes nothing.
- ``delete``: the named Datasets go; their member Tables never do, and there
  is no OEDB work. The typed confirmation (``Preflight.confirmation``) is
  enforced here, under the lock: the name for one published Dataset, the
  count for a batch holding a published Dataset or more than
  ``TYPED_COUNT_ABOVE``; a draft alone needs none.
- ``members_add`` and ``members_remove``: the Dataset is the subject (the
  ``dataset`` parameter, one of the user's own), the names are Tables. Adding
  takes any Table in ``assignable_tables(user)``, the curation rule, with no
  Table role gate, and writes through ``assign_table``; removing takes any
  member, whoever holds it, and leaves the Dataset's Topics as they are.
  Names the request cannot change (already a member, not a member, no such
  Table) are left out and passed over: the request's outcome already holds
  for them, so a repeated call is safe. A Table no longer assignable when the
  lock is held refuses the whole request.

Publish, unpublish, edit and delete resolve their Datasets alike: one the
user may not read (another user's draft, or no such name) is "No such
dataset", one they may read but did not create "Not one of your datasets";
either refuses the request. Edit names one Dataset and says so as an
``ActionError`` instead (``DatasetNotFound``, ``NotYourDataset``), as the
member actions do for their subject.

**The service owns Topic validation** (``topics``, on create and edit): an
unknown name and the draft pseudo-topic are an ``InvalidParameters`` naming
them, never silently dropped.

``modified_at`` is stamped here, and only on a real change (a Modification):
an edit that changed something, Tables actually added or removed. A create's
stamp is its creation time; publishing, unpublishing and deleting stamp
nothing.

Log lines, on the ``oeplatform.dataset_actions`` logger, written once the
transaction has committed and never for a refused request nor for one that
wrote nothing::

    dataset_action dataset=<name> action=create by=<user pk>
        via=<entry point> batch=-
    dataset_action dataset=<name> action=edit changed=<field>,<field> by=…
    dataset_action dataset=<name> action=publish republish=yes|no by=…
    dataset_action dataset=<name> action=unpublish by=…
    dataset_action dataset=<name> action=delete published=yes|no members=<n>
        by=…
    dataset_action dataset=<name> action=members_add|members_remove
        table=<name> by=…

One line per Dataset created, edited, published, unpublished or deleted,
one per Table added or removed. ``batch`` ties together the lines of one
request writing more than one, and is ``-`` for a single line. No audit
model: these lines are the record.
"""  # noqa: 501

import logging
import uuid
from dataclasses import dataclass, field
from typing import ClassVar

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import Http404
from django.utils import timezone

from api.services import batch_actions
from api.services.batch_actions import (  # noqa: F401 (part of this module's interface)
    TYPED_COUNT_ABOVE,
    ActionError,
    InvalidParameters,
    LeftOut,
    confirm_error,
    quoted,
    unique,
)
from api.services.dataset_creation import (
    DatasetNameTaken,
    assign_table,
    assignable_tables,
    create_dataset,
    dataset_title,
    name_taken_message,
    set_dataset_topics,
    update_dataset,
)
from dataedit.models import DATASET_NOT_FOUND, Dataset, Table, Topic
from dataedit.publish_gate import DATASET_GATE, publish_checks
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

logger = logging.getLogger("oeplatform.dataset_actions")

CREATE, EDIT = "create", "edit"
PUBLISH, UNPUBLISH = "publish", "unpublish"
DELETE = "delete"
MEMBERS_ADD, MEMBERS_REMOVE = "members_add", "members_remove"
ACTIONS = (CREATE, EDIT, PUBLISH, UNPUBLISH, DELETE, MEMBERS_ADD, MEMBERS_REMOVE)
MEMBER_ACTIONS = (MEMBERS_ADD, MEMBERS_REMOVE)
# What an edit may change, in the order a log line names the changes.
EDITABLE = ("title", "description", "at_id", "topics")

# The most names one request may carry, per action; over it the request is
# refused before anything is read.
#
# Adding and removing members: 2,500 Tables each, the tables tab's measured
# number for the same writes from the other side (``table_actions.CEILINGS``
# for dataset_add / dataset_remove: worst 6.8 ms per Table, about 17 s for
# 2,500 against the host's 300 s). Both write through the same
# ``assign_table`` and membership rows, and this side reads less: no Table
# role, only the curation rule, once per request.
#
# Publish, unpublish and delete have none yet: their shared ceiling is
# measured when the bulk bar arrives (#2626). Until then every caller names
# one Dataset per request. Create and edit take exactly one name.
CEILINGS = {
    MEMBERS_ADD: 2500,
    MEMBERS_REMOVE: 2500,
}

# What an action is called at the start of a sentence, as in the ceiling's
# "Adding tables to a dataset takes at most 2,500 tables at a time".
ACTION_NAMES = {
    CREATE: "Create",
    EDIT: "Edit",
    PUBLISH: "Publish",
    UNPUBLISH: "Unpublish",
    DELETE: "Delete",
    MEMBERS_ADD: "Adding tables to a dataset",
    MEMBERS_REMOVE: "Removing tables from a dataset",
}

# Left-out reasons. A Dataset the user may not read and a name that never
# existed are told apart by nothing, as every reader tells them apart by
# nothing (``DATASET_NOT_FOUND``).
NOT_FOUND = "No such dataset"
NOT_YOURS = "Not one of your datasets"
NO_SUCH_TABLE = "No such table"
ALREADY_IN = "Already in the dataset"
NOT_IN = "Not in the dataset"
ALREADY_DRAFT = "Already a draft"
ALREADY_PUBLISHED = "Already published"
# The curation rule (``assignable_tables``) refusing a Table: a draft or
# embargoed Table the user holds no Data editor grant on.
MAY_NOT_ASSIGN = "Drafts and embargoed tables need Data editor on the table"

# A Dataset failing ``DATASET_GATE`` is left out by the failed check's own
# reason (the ``error`` its ``run`` answers: "No member tables", "No
# topics"), which refuses a publish.

# Left-out reasons ``execute`` passes over instead of refusing the request:
# there is nothing to do for those names, because the outcome asked for holds
# already (a member added, a non-member removed, a draft unpublished) or
# there is no such Table. Every other reason refuses the whole request.
PASSED_OVER = frozenset(
    {ALREADY_IN, NOT_IN, NO_SUCH_TABLE, ALREADY_DRAFT, ALREADY_PUBLISHED}
)


class DatasetNotFound(ActionError):
    """The Dataset a request is about is not one the user may read: another
    user's draft, or no such name. Said in the same words as every reader
    says it (``DATASET_NOT_FOUND``)."""

    def __init__(self):
        super().__init__(DATASET_NOT_FOUND)


class NotYourDataset(ActionError):
    """The Dataset a request is about is one the user may read but did not
    create. Only its creator may change it."""

    def __init__(self):
        super().__init__("Only the dataset's creator may change it.")


class ActionRefused(batch_actions.ActionRefused):
    """Something named is no longer allowed, so nothing was written
    (``batch_actions.ActionRefused``). ``for_role`` says a Dataset was
    another user's; ``not_found`` that one was not there to be read."""

    role_refusals = frozenset({NOT_YOURS})

    @property
    def not_found(self) -> bool:
        return any(group.reason == NOT_FOUND for group in self.refused)

    @property
    def failed_checks(self) -> list:
        """The ``DATASET_GATE`` checks a refused publish failed, by name, in
        the gate's order: what the API's 409 lists. Empty for any other
        refusal."""
        failed = {
            name
            for names in self.preflight.consequences.get("gate", {}).values()
            for name in names
        }
        return [check.name for check in DATASET_GATE if check.name in failed]


@dataclass
class Preflight(batch_actions.Preflight):
    """What ``execute`` would do with these names, before it does it
    (``batch_actions.Preflight``). The names are Datasets, except for the
    member actions, where they are Tables and the subject is ``dataset``.
    A create has nothing to act on yet, so its ``eligible`` is empty."""

    action_names: ClassVar[dict] = ACTION_NAMES

    # The member actions only: the Dataset whose members change.
    dataset: Dataset = None

    @property
    def item(self) -> str:
        return _nouns(self.action)[0]

    @property
    def items(self) -> str:
        return _nouns(self.action)[1]


@dataclass(frozen=True)
class Outcome:
    """What ``execute`` did. ``datasets`` are the Datasets acted on (after a
    delete, as they were; for an edit, the one Dataset whether or not
    anything changed); ``left_out`` the names passed over, by reason; for the
    member actions, ``tables`` are the Tables added or removed, and for an
    edit ``changed`` the fields that changed."""

    action: str
    datasets: list
    tables: list = field(default_factory=list)
    left_out: list = field(default_factory=list)
    changed: list = field(default_factory=list)


def _nouns(action) -> tuple:
    if action in MEMBER_ACTIONS:
        return "table", "tables"
    return "dataset", "datasets"


def _created_by(dataset, user) -> bool:
    """Whether ``user`` created ``dataset``: the one who may change it. An
    ownerless Dataset is nobody's."""
    return dataset.creator_id is not None and dataset.creator_id == user.pk


def own_dataset(user, name) -> Dataset:
    """The Dataset called ``name``, which ``user`` created. Resolved through
    the read rule first (``Dataset.objects.readable_or_404``), so a write
    never tells more than a read: a Dataset the user may not read is
    ``DatasetNotFound``, one they may read but did not create
    ``NotYourDataset``."""
    try:
        dataset = Dataset.objects.readable_or_404(user, name)
    except Http404 as error:
        raise DatasetNotFound() from error
    if not _created_by(dataset, user):
        raise NotYourDataset()
    return dataset


def _over_ceiling(action, names) -> bool:
    ceiling = CEILINGS.get(action)
    return ceiling is not None and len(names) > ceiling


def _ceiling_message(action, total) -> str:
    return batch_actions.ceiling_message(
        ACTION_NAMES[action], CEILINGS[action], total, _nouns(action)[1]
    )


def _resolve(user, names, annotations=None):
    """The Datasets ``names`` names, by the user's rights over them: those
    the user may read (``found``, by name), the user's own among them
    (``eligible``, in the order named) and the rest by left-out reason
    (``NOT_FOUND`` or ``NOT_YOURS``). One query, with ``annotations`` on
    each Dataset found."""
    datasets = Dataset.objects.visible_to(user).filter(name__in=names)
    if annotations:
        datasets = datasets.annotate(**annotations)
    found = {dataset.name: dataset for dataset in datasets}
    eligible, reasons = [], {}
    for name in names:
        dataset = found.get(name)
        if dataset is None:
            reason = NOT_FOUND
        elif not _created_by(dataset, user):
            reason = NOT_YOURS
        else:
            eligible.append(dataset)
            continue
        reasons.setdefault(reason, []).append(name)
    return found, eligible, reasons


def _subject(action, names, eligible, found) -> str:
    """What the dialog is about: the one Dataset's title (its name when the
    user may not read it), or the batch counted (``batch_subject``)."""
    if len(names) == 1:
        dataset = found.get(names[0])
        return quoted([dataset_title(dataset) if dataset else names[0]])
    return batch_actions.batch_subject(len(eligible), len(names), _nouns(action)[1])


def _left_out(reasons) -> list:
    return [LeftOut(reason, group) for reason, group in reasons.items()]


def _delete_preflight(user, names) -> Preflight:
    """Delete: the user's own Datasets among ``names``, the rest left out
    (``NOT_FOUND`` or ``NOT_YOURS``), each eligible one carrying its member
    count as ``members``. One query."""
    found, eligible, reasons = _resolve(user, names, {"members": Count("tables")})
    published = [dataset for dataset in eligible if dataset.is_published]
    return Preflight(
        action=DELETE,
        total=len(names),
        eligible=eligible,
        left_out=_left_out(reasons),
        consequences={
            "published": published,
            "members": sum(dataset.members for dataset in eligible),
        },
        subject=_subject(DELETE, names, eligible, found),
        confirmation=batch_actions.typed_confirmation(
            eligible, lambda dataset: dataset.is_published
        ),
        requested=names,
    )


def _member_mix(datasets) -> dict:
    """How many distinct Tables ``datasets`` hold, and how many of them are
    drafts or under an active embargo: what a publish dialog states and
    never refuses on. One query, none for no Datasets."""
    if not datasets:
        return {"members": 0, "drafts": 0, "embargoed": 0}
    return Table.objects.filter(
        datasets__in=[dataset.pk for dataset in datasets]
    ).aggregate(
        members=Count("pk", distinct=True),
        drafts=Count("pk", filter=Q(is_publish=False), distinct=True),
        embargoed=Count(
            "pk", filter=Q(embargos__date_ended__gt=timezone.now()), distinct=True
        ),
    )


def _publish_preflight(user, names, republish=False) -> Preflight:
    """Publish: the user's own Datasets among ``names`` that pass
    ``DATASET_GATE`` now; the rest left out (``NOT_FOUND``, ``NOT_YOURS``, or
    a failed check's reason). A published one is passed over
    (``ALREADY_PUBLISHED``) unless ``republish``, and then judged by the gate
    like a draft. ``consequences`` carry ``gate``, the failed check names by
    Dataset, ``republished``, the eligible Datasets already published, and
    the member mix of the eligible ones (``_member_mix``). One query for the
    Datasets, two per own Dataset judged by the gate, one for the mix."""
    found, own, reasons = _resolve(user, names)
    eligible, gate = [], {}
    for dataset in own:
        if dataset.is_published and not republish:
            reasons.setdefault(ALREADY_PUBLISHED, []).append(dataset.name)
            continue
        failed = [
            check for check in publish_checks(dataset, DATASET_GATE) if not check.passed
        ]
        if not failed:
            eligible.append(dataset)
            continue
        gate[dataset.name] = [check.name for check in failed]
        for check in failed:
            reasons.setdefault(check.reason, []).append(dataset.name)
    return Preflight(
        action=PUBLISH,
        total=len(names),
        eligible=eligible,
        left_out=_left_out(reasons),
        consequences={
            "gate": gate,
            "republished": [dataset for dataset in eligible if dataset.is_published],
            **_member_mix(eligible),
        },
        subject=_subject(PUBLISH, names, eligible, found),
        requested=names,
    )


def _unpublish_preflight(user, names) -> Preflight:
    """Unpublish: the user's own published Datasets among ``names``; their
    drafts are passed over (``ALREADY_DRAFT``), the rest left out
    (``NOT_FOUND`` or ``NOT_YOURS``). One query."""
    found, own, reasons = _resolve(user, names)
    eligible = [dataset for dataset in own if dataset.is_published]
    for dataset in own:
        if not dataset.is_published:
            reasons.setdefault(ALREADY_DRAFT, []).append(dataset.name)
    return Preflight(
        action=UNPUBLISH,
        total=len(names),
        eligible=eligible,
        left_out=_left_out(reasons),
        subject=_subject(UNPUBLISH, names, eligible, found),
        requested=names,
    )


def validated_topics(names) -> list:
    """The Topics ``names`` names, for a Dataset's own set, in the order
    named. A name no Topic has, and the draft pseudo-topic (which marks a
    draft Table and is never a Dataset's), are an ``InvalidParameters`` on
    ``topics`` naming them: refused, never silently dropped. One query."""
    names = unique(str(name).strip() for name in names)
    found = {topic.name: topic for topic in Topic.objects.filter(name__in=names)}
    draft = [name for name in names if name == PSEUDO_TOPIC_DRAFT]
    unknown = [name for name in names if name not in found and name not in draft]
    problems = []
    if unknown:
        problems.append(f"No such topic: {quoted(unknown)}.")
    if draft:
        problems.append(
            f"{quoted(draft)} marks draft tables and is never a dataset's topic."
        )
    if problems:
        raise InvalidParameters({"topics": " ".join(problems)})
    return [found[name] for name in names]


def _one_name(names) -> str:
    if len(names) != 1:
        raise InvalidParameters({"datasets": "Name exactly one dataset."})
    return names[0]


def _create_preflight(user, names, params) -> Preflight:
    """Create: whether the one name in ``names`` is free and the parameters
    are usable. A taken name, a missing title or description and an unusable
    Topic are each an ``InvalidParameters``. The validated Topics ride in
    ``consequences["topics"]``. Two queries."""
    name = _one_name(names)
    missing = {
        key: "This field is required."
        for key in ("title", "description")
        if not (params.get(key) or "").strip()
    }
    if missing:
        raise InvalidParameters(missing)
    if Dataset.objects.filter(name=name).exists():
        raise InvalidParameters({"name": name_taken_message(name)})
    topics = validated_topics(params.get("topics") or [])
    return Preflight(
        action=CREATE,
        total=1,
        eligible=[],
        left_out=[],
        consequences={"topics": topics},
        subject=quoted([params["title"]]),
        requested=names,
    )


def _as_edited(dataset) -> dict:
    """The editable fields of ``dataset`` as an edit compares them."""
    metadata = dataset.metadata or {}
    return {
        "title": metadata.get("title"),
        "description": metadata.get("description"),
        "at_id": metadata.get("@id"),
        "topics": sorted(dataset.topics.values_list("name", flat=True)),
    }


def _edit_preflight(user, names, params) -> Preflight:
    """Edit: which of the given fields would change on the one Dataset
    ``names`` names, one of the user's own (``own_dataset``). Only keys
    present in ``params`` count, and an empty ``at_id`` keeps the stored one,
    so a parameter left out is a field left alone. ``consequences`` carry
    ``changes`` (in ``EDITABLE`` order; empty for a no-op) and the validated
    ``topics`` (None when not given). Two queries, three with Topics."""
    dataset = own_dataset(user, _one_name(names))
    wanted = {key: params[key] for key in ("title", "description") if key in params}
    if params.get("at_id"):
        wanted["at_id"] = params["at_id"]
    topics = None
    if "topics" in params:
        topics = validated_topics(params["topics"] or [])
        wanted["topics"] = sorted(topic.name for topic in topics)
    current = _as_edited(dataset)
    changes = [key for key in EDITABLE if key in wanted and wanted[key] != current[key]]
    return Preflight(
        action=EDIT,
        total=1,
        eligible=[dataset],
        left_out=[],
        consequences={"changes": changes, "topics": topics},
        subject=quoted([dataset_title(dataset)]),
        requested=names,
    )


def _members_preflight(user, action, names, dataset) -> Preflight:
    """The member actions on ``dataset``: which of the Tables ``names`` the
    action changes, the rest left out by reason. Three queries for an add
    (the Tables, the members among them, the assignable among them), one for
    a removal (the members among them)."""
    if action == MEMBERS_REMOVE:
        found = {table.name: table for table in dataset.tables.filter(name__in=names)}
        members = set(found)
    else:
        found = {table.name: table for table in Table.objects.filter(name__in=names)}
        ids = [table.pk for table in found.values()]
        members = set(dataset.tables.filter(pk__in=ids).values_list("name", flat=True))
        assignable = set(
            assignable_tables(user).filter(pk__in=ids).values_list("name", flat=True)
        )
    eligible, reasons = [], {}
    for name in names:
        if action == MEMBERS_REMOVE:
            reason = "" if name in members else NOT_IN
        elif name not in found:
            reason = NO_SUCH_TABLE
        elif name in members:
            reason = ALREADY_IN
        elif name not in assignable:
            reason = MAY_NOT_ASSIGN
        else:
            reason = ""
        if reason:
            reasons.setdefault(reason, []).append(name)
        else:
            eligible.append(found[name])
    if len(names) == 1:
        table = found.get(names[0])
        subject = quoted([(table and table.human_readable_name) or names[0]])
    else:
        subject = batch_actions.batch_subject(
            len(eligible), len(names), _nouns(action)[1]
        )
    return Preflight(
        action=action,
        total=len(names),
        eligible=eligible,
        left_out=[LeftOut(reason, group) for reason, group in reasons.items()],
        ceiling=CEILINGS[action],
        subject=subject,
        requested=names,
        dataset=dataset,
    )


def choice(action, params) -> str:
    """The choice a dialog makes before it is confirmed, as one string
    (``batch_actions.choice``): none, for every Dataset action. Every
    parameter a Dataset dialog sends is entered, never chosen and re-checked,
    so its preview is never stale. Offered because the dashboard's action
    view asks every action service for it."""
    return batch_actions.choice((), params)


def _dataset_param(params) -> str:
    value = params.get("dataset")
    name = value.name if isinstance(value, Dataset) else (value or "").strip()
    if not name:
        raise InvalidParameters({"dataset": "Name the dataset."})
    return name


def preflight(user, action, names, params=None) -> Preflight:
    """What ``action`` would do with ``names``. Writes nothing.

    For create and edit, ``names`` is the one Dataset (a taken name, or a
    Dataset that is not the user's own, raises: ``InvalidParameters``,
    ``DatasetNotFound``, ``NotYourDataset``), and the fields are
    ``params``. For publish, unpublish and delete, ``names`` are Datasets.
    For the member actions they are Tables, and ``params["dataset"]`` names
    the Dataset (``own_dataset``); more names than ``CEILINGS`` allows are
    counted and nothing is read, not even the Dataset. ``topics``, on create
    and edit, are validated here (``validated_topics``).
    """
    if action not in ACTIONS:
        raise ValueError(f"unknown dataset action: {action}")
    params = params or {}
    names = unique(names)
    if action == CREATE:
        return _create_preflight(user, names, params)
    if action == EDIT:
        return _edit_preflight(user, names, params)
    if action == PUBLISH:
        return _publish_preflight(user, names, bool(params.get("republish")))
    if action == UNPUBLISH:
        return _unpublish_preflight(user, names)
    if action == DELETE:
        return _delete_preflight(user, names)
    if _over_ceiling(action, names):
        return Preflight(
            action=action,
            total=len(names),
            eligible=[],
            left_out=[],
            ceiling=CEILINGS[action],
            subject=batch_actions.batch_subject(
                len(names), len(names), _nouns(action)[1]
            ),
            requested=names,
        )
    dataset = own_dataset(user, _dataset_param(params))
    return _members_preflight(user, action, names, dataset)


def _lock(action, names, params):
    """Hold a row lock until the transaction ends on everything the check
    reads that another request could change, so the check and the write are
    one step: the Datasets the request is about and, for an add, the named
    Tables, whose state the curation rule judges (published, embargoed).

    Tables before the Dataset: the order the table action service takes
    (it locks Tables, then writes the Dataset's ``modified_at``), so the two
    services cannot wait on each other in a circle. Locking a Dataset the
    user turns out not to own costs nothing: the check refuses it next.

    The Dataset's row is what every write to its members and Topics takes
    first (or updates, which locks it too), so holding it keeps the
    publish gate's verdict true until the commit. A create has no row to
    lock: the name's unique constraint decides a race."""
    if action == CREATE:
        return
    if action == MEMBERS_ADD:
        tables = Table.objects.filter(name__in=names).select_for_update()
        list(tables.values_list("pk", flat=True))
    if action in MEMBER_ACTIONS:
        locked = Dataset.objects.filter(name=_dataset_param(params))
    else:
        locked = Dataset.objects.filter(name__in=names)
    list(locked.select_for_update().values_list("pk", flat=True))


def _log(user, action, lines, via):
    """One line per ``(dataset, fields)`` in ``lines``: the Dataset's name
    and what the action adds after ``action=`` (``table=`` for a member
    change, ``published= members=`` for a delete, ``changed=`` for an edit,
    ``republish=`` for a publish; "" for nothing)."""
    batch = uuid.uuid4().hex[:12] if len(lines) > 1 else "-"
    for dataset, fields in lines:
        logger.info(
            "dataset_action dataset=%s action=%s %sby=%s via=%s batch=%s",
            dataset,
            action,
            f"{fields} " if fields else "",
            user.pk,
            via,
            batch,
        )


def _delete(user, check, via) -> Outcome:
    datasets = check.eligible
    lines = [
        (
            dataset.name,
            f"published={'yes' if dataset.is_published else 'no'}"
            f" members={dataset.members}",
        )
        for dataset in datasets
    ]
    Dataset.objects.filter(pk__in=[dataset.pk for dataset in datasets]).delete()
    transaction.on_commit(lambda: _log(user, DELETE, lines, via))
    return Outcome(DELETE, datasets)


def _create(user, name, params, check, via) -> Outcome:
    fields = {
        "name": name,
        "title": params["title"],
        "description": params["description"],
        "at_id": params.get("at_id"),
    }
    # Only the insert can lose a race for the name: a request that passed
    # the check above and committed first. Its unique constraint decides,
    # and is told as a name taken before; any other integrity failure is not
    # the name's and is not dressed up as it.
    try:
        with transaction.atomic():
            dataset = create_dataset(fields, creator=user)
    except (IntegrityError, DatasetNameTaken) as error:
        raise InvalidParameters({"name": name_taken_message(name)}) from error
    topics = check.consequences["topics"]
    if topics:
        # part of the creation, whose stamp is ``created_at``: no second one
        set_dataset_topics(dataset, [topic.name for topic in topics])
    transaction.on_commit(lambda: _log(user, CREATE, [(name, "")], via))
    return Outcome(CREATE, [dataset])


def _edit(user, params, check, via) -> Outcome:
    dataset, changes = check.eligible[0], check.consequences["changes"]
    if not changes:
        return Outcome(EDIT, [dataset])
    if set(changes) - {"topics"}:
        current = _as_edited(dataset)
        update_dataset(
            dataset,
            {
                key: params[key] if key in changes else current[key]
                for key in ("title", "description", "at_id")
            },
        )
    if "topics" in changes:
        topics = check.consequences["topics"]
        set_dataset_topics(dataset, [topic.name for topic in topics])
    Dataset.objects.filter(pk=dataset.pk).stamp_modified()
    lines = [(dataset.name, f"changed={','.join(changes)}")]
    transaction.on_commit(lambda: _log(user, EDIT, lines, via))
    return Outcome(EDIT, [dataset], changed=changes)


def _set_published(user, action, check, via) -> Outcome:
    """Publish (``published_at`` now, overwriting a republished Dataset's)
    or unpublish (cleared) the eligible Datasets. Neither is a Modification,
    so nothing is stamped."""
    datasets = check.eligible
    if datasets:
        published_at = timezone.now() if action == PUBLISH else None
        Dataset.objects.filter(pk__in=[dataset.pk for dataset in datasets]).update(
            published_at=published_at
        )
        lines = [
            (
                dataset.name,
                (
                    f"republish={'yes' if dataset.is_published else 'no'}"
                    if action == PUBLISH
                    else ""
                ),
            )
            for dataset in datasets
        ]
        transaction.on_commit(lambda: _log(user, action, lines, via))
    return Outcome(action, datasets, left_out=check.left_out)


def _change_members(user, action, check, via) -> Outcome:
    dataset, tables = check.dataset, check.eligible
    if action == MEMBERS_ADD:
        for table in tables:
            assign_table(dataset, table)
    elif tables:
        dataset.tables.remove(*tables)
    if tables:
        Dataset.objects.filter(pk=dataset.pk).stamp_modified()
        lines = [(dataset.name, f"table={table.name}") for table in tables]
        transaction.on_commit(lambda: _log(user, action, lines, via))
    return Outcome(action, [dataset], tables=tables, left_out=check.left_out)


def execute(user, action, names, params=None, via="dashboard") -> Outcome:
    """Do ``action`` on everything ``names`` names, or on nothing.

    More names than ``CEILINGS`` allows is refused before anything is read
    (``InvalidParameters`` on ``tables``). Then, inside one transaction
    holding a row lock on the Datasets the request is about, everything is
    checked again (``preflight``): any left-out group that is not passed
    over (``PASSED_OVER``) refuses the whole request
    (``ActionRefused``). A typed confirmation that does not match what the
    check asks for now is an ``InvalidParameters`` on ``confirm``. A failure
    part-way leaves nothing behind, and the log lines are written only once
    the transaction has committed. A create that loses a race for its name
    is an ``InvalidParameters`` on ``name``, as a name taken before it
    (``_create``).
    """
    if action not in ACTIONS:
        raise ValueError(f"unknown dataset action: {action}")
    params = params or {}
    names = unique(names)
    if _over_ceiling(action, names):
        raise InvalidParameters(
            {_nouns(action)[1]: _ceiling_message(action, len(names))}
        )
    if not names:
        raise InvalidParameters(
            {_nouns(action)[1]: f"Name at least one {_nouns(action)[0]}."}
        )
    confirm = (params.get("confirm") or "").strip()
    with transaction.atomic():
        _lock(action, names, params)
        check = preflight(user, action, names, params)
        refused = [group for group in check.left_out if group.reason not in PASSED_OVER]
        if refused:
            raise ActionRefused(check, refused)
        if check.confirmation and confirm != check.confirmation:
            raise InvalidParameters({"confirm": confirm_error(check)})
        if action == CREATE:
            return _create(user, names[0], params, check, via)
        if action == EDIT:
            return _edit(user, params, check, via)
        if action in (PUBLISH, UNPUBLISH):
            return _set_published(user, action, check, via)
        if action == DELETE:
            return _delete(user, check, via)
        return _change_members(user, action, check, via)
