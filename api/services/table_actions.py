"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The table action service (spec #2551): one path every action on Tables
takes, whoever calls it. Two operations:

- ``preflight(user, action, names, params)``: what would run, what is left
  out and why, and the consequences worth stating before a confirmation. It
  writes nothing, and the dialog shows it.
- ``execute(user, action, names, params, via=...)``: re-checks every named
  Table and refuses the whole request if any of them is no longer allowed
  (``ActionRefused``, nothing written); otherwise writes all of them in one
  transaction and logs one line per Table once it has committed.

Delete spans two databases that share no transaction. ``execute`` removes
the Django rows of every Table in its one transaction and drops the OEDB
tables after that has committed, one Table at a time. A drop that fails
leaves an OEDB table nothing points at any more: it is logged with
``drop=failed`` and named in the ``Outcome``, never reported as a plain
success. The other order would be worse: a Table whose rows are gone while
its record still lists it.

A row action is a bulk action of one: both operations take a list of names,
and the dashboard sends one name from a row's menu.

The actions so far are ``publish``, ``unpublish`` and ``delete``; the
Dataset assignment joins as its ticket lands (#2563).

The role an action needs is read off ``table_levels``, which states the
platform's permission rule set-based, as ``myuser.get_table_permission_level``
does for one Table: the highest of the user's direct grant and the grants of
their Organizations, and Table admin on every Table for a platform admin or a
member of an admin Organization. It is the same rule the API's permission
decorators read, so the API can move onto this service (#2569) without
changing who may do what.

Log lines, on the ``oeplatform.table_actions`` logger, one per Table::

    table_action table=<name> action=<action> by=<user pk> via=<entry point>
        batch=<id>|- [topic=<topic> embargo=<period>]
        [datasets=<names left>|- published=yes|no drop=ok|failed]

``batch`` ties together the Tables of one request with more than one Table,
and is ``-`` for a single Table. A failed drop is logged at WARNING with its
traceback. No audit model: these lines are the record.
"""  # noqa: 501

import logging
import uuid
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from api.actions import move_publish
from api.error import APIError
from dataedit.models import Dataset, Embargo, PeerReview, Table, Topic
from dataedit.publish_gate import publish_checks
from login.models import GroupPermission, Organization, UserPermission
from login.permissions import ADMIN_PERM, DELETE_PERM, NO_PERM
from login.tables_tab import visible_datasets
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

logger = logging.getLogger("oeplatform.table_actions")

PUBLISH, UNPUBLISH, DELETE = "publish", "unpublish", "delete"
ACTIONS = (PUBLISH, UNPUBLISH, DELETE)

# What an embargo may be when publishing, in the order the dialog offers
# them; the values are the ones ``api.actions.move_publish`` reads.
EMBARGO_PERIODS = (
    ("none", "No embargo"),
    ("6_months", "6 months"),
    ("1_year", "1 year"),
)


@dataclass(frozen=True)
class RoleGate:
    """The Table role an action needs, and what a user below it is told,
    both by the menu (which shows the action disabled with this text) and
    by the preflight (which leaves the Table out for this reason)."""

    level: int
    refusal: str


ROLE_GATES = {
    PUBLISH: RoleGate(ADMIN_PERM, "Only Table admins can publish"),
    UNPUBLISH: RoleGate(ADMIN_PERM, "Only Table admins can unpublish"),
    DELETE: RoleGate(DELETE_PERM, "Only Data maintainers and Table admins can delete"),
}

# The most Tables one request may name, per action; an action not listed has
# no ceiling yet (publish and unpublish get theirs in #2564). The dashboard is
# synchronous by design (no task queue), so a request has to finish inside
# the host's timeout; mass work stays possible through the API, one call per
# Table.
#
# Delete: 50. The host's limit is Apache's ``Timeout 300`` and mod_wsgi's
# ``socket-timeout=300`` on both daemon groups, with no ``request-timeout``
# (read from /data/httpd/conf on production, 2026-10-02; the config is in no
# repository and has drifted before, so read it again rather than trusting
# this line). Deleting one Table, measured locally with
# ``benchmarks/tables_tab/delete_cost.py`` (Postgres 14, three rounds): 17-38
# ms typical from an empty Table to 1M rows (83 MB), the drop being 9-24 ms
# of it; the worst single drop was 1.13 s (10M rows, 0.83 GB; one 1M-row drop
# also took 1.02 s). At a worst case of 1.2 s per Table, 50 Tables take 60 s:
# a safety factor of 5 against the 300 s, which covers production's OEDB
# sitting on another host and its larger buffer pool. Typical: 1-2 s. Not
# covered: a drop waiting for a lock another session holds on that Table.
CEILINGS = {
    DELETE: 50,
}

# A batch of more than this many Tables is confirmed by typing its count.
TYPED_COUNT_ABOVE = 10

# Left-out reasons that do not depend on the role. A gate failure is
# "Fails the Publish gate: <check>" (``_gate_reason``).
NOT_YOURS = "Not one of your tables"
ALREADY_PUBLISHED = "Already published"
NOT_PUBLISHED = "Not published"


class ActionError(Exception):
    """Base of the two ways ``execute`` can decline."""


class InvalidParameters(ActionError):
    """A parameter of the request is unusable; ``errors`` maps each
    parameter to what is wrong with it. Nothing was written."""

    def __init__(self, errors: dict):
        super().__init__("; ".join(errors.values()))
        self.errors = errors


class ActionRefused(ActionError):
    """At least one named Table is no longer allowed, so nothing was
    written. ``refused`` is the left-out groups that caused it, and
    ``preflight`` the check as it stands now."""

    def __init__(self, preflight: "Preflight", refused: list):
        self.preflight = preflight
        self.refused = refused
        super().__init__(self.message)

    @property
    def message(self) -> str:
        parts = [f"{group.reason} ({_quoted(group.names)})" for group in self.refused]
        return "Nothing was changed: " + "; ".join(parts) + "."


@dataclass(frozen=True)
class LeftOut:
    """Tables an action would not touch, all for the same reason. The
    reason is the text the user is shown."""

    reason: str
    names: list


@dataclass
class Preflight:
    """What ``execute`` would do with these names, before it does it.

    ``eligible`` are the Tables it would act on, in the order named;
    ``left_out`` the rest, grouped by reason. ``ceiling`` is the most Tables
    the action takes in one request (``CEILINGS``), None where no limit is
    set; ``over_ceiling`` says the names sent exceed it, and then nothing
    can be confirmed. ``consequences`` holds what the dialog has to state
    for this action, and ``subject`` is what the request is about: the one
    Table's title, or "n tables". ``confirmation`` is what the user has to
    type to confirm, "" for a plain confirmation (``_confirmation``).
    """

    action: str
    total: int
    eligible: list
    left_out: list
    ceiling: int = None
    consequences: dict = field(default_factory=dict)
    subject: str = ""
    confirmation: str = ""

    @property
    def names(self) -> list:
        return [table.name for table in self.eligible]

    @property
    def over_ceiling(self) -> bool:
        return self.ceiling is not None and self.total > self.ceiling

    @property
    def ceiling_message(self) -> str:
        return _ceiling_message(self.action, self.ceiling, self.total)


@dataclass(frozen=True)
class Outcome:
    """What ``execute`` did: the action and the Tables it changed, as they
    are now. After a delete the Tables have no primary key any more, and
    ``drop_failed`` names those whose OEDB table could not be dropped."""

    action: str
    tables: list
    params: dict
    drop_failed: list = field(default_factory=list)


def table_levels(user, tables) -> dict:
    """The user's effective Table role on each of ``tables``, by primary
    key. See the module docstring for the rule. Three queries whatever the
    number of Tables (one for a platform admin)."""
    ids = [table.pk for table in tables]
    if user.is_admin or (
        Organization.objects.filter(is_admin=True, memberships__user=user).exists()
    ):
        return dict.fromkeys(ids, ADMIN_PERM)
    levels = dict.fromkeys(ids, NO_PERM)
    grants = list(
        UserPermission.objects.filter(holder=user, table_id__in=ids).values_list(
            "table_id", "level"
        )
    )
    grants += GroupPermission.objects.filter(
        holder__memberships__user=user, table_id__in=ids
    ).values_list("table_id", "level")
    for table_id, level in grants:
        levels[table_id] = max(levels[table_id], level)
    return levels


def publish_topics():
    """The Topics a Table can be published under: every real Topic. The
    draft pseudo-topic is a status, never a Topic."""
    return Topic.objects.exclude(name=PSEUDO_TOPIC_DRAFT).order_by("name")


def _quoted(names) -> str:
    return ", ".join(f"“{name}”" for name in names)


def _unique(names) -> list:
    return list(dict.fromkeys(name for name in names if name))


def _gate_reason(table) -> str:
    """Why ``table`` fails the Publish gate, or "" when it passes.

    A Table whose stored verdict (``Table.publishable``) is a pass is not
    validated again here, so a batch of publishable Tables costs no validator
    pass; publishing itself validates live (``move_publish``), and a Table
    that fails there refuses the whole request. A stored fail, or no verdict
    yet (before ``recompute_publish_gate`` ran), runs the checks live: that
    names the failed check, and it agrees with the Publishable cell, where
    the live result wins over a stale stored one.
    """
    if table.publishable:
        return ""
    failed = [check.name for check in publish_checks(table) if not check.passed]
    if not failed:
        return ""
    return "Fails the Publish gate: " + ", ".join(failed)


def _ceiling_message(action, ceiling, total) -> str:
    return (
        f"{action.capitalize()} takes at most {ceiling} tables at a time; "
        f"you selected {total}."
    )


def _confirmation(action, eligible) -> str:
    """What the user has to type to confirm ``action`` on ``eligible``, or
    "" for a plain confirmation. Only delete asks: the Table's name for one
    published Table, the number of Tables for a batch holding a published
    Table or more than ``TYPED_COUNT_ABOVE``."""
    if action != DELETE or not eligible:
        return ""
    published = any(table.is_publish for table in eligible)
    if len(eligible) == 1:
        return eligible[0].name if published else ""
    if published or len(eligible) > TYPED_COUNT_ABOVE:
        return str(len(eligible))
    return ""


def _check(user, action, table, level) -> str:
    """Why ``action`` would leave ``table`` out, or "" when it would act."""
    if level < ROLE_GATES[action].level:
        return ROLE_GATES[action].refusal
    if action == PUBLISH:
        if table.is_publish:
            return ALREADY_PUBLISHED
        return _gate_reason(table)
    if action == UNPUBLISH and not table.is_publish:
        return NOT_PUBLISHED
    return ""


def _others_datasets(user, tables) -> list:
    """``(owner's name, Dataset name)`` for every other user's Dataset that
    contains one of ``tables``: after an unpublish they hold a draft member.
    Only Datasets the user may see are named (``visible_datasets``)."""
    rows = (
        Dataset.objects.filter(tables__in=tables)
        .filter(pk__in=visible_datasets(user).values("pk"))
        .exclude(creator=user)
        .order_by("creator__name", "name")
        .values_list("creator__name", "name")
        .distinct()
    )
    return [(owner or "Unknown owner", name) for owner, name in rows]


def _delete_consequences(user, tables) -> dict:
    """What deleting ``tables`` breaks, for the dialog: the Datasets they
    leave (the user's own by name, other people's by owner and name, since
    their membership goes silently), which are published, their Review
    state, an active embargo, and whether knowledge-graph links may point at
    them. Five queries whatever the number of Tables."""
    names = [table.name for table in tables]
    published = [table for table in tables if table.is_publish]
    datasets = (
        Dataset.objects.filter(tables__in=tables)
        .filter(pk__in=visible_datasets(user).values("pk"))
        .order_by("name")
        .distinct()
    )
    reviews = {}
    for name, finished in PeerReview.objects.filter(table__in=names).values_list(
        "table", "is_finished"
    ):
        reviews[name] = reviews.get(name, False) or finished
    embargoes = dict(
        Embargo.objects.filter(table__in=tables, date_ended__gt=timezone.now())
        .order_by("date_ended")
        .values_list("table__name", "date_ended")
    )
    by_name = {table.name: table for table in tables}
    return {
        "published": published,
        "own_datasets": list(
            datasets.filter(creator=user).values_list("name", flat=True)
        ),
        "others_datasets": _others_datasets(user, tables),
        "reviewed": [
            (by_name[name], "Reviewed" if finished else "In review")
            for name, finished in sorted(reviews.items())
        ],
        "embargoed": [
            (by_name[name], until) for name, until in sorted(embargoes.items())
        ],
        # Scenario bundles cite published Tables by address; a deleted one
        # reads ``resolvable: false`` from then on (oekg/resolution.py).
        "knowledge_graph": bool(published),
    }


def preflight(user, action, names, params=None) -> Preflight:
    """What ``action`` would do with the Tables ``names``. Writes nothing.

    A name that is not a Table, or a Table the user holds no role on, is
    left out as "Not one of your tables", the same for both, so the answer
    does not reveal which Tables exist.
    """
    if action not in ACTIONS:
        raise ValueError(f"unknown table action: {action}")
    names = _unique(names)
    found = {table.name: table for table in Table.objects.filter(name__in=names)}
    levels = table_levels(user, found.values())

    eligible, reasons = [], {}
    subject = f"{len(names)} tables"
    for name in names:
        table = found.get(name)
        if table is None or levels[table.pk] <= NO_PERM:
            reason = NOT_YOURS
            if len(names) == 1:
                subject = _quoted([name])
        else:
            reason = _check(user, action, table, levels[table.pk])
            if len(names) == 1:
                subject = _quoted([table.human_readable_name or name])
        if reason:
            reasons.setdefault(reason, []).append(name)
        else:
            eligible.append(table)

    consequences = {}
    if action == UNPUBLISH and eligible:
        consequences["others_datasets"] = _others_datasets(user, eligible)
    elif action == DELETE and eligible:
        consequences = _delete_consequences(user, eligible)
    return Preflight(
        action=action,
        total=len(names),
        eligible=eligible,
        left_out=[LeftOut(reason, group) for reason, group in reasons.items()],
        ceiling=CEILINGS.get(action),
        consequences=consequences,
        subject=subject,
        confirmation=_confirmation(action, eligible),
    )


def _publish_params(params) -> dict:
    """The publish parameters, checked: a real Topic and a known embargo."""
    errors = {}
    topic = (params.get("topic") or "").strip()
    if not topic:
        errors["topic"] = "Choose a topic."
    elif topic == PSEUDO_TOPIC_DRAFT:
        errors["topic"] = "Draft is a status, not a topic. Choose a topic."
    elif not Topic.objects.filter(name=topic).exists():
        errors["topic"] = f"There is no topic “{topic}”."
    embargo = (params.get("embargo") or "none").strip()
    if embargo not in dict(EMBARGO_PERIODS):
        errors["embargo"] = f"“{embargo}” is not an embargo period."
    if errors:
        raise InvalidParameters(errors)
    return {"topic": topic, "embargo": embargo}


def _checked_params(action, params) -> dict:
    if action == PUBLISH:
        return _publish_params(params)
    if action == DELETE:
        # checked against what the preflight asks for inside ``execute``,
        # because that depends on the Tables as they are then
        return {"confirm": (params.get("confirm") or "").strip()}
    return {}


def _confirm_error(check) -> str:
    if check.total == 1:
        return f"Type the table's name, {check.confirmation}, to confirm."
    return f"Type the number of tables, {check.confirmation}, to confirm."


def _write(action, table, params):
    if action == PUBLISH:
        move_publish(table, params["topic"], params["embargo"])
    elif action == UNPUBLISH:
        table.set_not_published()
    elif action == DELETE:
        table.delete_record()


@dataclass(frozen=True)
class _Deleted:
    """What the log line of one deleted Table says, read before its rows
    went: the Datasets it left (all of them, for the operator) and whether
    it was published."""

    table: Table
    datasets: list
    published: bool


def _deleted(tables) -> list:
    left = {}
    for table_id, dataset in Dataset.tables.through.objects.filter(
        table__in=tables
    ).values_list("table_id", "dataset__name"):
        left.setdefault(table_id, []).append(dataset)
    return [
        _Deleted(table, sorted(left.get(table.pk, [])), table.is_publish)
        for table in tables
    ]


def _drop(table):
    """Drop ``table``'s OEDB tables; the exception when that failed, None
    when it worked. Whatever went wrong, the Django rows are gone already,
    so the failure is reported, not raised."""
    try:
        table.drop_oedb_table()
    except Exception as error:
        return error
    return None


def _log(user, action, tables, params, via, deleted=None, dropped=None):
    batch = uuid.uuid4().hex[:12] if len(tables) > 1 else "-"
    extra = ""
    if action == PUBLISH:
        extra = f" topic={params['topic']} embargo={params['embargo']}"
    for index, table in enumerate(tables):
        fields, level, exc_info = extra, logging.INFO, None
        if deleted is not None:
            record, error = deleted[index], dropped[index]
            fields = (
                f" datasets={','.join(record.datasets) or '-'}"
                f" published={'yes' if record.published else 'no'}"
                f" drop={'failed' if error else 'ok'}"
            )
            if error:
                level, exc_info = logging.WARNING, error
        logger.log(
            level,
            "table_action table=%s action=%s by=%s via=%s batch=%s%s",
            table.name,
            action,
            user.pk,
            via,
            batch,
            fields,
            exc_info=exc_info,
        )


def execute(user, action, names, params=None, via="dashboard") -> Outcome:
    """Do ``action`` on every Table in ``names``, or on none of them.

    The parameters are checked first (``InvalidParameters``), and so is the
    ceiling: more names than ``CEILINGS`` allows is refused before anything
    is read. Then, inside one transaction holding a row lock on every named
    Table, each of them is checked again: if any is left out now, for
    whatever reason, the request is refused whole (``ActionRefused``). A
    typed confirmation that does not match what the check asks for now is
    an ``InvalidParameters`` on ``confirm``. The lock makes the check and the
    write one step, so two requests publishing the same draft cannot both
    pass the check (the second would add a second Topic). A failure
    part-way leaves nothing behind, and the log lines are written only once
    the transaction has committed.

    A delete's transaction is durable (it refuses to run nested in another
    one), so once it is left the rows are committed and the OEDB tables are
    dropped, one at a time. A failed drop is in ``Outcome.drop_failed``.
    """
    params = _checked_params(action, params or {})
    ceiling = CEILINGS.get(action)
    if ceiling is not None and len(_unique(names)) > ceiling:
        raise InvalidParameters(
            {"table": _ceiling_message(action, ceiling, len(_unique(names)))}
        )
    deleted = None
    try:
        with transaction.atomic(durable=action == DELETE):
            list(
                Table.objects.select_for_update()
                .filter(name__in=_unique(names))
                .values_list("pk", flat=True)
            )
            check = preflight(user, action, names, params)
            if check.left_out:
                raise ActionRefused(check, check.left_out)
            if not check.eligible:
                raise InvalidParameters({"table": "Name at least one table."})
            if check.confirmation and params["confirm"] != check.confirmation:
                raise InvalidParameters({"confirm": _confirm_error(check)})
            tables = check.eligible
            if action == DELETE:
                deleted = _deleted(tables)
            for table in tables:
                try:
                    _write(action, table, params)
                except APIError as error:
                    raise _WriteRefused(table, error) from error
            if action != DELETE:
                transaction.on_commit(lambda: _log(user, action, tables, params, via))
    except _WriteRefused as refused:
        # ``move_publish`` validates the gate live and refuses on its own, as
        # it does for a stored pass gone stale; the transaction has rolled
        # back every Table written before it.
        again = preflight(user, action, names, params)
        reason = LeftOut(str(refused.error), [refused.table.name])
        raise ActionRefused(again, again.left_out or [reason]) from refused.error
    if action != DELETE:
        return Outcome(action, tables, params)
    dropped = [_drop(table) for table in tables]
    _log(user, action, tables, params, via, deleted=deleted, dropped=dropped)
    failed = [table for table, error in zip(tables, dropped) if error]
    return Outcome(action, tables, params, drop_failed=failed)


class _WriteRefused(Exception):
    """A write refused one Table: which, and the ``APIError`` it raised."""

    def __init__(self, table, error):
        super().__init__(str(error))
        self.table = table
        self.error = error
