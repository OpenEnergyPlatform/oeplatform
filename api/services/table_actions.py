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

The actions are ``publish``, ``unpublish``, ``delete``, and adding a Table to
or removing it from one of the user's own Datasets (``dataset_add``,
``dataset_remove``, with the Dataset as the ``dataset`` parameter). Whether a Table may be added at all is the
curation rule of ``api.services.dataset_creation.assignable_tables``, the
same rule the dataset assign API and the Dataset tab's picker read.

Two more change who holds a role (#2568): sharing the Tables with one of the
user's Organizations (``organization_share``, with ``organization`` and
``level``) and removing an Organization from them (``organization_remove``,
with ``organization``). They are the bulk bar's only, and every rule about
them is the permission service's (``login.table_roles``: its plan decides
what is unchanged, left out and lost, and its two bulk writes write and log).
This module gives them what every action gets: the preflight with its
left-out groups and ceiling, the role gate, the row lock and the whole-request
refusal. Their log lines are the permission service's
``table_permission_write``, one per Table written, not ``table_action``: a
change of access has one record, whichever way it was made.

The role an action needs is read off ``table_levels`` (``login.table_roles``,
the permission service), which states the platform's permission rule
set-based, as ``myuser.get_table_permission_level``
does for one Table: the highest of the user's direct grant and the grants of
their Organizations, and Table admin on every Table for a platform admin or a
member of an admin Organization. It is the same rule the API's permission
decorators read, so the API's publish, unpublish and delete endpoints call
this service (#2569) without changing who may do what.

Log lines, on the ``oeplatform.table_actions`` logger, one per Table::

    table_action table=<name> action=<action> by=<user pk> via=<entry point>
        batch=<id>|- [topic=<topic> embargo=<period>] [dataset=<name>]
        [datasets=<names left>|- published=yes|no drop=ok|failed]

``batch`` ties together the Tables of one request with more than one Table,
and is ``-`` for a single Table. A failed drop is logged at WARNING with its
traceback. No audit model: these lines are the record.
"""  # noqa: 501

import logging
import uuid
from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from api.actions import move_publish
from api.error import APIError
from api.services.dataset_creation import assign_table, assignable_tables
from dataedit.models import Dataset, Embargo, PeerReview, Table, Topic
from dataedit.publish_gate import publish_checks
from login import table_roles
from login.models import Organization
from login.permissions import ADMIN_PERM, DELETE_PERM, NO_PERM, WRITE_PERM
from login.table_roles import table_levels
from login.tables_tab import visible_datasets
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

logger = logging.getLogger("oeplatform.table_actions")

PUBLISH, UNPUBLISH, DELETE = "publish", "unpublish", "delete"
DATASET_ADD, DATASET_REMOVE = "dataset_add", "dataset_remove"
ORGANIZATION_SHARE, ORGANIZATION_REMOVE = "organization_share", "organization_remove"
ACTIONS = (
    PUBLISH,
    UNPUBLISH,
    DELETE,
    DATASET_ADD,
    DATASET_REMOVE,
    ORGANIZATION_SHARE,
    ORGANIZATION_REMOVE,
)
DATASET_ACTIONS = (DATASET_ADD, DATASET_REMOVE)
ORGANIZATION_ACTIONS = (ORGANIZATION_SHARE, ORGANIZATION_REMOVE)

# The parameters a bulk dialog chooses inside the dialog, which what it
# leaves out depends on. Its re-check sends them, and the preview carries the
# ones it was checked against as ``previewed`` (``choice``), so a
# confirmation sent before the re-check of a newer choice came back is
# checked again instead of run.
CHOICES = {
    DATASET_ADD: ("dataset",),
    DATASET_REMOVE: ("dataset",),
    ORGANIZATION_SHARE: ("organization", "level"),
    ORGANIZATION_REMOVE: ("organization",),
}

# What an embargo may be when publishing, in the order the dialog offers
# them; the values are the ones ``api.actions.move_publish`` reads.
EMBARGO_PERIODS = (
    ("none", "No embargo"),
    ("6_months", "6 months"),
    ("1_year", "1 year"),
)

# Publishing without naming an embargo leaves the Table's embargo as it is,
# which ``move_publish`` does for any value but the three above. The dialog
# never sends it; the publish API does when its request names no embargo,
# because there an omitted embargo has never lifted one.
KEEP_EMBARGO = "keep"


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
    DATASET_ADD: RoleGate(WRITE_PERM, "Only Data editors can add to a dataset"),
    DATASET_REMOVE: RoleGate(WRITE_PERM, "Only Data editors can remove from a dataset"),
    DELETE: RoleGate(DELETE_PERM, "Only Data maintainers and Table admins can delete"),
    ORGANIZATION_SHARE: RoleGate(ADMIN_PERM, "Only Table admins can share a table"),
    ORGANIZATION_REMOVE: RoleGate(
        ADMIN_PERM, "Only Table admins can remove an organization"
    ),
}

# The most Tables one request may name, per action. The dashboard is
# synchronous by design (no task queue), so a request has to finish inside
# the host's timeout; mass work stays possible through the API, one call per
# Table. Over the ceiling the preflight reads nothing and nothing can be
# confirmed.
#
# Publish and unpublish: 1,000 each. The same host limit as delete's below
# (300 s). Measured locally with ``benchmarks/tables_tab/publish_cost.py``
# (Postgres 14, batches of 100, 400 and 1,000, three rounds), per Table,
# against 6 / 60 / 500 KB of metadata: publishing (with an embargo, the
# heaviest) 6.0-7.5 / 7.2-9.1 / 20-34 ms, unpublishing 1.6-2.1 / 2.8-4.2 /
# 16-21 ms; the preflight is 0.1-0.5 / 0.4-0.5 / 3.0-5.0 ms of that and costs
# the same whether the Publish gate is read from the stored flag or run
# live, because decoding the metadata is what it pays for. Both writes save
# the whole row, which is why they grow with the metadata. At the worst 34
# ms, 1,000 Tables take 34 s: a safety factor of about 9 against the 300 s,
# room for production's database answering each of the eight or so queries
# a publish makes per Table more slowly than a local one. Typical (60 KB):
# about 9 s. The largest account (2,068 Tables) publishes in three requests.
# A selection of that size travels as one comma-joined field, never as one
# parameter per Table: Django refuses more than 1,000 parameters
# (``DATA_UPLOAD_MAX_NUMBER_FIELDS``), which a full batch would exceed.
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
#
# Adding to and removing from a Dataset: 2,500 each. The same host limit
# (300 s). Measured locally with ``benchmarks/tables_tab/dataset_cost.py``
# (Postgres 14, batches of 100, 400 and 1,000, three rounds), per Table,
# against 6 / 60 / 500 KB of metadata: adding 2.5-3.0 / 2.7-3.3 / 5.0-6.8
# ms, removing 0.8-1.2 / 1.1-1.4 / 3.3-3.9 ms; the preflight with a Dataset
# chosen is 0.1-0.3 / 0.4-0.7 / 3.0-3.5 ms of that. Adding is the dearer: it
# writes the membership and seeds the Table's Topics into the Dataset.
# Neither saves the Table, so the metadata costs only its decoding in the
# preflight. At the worst 6.8 ms, 2,500 Tables take about 17 s: a safety
# factor of about 17 against the 300 s, more than publish's, because this
# ceiling is set by what a curator needs rather than by time: "select all"
# on the largest account (2,068 Tables), then "Add to dataset", is one
# request.
#
# Sharing with an Organization and removing one: 2,500 each, for the same
# reason as the Dataset actions: "select all" on the largest account, then
# "Share with organization…", is one request. The same host limit (300 s).
# Measured locally with ``benchmarks/tables_tab/organization_cost.py``
# (Postgres 14, batches of 100, 400 and 1,000, three rounds, an Organization
# of ten members holding Data editor on half the Tables, shared at Data
# maintainer so that both an add and a change are measured), per Table,
# against 6 / 60 / 500 KB of metadata: sharing 0.7-1.1 / 1.0-1.6 / 3.6-4.9
# ms, removing 0.8-1.4 / 1.1-1.5 / 3.4-5.2 ms; the preflight with both chosen
# is 0.1-0.7 / 0.4-0.6 / 3.1-4.5 ms of that, so loading the Tables, metadata
# and all, is most of it; the permission service's plan is a handful of
# queries whatever the batch. Neither saves the Table. At the
# worst 5.2 ms, 2,500 Tables take about 13 s: a safety factor of about 23.
CEILINGS = {
    PUBLISH: 1000,
    UNPUBLISH: 1000,
    DATASET_ADD: 2500,
    DATASET_REMOVE: 2500,
    ORGANIZATION_SHARE: 2500,
    ORGANIZATION_REMOVE: 2500,
    DELETE: 50,
}

# A batch of more than this many Tables is confirmed by typing its count.
TYPED_COUNT_ABOVE = 10

# Left-out reasons that do not depend on the role. A gate failure is
# "Fails the Publish gate: <check>" (``_gate_reason``).
NOT_YOURS = "Not one of your tables"
ALREADY_PUBLISHED = "Already published"
NOT_PUBLISHED = "Not published"
# The curation rule (``assignable_tables``) refusing a Table the role allows:
# a draft or embargoed Table the user holds no grant on. Only a platform
# admin gets that far, and the rule gives them no exemption.
MAY_NOT_ASSIGN = "Drafts and embargoed tables need Data editor on the table"
# A removal whose dashboard losses grew after the dialog named them: the user
# confirmed losing fewer Tables than the removal would take.
LOSE_ACCESS_UNSAID = "You would also lose access to these, which the dialog did not say"


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
    # every name sent, once each, in the order sent: what a bulk dialog
    # re-checks when the user chooses a Dataset, so the left-out groups stay
    # complete although the form posts only the eligible names
    requested: list = field(default_factory=list)
    # The Dataset actions only: the user's own Datasets the action could
    # change for these Tables, and the one it is about (None until chosen).
    datasets: list = field(default_factory=list)
    dataset: Dataset = None
    # The Organization actions only: the Organizations the user can choose
    # (each with ``members``), the one chosen (None until chosen), the role
    # a share gives, and the Tables a share leaves as they are because the
    # Organization holds that role or more there already. A removal's
    # ``consequences["lose_access"]`` are the Tables it takes off the user's
    # dashboard.
    organizations: list = field(default_factory=list)
    organization: object = None
    level: int = None
    members: int = 0
    unchanged: list = field(default_factory=list)

    @property
    def names(self) -> list:
        return [table.name for table in self.eligible]

    @property
    def role(self) -> str:
        """The name of the role a share gives, "" without one."""
        return table_roles.role_label(self.level) if self.level else ""

    @property
    def rechecks(self) -> bool:
        """Whether the dialog asks the preflight again when the user chooses
        in it: a batch's Dataset, and an Organization (and role) always,
        because what is unchanged or left out depends on it even for one
        Table."""
        if self.action in ORGANIZATION_ACTIONS:
            return bool(self.organizations)
        return self.action in DATASET_ACTIONS and bool(self.datasets) and self.total > 1

    @property
    def previewed(self) -> str:
        """The choice this preview was checked against (``choice``)."""
        chosen = {
            "dataset": self.dataset.name if self.dataset else "",
            "organization": self.organization.pk if self.organization else "",
            "level": self.level or "",
        }
        return choice(self.action, chosen)

    @property
    def confirmable(self) -> bool:
        """Whether the dialog can be confirmed: something is eligible, the
        names are within the ceiling and, for the Dataset actions, there is a
        Dataset to choose."""
        if self.over_ceiling:
            return False
        if self.action in DATASET_ACTIONS and not self.datasets:
            return False
        if self.action in ORGANIZATION_ACTIONS and self.organization is None:
            return False
        if self.action == ORGANIZATION_SHARE and self.level is None:
            return False
        return bool(self.eligible)

    @property
    def over_ceiling(self) -> bool:
        return self.ceiling is not None and self.total > self.ceiling

    @property
    def ceiling_message(self) -> str:
        return _ceiling_message(self.action, self.ceiling, self.total)

    @property
    def ceiling_rule(self) -> str:
        """The ceiling as the dialog states it before anything exceeds it,
        "" where the action has none."""
        return _ceiling_rule(self.action, self.ceiling) if self.ceiling else ""

    @property
    def dataset_title(self) -> str:
        """What the chosen Dataset is called, "" while none is chosen."""
        return dataset_title(self.dataset) if self.dataset else ""


@dataclass(frozen=True)
class Outcome:
    """What ``execute`` did: the action and the Tables it changed, as they
    are now. After a delete the Tables have no primary key any more, and
    ``drop_failed`` names those whose OEDB table could not be dropped."""

    action: str
    tables: list
    params: dict
    drop_failed: list = field(default_factory=list)
    # an Organization removed: the Tables that left the user's dashboard
    lost: list = field(default_factory=list)


def own_datasets(user):
    """The Datasets ``user`` created: the only ones they may add a Table to
    or remove one from."""
    return Dataset.objects.filter(creator=user)


def dataset_title(dataset) -> str:
    """What a Dataset is called where the user reads it."""
    return (dataset.metadata or {}).get("title") or dataset.name


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

    The stored verdict (``Table.publishable``, kept by the one metadata write
    path) decides what needs a validator pass:

    - a stored pass is taken at its word, so a batch of publishable Tables
      costs no validator pass at all;
    - a stored fail runs the checks for that Table only, because the reason
      the dialog names is the failed check (``dataedit.publish_gate``). When
      they pass after all, the flag was stale and the Table is eligible: the
      live result wins, as it does in the Publishable cell, which the user
      has just read;
    - no verdict yet (NULL: a Table untouched since before the flag existed,
      until ``recompute_publish_gate`` has run) runs the checks too, since a
      Table that has never been judged can be neither kept out nor let
      through on faith.

    So only the Tables the preflight may leave out are validated. Publishing
    itself validates live (``move_publish``), and a Table that fails there
    refuses the whole request: a stale pass can mislabel a row in the
    dialog, never publish it.
    """
    if table.publishable:
        return ""
    failed = [check.name for check in publish_checks(table) if not check.passed]
    if not failed:
        return ""
    return "Fails the Publish gate: " + ", ".join(failed)


# What an action is called at the start of a sentence, as in the ceiling's
# "Delete takes at most 50 tables at a time".
ACTION_NAMES = {
    PUBLISH: "Publish",
    UNPUBLISH: "Unpublish",
    DELETE: "Delete",
    DATASET_ADD: "Adding to a dataset",
    DATASET_REMOVE: "Removing from a dataset",
    ORGANIZATION_SHARE: "Sharing with an organization",
    ORGANIZATION_REMOVE: "Removing an organization",
}


def choice(action, params) -> str:
    """The dialog's choice in ``params`` (``CHOICES``) as one string: what
    the preview carries as ``previewed``, and what a confirmation's own
    parameters are compared with."""
    return ",".join(str(params.get(key) or "") for key in CHOICES.get(action, ()))


def _ceiling_rule(action, ceiling) -> str:
    return f"{ACTION_NAMES[action]} takes at most {ceiling:,} tables at a time."


def _ceiling_message(action, ceiling, total) -> str:
    return f"{_ceiling_rule(action, ceiling)[:-1]}; you selected {total:,}."


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


def _check(user, action, table, level, assignable=frozenset(), republish=False) -> str:
    """Why ``action`` would leave ``table`` out, or "" when it would act.
    ``assignable`` holds the primary keys the curation rule accepts; only
    adding to a Dataset reads it. Whether the Table is in the chosen Dataset
    is decided afterwards (``_by_membership``). ``republish`` lets a publish
    take a Table that is published already (``_publish_params``)."""
    if level < ROLE_GATES[action].level:
        return ROLE_GATES[action].refusal
    if action == DATASET_ADD and table.pk not in assignable:
        return MAY_NOT_ASSIGN
    if action == PUBLISH:
        if table.is_publish and not republish:
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
    their membership goes silently), each with how many of ``tables`` leave
    it, which are published, their Review state, an active embargo, and
    whether knowledge-graph links may point at them. A batch is shown
    counted rather than listed per Table, so the review states are counted
    here too. Three queries whatever the number of Tables."""
    names = [table.name for table in tables]
    published = [table for table in tables if table.is_publish]
    datasets = (
        Dataset.objects.filter(pk__in=visible_datasets(user).values("pk"))
        .annotate(leaving=Count("tables", filter=Q(tables__in=tables)))
        .filter(leaving__gt=0)
        .values_list("creator_id", "creator__name", "name", "leaving")
    )
    own, others = [], []
    for creator, owner, name, leaving in datasets:
        if creator == user.pk:
            own.append((name, leaving))
        else:
            others.append((owner or "Unknown owner", name, leaving))
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
    finished = sum(1 for state in reviews.values() if state)
    return {
        "published": published,
        "own_datasets": sorted(own),
        "others_datasets": sorted(others),
        "reviewed": [
            (by_name[name], "Reviewed" if state else "In review")
            for name, state in sorted(reviews.items())
        ],
        "finished_reviews": finished,
        "open_reviews": len(reviews) - finished,
        "embargoed": [
            (by_name[name], until) for name, until in sorted(embargoes.items())
        ],
        # Scenario bundles cite published Tables by address; a deleted one
        # reads ``resolvable: false`` from then on (oekg/resolution.py).
        "knowledge_graph": bool(published),
    }


def _dataset_choices(user, action, tables) -> list:
    """The user's own Datasets ``action`` could change for ``tables``: for
    adding, those still missing at least one of them; for removing, those
    holding at least one. By title. One query."""
    if not tables:
        return []
    ids = [table.pk for table in tables]
    datasets = own_datasets(user).annotate(
        held=Count("tables", filter=Q(tables__in=ids))
    )
    if action == DATASET_ADD:
        datasets = datasets.filter(held__lt=len(ids))
    else:
        datasets = datasets.filter(held__gt=0)
    return sorted(datasets, key=lambda d: (dataset_title(d).lower(), d.name))


def _chosen_dataset(user, value, choices):
    """The Dataset a request is about: ``value`` (a checked Dataset or a
    name) if it is one of the user's own, else nothing. Without a value,
    the only choice when there is exactly one, so a row whose Table is in
    one of the user's Datasets is removed from it in one confirmation."""
    if isinstance(value, Dataset):
        return value if value.creator_id == user.pk else None
    if value:
        for dataset in choices:
            if dataset.name == value:
                return dataset
        return own_datasets(user).filter(name=value).first()
    return choices[0] if len(choices) == 1 else None


