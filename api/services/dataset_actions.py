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

- ``delete``: the named Datasets go; their member Tables never do, and there
  is no OEDB work. A Dataset the user may not read (another user's draft, or
  no such name) is left out as "No such dataset", one they may read but did
  not create as "Not one of your datasets"; either refuses the request. The
  typed confirmation (``Preflight.confirmation``) is enforced here, under the
  lock: the name for one published Dataset, the count for a batch holding a
  published Dataset or more than ``TYPED_COUNT_ABOVE``; a draft alone needs
  none.
- ``members_add`` and ``members_remove``: the Dataset is the subject (the
  ``dataset`` parameter, one of the user's own), the names are Tables. Adding
  takes any Table in ``assignable_tables(user)``, the curation rule, with no
  Table role gate, and writes through ``assign_table``; removing takes any
  member, whoever holds it, and leaves the Dataset's Topics as they are.
  Names the request cannot change (already a member, not a member, no such
  Table) are left out and passed over: the request's outcome already holds
  for them, so a repeated call is safe. A Table no longer assignable when the
  lock is held refuses the whole request.

``modified_at`` is stamped here, and only on a real change: Tables actually
added or removed. Deleting leaves nothing to stamp.

Log lines, on the ``oeplatform.dataset_actions`` logger, written once the
transaction has committed and never for a refused request::

    dataset_action dataset=<name> action=delete by=<user pk> via=<entry point>
        batch=<id>|- published=yes|no members=<n>
    dataset_action dataset=<name> action=members_add|members_remove
        table=<name> by=<user pk> via=<entry point> batch=<id>|-

One line per Dataset deleted, one per Table added or removed. ``batch`` ties
together the lines of one request writing more than one, and is ``-`` for a
single line. No audit model: these lines are the record.
"""  # noqa: 501

import logging
import uuid
from dataclasses import dataclass, field
from typing import ClassVar

from django.db import transaction
from django.db.models import Count
from django.http import Http404

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
from api.services.dataset_creation import assign_table, assignable_tables
from dataedit.models import DATASET_NOT_FOUND, Dataset, Table

logger = logging.getLogger("oeplatform.dataset_actions")

DELETE = "delete"
MEMBERS_ADD, MEMBERS_REMOVE = "members_add", "members_remove"
ACTIONS = (DELETE, MEMBERS_ADD, MEMBERS_REMOVE)
MEMBER_ACTIONS = (MEMBERS_ADD, MEMBERS_REMOVE)

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
# Delete has none yet: the bulk bar's ceiling for publish, unpublish and
# delete is measured when the bulk bar arrives (#2626). Until then the only
# caller is the API, one Dataset per request.
CEILINGS = {
    MEMBERS_ADD: 2500,
    MEMBERS_REMOVE: 2500,
}

# What an action is called at the start of a sentence, as in the ceiling's
# "Adding tables to a dataset takes at most 2,500 tables at a time".
ACTION_NAMES = {
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
# The curation rule (``assignable_tables``) refusing a Table: a draft or
# embargoed Table the user holds no Data editor grant on.
MAY_NOT_ASSIGN = "Drafts and embargoed tables need Data editor on the table"

# Left-out reasons ``execute`` passes over instead of refusing the request:
# there is nothing to do for those names, because the outcome asked for holds
# already (a member added, a non-member removed) or there is no such Table.
# Every other reason refuses the whole request.
PASSED_OVER = frozenset({ALREADY_IN, NOT_IN, NO_SUCH_TABLE})


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


@dataclass
class Preflight(batch_actions.Preflight):
    """What ``execute`` would do with these names, before it does it
    (``batch_actions.Preflight``). The names are Datasets for delete and
    Tables for the member actions, whose subject is ``dataset``."""

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
    delete, as they were); for the member actions, ``tables`` are the Tables
    added or removed and ``left_out`` the names passed over, by reason."""

    action: str
    datasets: list
    tables: list = field(default_factory=list)
    left_out: list = field(default_factory=list)


def _nouns(action) -> tuple:
    if action in MEMBER_ACTIONS:
        return "table", "tables"
    return "dataset", "datasets"


def dataset_title(dataset) -> str:
    """What a Dataset is called where the user reads it."""
    return (dataset.metadata or {}).get("title") or dataset.name


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
    if dataset.creator_id is None or dataset.creator_id != user.pk:
        raise NotYourDataset()
    return dataset


def _over_ceiling(action, names) -> bool:
    ceiling = CEILINGS.get(action)
    return ceiling is not None and len(names) > ceiling


def _ceiling_message(action, total) -> str:
    return batch_actions.ceiling_message(
        ACTION_NAMES[action], CEILINGS[action], total, _nouns(action)[1]
    )


def _delete_preflight(user, names) -> Preflight:
    """Delete: the user's own Datasets among ``names``, the rest left out
    (``NOT_FOUND`` or ``NOT_YOURS``), each eligible one carrying its member
    count as ``members``. One query."""
    found = {
        dataset.name: dataset
        for dataset in Dataset.objects.visible_to(user)
        .filter(name__in=names)
        .annotate(members=Count("tables"))
    }
    eligible, reasons = [], {}
    for name in names:
        dataset = found.get(name)
        if dataset is None:
            reason = NOT_FOUND
        elif dataset.creator_id is None or dataset.creator_id != user.pk:
            reason = NOT_YOURS
        else:
            eligible.append(dataset)
            continue
        reasons.setdefault(reason, []).append(name)
    if len(names) == 1:
        subject = quoted([dataset_title(eligible[0]) if eligible else names[0]])
    else:
        subject = batch_actions.batch_subject(len(eligible), len(names), "datasets")
    published = [dataset for dataset in eligible if dataset.is_published]
    return Preflight(
        action=DELETE,
        total=len(names),
        eligible=eligible,
        left_out=[LeftOut(reason, group) for reason, group in reasons.items()],
        consequences={
            "published": published,
            "members": sum(dataset.members for dataset in eligible),
        },
        subject=subject,
        confirmation=batch_actions.typed_confirmation(
            eligible, lambda dataset: dataset.is_published
        ),
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
        subject = batch_actions.batch_subject(len(eligible), len(names), "tables")
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


def _dataset_param(params) -> str:
    value = params.get("dataset")
    name = value.name if isinstance(value, Dataset) else (value or "").strip()
    if not name:
        raise InvalidParameters({"dataset": "Name the dataset."})
    return name


def preflight(user, action, names, params=None) -> Preflight:
    """What ``action`` would do with ``names``. Writes nothing.

    For delete, ``names`` are Datasets. For the member actions they are
    Tables, and ``params["dataset"]`` names the Dataset (``own_dataset``:
    ``DatasetNotFound`` or ``NotYourDataset`` when it is not the user's);
    more names than ``CEILINGS`` allows are counted and nothing is read, not
    even the Dataset.
    """
    if action not in ACTIONS:
        raise ValueError(f"unknown dataset action: {action}")
    params = params or {}
    names = unique(names)
    if action == DELETE:
        return _delete_preflight(user, names)
    if _over_ceiling(action, names):
        return Preflight(
            action=action,
            total=len(names),
            eligible=[],
            left_out=[],
            ceiling=CEILINGS[action],
            subject=batch_actions.batch_subject(len(names), len(names), "tables"),
            requested=names,
        )
    dataset = own_dataset(user, _dataset_param(params))
    return _members_preflight(user, action, names, dataset)


def _lock(action, names, params):
    """Hold a row lock on every Dataset the request is about until the
    transaction ends, so the check and the write are one step."""
    if action == DELETE:
        locked = Dataset.objects.filter(name__in=names)
    else:
        locked = Dataset.objects.filter(name=_dataset_param(params))
    list(locked.select_for_update().values_list("pk", flat=True))


def _log(user, action, lines, via):
    """One line per ``(dataset, before, after)`` in ``lines``: the fields
    each line carries before ``by=`` and after ``batch=``."""
    batch = uuid.uuid4().hex[:12] if len(lines) > 1 else "-"
    for dataset, before, after in lines:
        logger.info(
            "dataset_action dataset=%s action=%s%s by=%s via=%s batch=%s%s",
            dataset,
            action,
            before,
            user.pk,
            via,
            batch,
            after,
        )


def _delete(user, check, via) -> Outcome:
    datasets = check.eligible
    lines = [
        (
            dataset.name,
            "",
            f" published={'yes' if dataset.is_published else 'no'}"
            f" members={dataset.members}",
        )
        for dataset in datasets
    ]
    Dataset.objects.filter(pk__in=[dataset.pk for dataset in datasets]).delete()
    transaction.on_commit(lambda: _log(user, DELETE, lines, via))
    return Outcome(DELETE, datasets)


def _change_members(user, action, check, via) -> Outcome:
    dataset, tables = check.dataset, check.eligible
    if action == MEMBERS_ADD:
        for table in tables:
            assign_table(dataset, table)
    elif tables:
        dataset.tables.remove(*tables)
    if tables:
        Dataset.objects.filter(pk=dataset.pk).stamp_modified()
        lines = [(dataset.name, f" table={table.name}", "") for table in tables]
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
    the transaction has committed.
    """
    if action not in ACTIONS:
        raise ValueError(f"unknown dataset action: {action}")
    params = params or {}
    names = unique(names)
    if _over_ceiling(action, names):
        raise InvalidParameters({"tables": _ceiling_message(action, len(names))})
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
        if action == DELETE:
            return _delete(user, check, via)
        return _change_members(user, action, check, via)
