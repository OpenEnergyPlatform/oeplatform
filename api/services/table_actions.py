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

A row action is a bulk action of one: both operations take a list of names,
and the dashboard sends one name from a row's menu.

The actions so far are ``publish`` and ``unpublish``; delete and the Dataset
assignment join as their tickets land (#2562, #2563).

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

``batch`` ties together the Tables of one request with more than one Table,
and is ``-`` for a single Table. No audit model: these lines are the record.
"""  # noqa: 501

import logging
import uuid
from dataclasses import dataclass, field

from django.db import transaction

from api.actions import move_publish
from api.error import APIError
from dataedit.models import Dataset, Table, Topic
from login.models import GroupPermission, Organization, UserPermission
from login.permissions import ADMIN_PERM, NO_PERM
from login.tables_tab import PUBLISH_GATE, visible_datasets
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

logger = logging.getLogger("oeplatform.table_actions")

PUBLISH, UNPUBLISH = "publish", "unpublish"
ACTIONS = (PUBLISH, UNPUBLISH)

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
}

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
    the action takes in one request, None while no limit is set (the bulk
    ceilings are measured in #2564). ``consequences`` holds what the dialog
    has to state for this action, and ``subject`` is what the request is
    about: the one Table's title, or "n tables".
    """

    action: str
    total: int
    eligible: list
    left_out: list
    ceiling: int = None
    consequences: dict = field(default_factory=dict)
    subject: str = ""

    @property
    def names(self) -> list:
        return [table.name for table in self.eligible]


@dataclass(frozen=True)
class Outcome:
    """What ``execute`` did: the action and the Tables it changed, as they
    are now."""

    action: str
    tables: list
    params: dict


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

    Live: the gate is run on the named Tables. Once the result is stored
    (#2560) the preflight reads the stored flag instead, which is why only
    the preflight asks here; publishing itself validates live either way.
    """
    failed = [check.name for check in PUBLISH_GATE if not check.run(table)["status"]]
    if not failed:
        return ""
    return "Fails the Publish gate: " + ", ".join(failed)


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
    return Preflight(
        action=action,
        total=len(names),
        eligible=eligible,
        left_out=[LeftOut(reason, group) for reason, group in reasons.items()],
        consequences=consequences,
        subject=subject,
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
    return {}


def _write(action, table, params):
    if action == PUBLISH:
        move_publish(table, params["topic"], params["embargo"])
    elif action == UNPUBLISH:
        table.set_not_published()


def _log(user, action, tables, params, via):
    batch = uuid.uuid4().hex[:12] if len(tables) > 1 else "-"
    extra = ""
    if action == PUBLISH:
        extra = f" topic={params['topic']} embargo={params['embargo']}"
    for table in tables:
        logger.info(
            "table_action table=%s action=%s by=%s via=%s batch=%s%s",
            table.name,
            action,
            user.pk,
            via,
            batch,
            extra,
        )


def execute(user, action, names, params=None, via="dashboard") -> Outcome:
    """Do ``action`` on every Table in ``names``, or on none of them.

    The parameters are checked first (``InvalidParameters``). Then, inside
    one transaction holding a row lock on every named Table, each of them is
    checked again: if any is left out now, for whatever reason, the request
    is refused whole (``ActionRefused``). The lock makes the check and the
    write one step, so two requests publishing the same draft cannot both
    pass the check (the second would add a second Topic). A failure
    part-way leaves nothing behind, and the log lines are written only once
    the transaction has committed.
    """
    params = _checked_params(action, params or {})
    check = None
    try:
        with transaction.atomic():
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
            tables = check.eligible
            for table in tables:
                _write(action, table, params)
            transaction.on_commit(lambda: _log(user, action, tables, params, via))
    except APIError as error:
        # ``move_publish`` validates the gate live and refuses on its own;
        # the transaction has rolled back every Table written before it.
        again = preflight(user, action, names, params)
        raise ActionRefused(
            again, again.left_out or [LeftOut(str(error), check.names)]
        ) from error
    return Outcome(action, tables, params)