def _by_membership(action, dataset, tables):
    """Split ``tables`` into those ``action`` changes in ``dataset`` and
    those it leaves out: already in it (add), not in it (remove)."""
    members = set(
        dataset.tables.filter(pk__in=[t.pk for t in tables]).values_list(
            "pk", flat=True
        )
    )
    title = _quoted([dataset_title(dataset)])
    if action == DATASET_ADD:
        keep, reason = (lambda t: t.pk not in members), f"Already in {title}"
    else:
        keep, reason = (lambda t: t.pk in members), f"Not in {title}"
    kept = [table for table in tables if keep(table)]
    left = [table.name for table in tables if not keep(table)]
    return kept, ([LeftOut(reason, left)] if left else [])


def _organization_choices(user, action, tables) -> list:
    """The Organizations ``action`` can be about for ``tables``: the user's
    own for a share, those holding a role on one of them for a removal."""
    if action == ORGANIZATION_SHARE:
        return list(table_roles.own_organizations(user))
    return list(table_roles.organizations_on(tables)) if tables else []


def _chosen_organization(value, choices):
    """The Organization a request is about: a checked one as it is, an id
    among ``choices``, or the only choice when nothing is named."""
    if hasattr(value, "pk"):
        return value
    for organization in choices:
        if str(organization.pk) == str(value):
            return organization
    return choices[0] if not value and len(choices) == 1 else None


def _share_level(value):
    """The role a share's preview is checked against: the one named, the
    lowest one while none is (the dialog shows it chosen), None for a value
    no Organization may be given."""
    if value in (None, ""):
        return table_roles.ORGANIZATION_ROLES[0].level
    try:
        return table_roles.organization_level(value)
    except table_roles.InvalidRequest:
        return None


def _by_organization(user, action, tables, organization, level):
    """Split ``tables`` by what ``action`` does to them with
    ``organization`` (``table_roles.plan_organization``): the Tables written,
    the left-out groups, the Tables a share leaves unchanged and the plan."""
    plan = table_roles.plan_organization(user, tables, organization, level)
    title = _quoted([organization.name])
    left_out = [
        LeftOut(reason, [table.name for table in group])
        for reason, group in (
            (ROLE_GATES[action].refusal, plan.not_admin),
            (table_roles.NOT_HELD.format(organization=title), plan.not_held),
            (table_roles.ONLY_ADMIN_THERE.format(organization=title), plan.guarded),
        )
        if group
    ]
    return plan.tables, left_out, plan.unchanged, plan


def preflight(user, action, names, params=None) -> Preflight:
    """What ``action`` would do with the Tables ``names``. Writes nothing.

    A name that is not a Table, or a Table the user holds no role on, is
    left out as "Not one of your tables", the same for both, so the answer
    does not reveal which Tables exist.

    A publish leaves out Tables that are published already, unless
    ``params["republish"]`` is set (``_publish_params``).

    For the Dataset actions, ``params["dataset"]`` names the Dataset (see
    ``_chosen_dataset``); the Tables already in it (add) or not in it
    (remove) are left out. Without one, nothing is left out for that
    reason, and ``datasets`` lists what the user can choose.

    For the Organization actions, ``params["organization"]`` names the
    Organization and, for a share, ``params["level"]`` the role (the lowest
    while none is named). A share leaves the Tables where it holds that role
    or more ``unchanged``; a removal leaves out the Tables it holds no role on
    and those whose only Admin is its old Admin grant, and names in
    ``consequences["lose_access"]`` the Tables the user would lose.
    """
    if action not in ACTIONS:
        raise ValueError(f"unknown table action: {action}")
    params = params or {}
    names = _unique(names)
    ceiling = CEILINGS.get(action)
    if ceiling is not None and len(names) > ceiling:
        # Nothing can be confirmed over the ceiling, so nothing is read: a
        # selection of every Table on a large account would otherwise load
        # each of them, metadata and all, only to be refused.
        return Preflight(
            action=action,
            total=len(names),
            eligible=[],
            left_out=[],
            ceiling=ceiling,
            subject=f"{len(names)} tables",
            requested=names,
        )
    found = {table.name: table for table in Table.objects.filter(name__in=names)}
    levels = table_levels(user, found.values())
    assignable = frozenset()
    if action == DATASET_ADD and found:
        assignable = frozenset(
            assignable_tables(user)
            .filter(pk__in=[table.pk for table in found.values()])
            .values_list("pk", flat=True)
        )

    republish = action == PUBLISH and bool(params.get("republish"))

    eligible, reasons = [], {}
    subject = f"{len(names)} tables"
    for name in names:
        table = found.get(name)
        if table is None or levels[table.pk] <= NO_PERM:
            reason = NOT_YOURS
            if len(names) == 1:
                subject = _quoted([name])
        else:
            reason = _check(
                user, action, table, levels[table.pk], assignable, republish
            )
            if len(names) == 1:
                subject = _quoted([table.human_readable_name or name])
        if reason:
            reasons.setdefault(reason, []).append(name)
        else:
            eligible.append(table)

    left_out = [LeftOut(reason, group) for reason, group in reasons.items()]
    datasets, dataset = [], None
    if action in DATASET_ACTIONS:
        datasets = _dataset_choices(user, action, eligible)
        dataset = _chosen_dataset(user, params.get("dataset"), datasets)
        if dataset is not None and eligible:
            eligible, by_membership = _by_membership(action, dataset, eligible)
            left_out += by_membership

    organizations, organization, level, members, unchanged = [], None, None, 0, []
    lose_access = []
    if action in ORGANIZATION_ACTIONS:
        organizations = _organization_choices(user, action, eligible)
        organization = _chosen_organization(params.get("organization"), organizations)
        if action == ORGANIZATION_SHARE:
            level = _share_level(params.get("level"))
        if organization is not None and (level or action == ORGANIZATION_REMOVE):
            eligible, by_organization, unchanged, plan = _by_organization(
                user, action, eligible, organization, level
            )
            left_out += by_organization
            members = plan.members
            lose_access = plan.lose_access

    consequences = {}
    if action == UNPUBLISH and eligible:
        consequences["others_datasets"] = _others_datasets(user, eligible)
    elif action == DELETE and eligible:
        consequences = _delete_consequences(user, eligible)
    elif action == ORGANIZATION_REMOVE and eligible:
        consequences["lose_access"] = lose_access
    return Preflight(
        action=action,
        total=len(names),
        eligible=eligible,
        left_out=left_out,
        ceiling=ceiling,
        consequences=consequences,
        subject=subject,
        confirmation=_confirmation(action, eligible),
        datasets=datasets,
        dataset=dataset,
        requested=names,
        organizations=organizations,
        organization=organization,
        level=level,
        members=members,
        unchanged=unchanged,
    )


def _publish_params(params) -> dict:
    """The publish parameters, checked: a real Topic and a known embargo
    (or ``KEEP_EMBARGO``).

    ``republish`` publishes a Table that is published already again: under
    one more Topic, with the embargo given. Only the publish API sets it,
    because there it has always been the way to add a Topic or change an
    embargo; the dashboard leaves published Tables out, so that a bulk
    publish cannot quietly change Tables that are out already."""
    errors = {}
    topic = (params.get("topic") or "").strip()
    if not topic:
        errors["topic"] = "Choose a topic."
    elif topic == PSEUDO_TOPIC_DRAFT:
        errors["topic"] = "Draft is a status, not a topic. Choose a topic."
    elif not Topic.objects.filter(name=topic).exists():
        errors["topic"] = f"There is no topic “{topic}”."
    embargo = (params.get("embargo") or "none").strip()
    if embargo not in dict(EMBARGO_PERIODS) and embargo != KEEP_EMBARGO:
        errors["embargo"] = f"“{embargo}” is not an embargo period."
    if errors:
        raise InvalidParameters(errors)
    return {
        "topic": topic,
        "embargo": embargo,
        "republish": bool(params.get("republish")),
    }


def _dataset_params(user, params) -> dict:
    """The Dataset parameter, checked: one of the user's own Datasets."""
    value = params.get("dataset")
    name = value.name if isinstance(value, Dataset) else (value or "").strip()
    if not name:
        raise InvalidParameters({"dataset": "Choose one of your datasets."})
    dataset = own_datasets(user).filter(name=name).first()
    if dataset is None:
        raise InvalidParameters({"dataset": f"“{name}” is not one of your datasets."})
    return {"dataset": dataset}


def _organization_params(user, action, params) -> dict:
    """The Organization parameters, checked: one of the user's own
    Organizations and a role it may be given (a share); an Organization, and
    the Tables the dialog said the user would lose (a removal, as a set of
    names, comma-joined when sent)."""
    errors, checked = {}, {}
    value = params.get("organization")
    pk = getattr(value, "pk", value)
    if action == ORGANIZATION_SHARE:
        try:
            checked["level"] = table_roles.organization_level(params.get("level"))
        except table_roles.InvalidRequest as error:
            errors["level"] = error.message
        candidates = table_roles.own_organizations(user)
        missing = "Choose one of your organizations."
    else:
        lose = params.get("lose_access") or ()
        if isinstance(lose, str):
            lose = [name.strip() for name in lose.split(",")]
        checked["lose_access"] = frozenset(name for name in lose if name)
        candidates = Organization.objects.all()
        missing = "Choose an organization."
    organization = candidates.filter(pk=pk).first() if str(pk or "").isdigit() else None
    if organization is None:
        errors["organization"] = missing
    if errors:
        raise InvalidParameters(errors)
    checked["organization"] = organization
    return checked


def _checked_params(user, action, params) -> dict:
    if action == PUBLISH:
        return _publish_params(params)
    if action in DATASET_ACTIONS:
        return _dataset_params(user, params)
    if action in ORGANIZATION_ACTIONS:
        return _organization_params(user, action, params)
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
    elif action == DATASET_ADD:
        assign_table(params["dataset"], table)
    elif action == DATASET_REMOVE:
        params["dataset"].tables.remove(table)
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
    elif action in DATASET_ACTIONS:
        extra = f" dataset={params['dataset'].name}"
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
    params = _checked_params(user, action, params or {})
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
            if action in ORGANIZATION_ACTIONS:
                lost = _organization_write(user, action, check, params, via)
                return Outcome(action, tables, params, lost=lost)
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


def _organization_write(user, action, check, params, via) -> list:
    """Share ``check``'s Tables with the chosen Organization, or remove it
    from them, through the permission service's bulk writes, which log one
    line per Table. Returns the Tables the user lost. The checks have run on
    the Tables as they are now, so only the dashboard losses can still
    disagree with the dialog: losing a Table it did not name refuses the
    request, which then names it."""
    organization = params["organization"]
    try:
        if action == ORGANIZATION_SHARE:
            table_roles.share_with_organization(
                user, check.eligible, organization, params["level"], via=via
            )
            return []
        table_roles.remove_organization(
            user,
            check.eligible,
            organization,
            via=via,
            confirmed=params["lose_access"],
        )
    except table_roles.ConfirmationNeeded as question:
        names = [table.name for table in question.tables]
        raise ActionRefused(check, [LeftOut(LOSE_ACCESS_UNSAID, names)])
    except table_roles.AccessError as error:
        # the service's own checks; the preflight under the same lock has
        # left out every Table they would decline for, so this is a rule
        # the two state differently
        names = [table.name for table in error.tables]
        raise ActionRefused(check, [LeftOut(error.message, names)])
    return check.consequences.get("lose_access", [])


class _WriteRefused(Exception):
    """A write refused one Table: which, and the ``APIError`` it raised."""

    def __init__(self, table, error):
        super().__init__(str(error))
        self.table = table
        self.error = error
