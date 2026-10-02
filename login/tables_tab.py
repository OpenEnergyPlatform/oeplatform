"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The tables tab of the profile dashboard (spec #2551): which Tables a user
sees there, how the list filters and sorts, and what each row says.

- ``accessible_tables``: every Table the user holds at least Data editor on,
  directly or through an Organization, sandbox Tables left out. Built as a
  primary-key subquery, so it carries no join an aggregate could multiply and
  needs no ``distinct()``; it deliberately does not reuse
  ``myuser.get_tables_queryset``, which ORs two joined querysets.
- ``tables_listing``: the tab's ``login.listing.Listing`` for one viewer. It
  is a function of the viewer because the Datasets column counts only the
  Datasets that viewer may see, and so does its sort.
- ``visible_datasets``: the one statement of which Datasets a viewer may see
  in a row, read by both the Datasets cell and its sort, so the number shown
  and the order it sorts by cannot disagree.
- ``table_rows``: one page of Tables as ``TableRow`` objects. The embargo,
  the Review state and the Topics are read in the page query; the Access cell
  and the Datasets cell in three more queries for the whole page, whatever
  its size. The Publish gate is computed live for the rows on the page only.
"""  # noqa: 501

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    Case,
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Lower, Now, NullIf

from dataedit.models import Dataset, Embargo, PeerReview, Table
from dataedit.peer_review.badges import badge_label, normalize_badge
from login.listing import Choice, Filter, Listing, Segment, Sort
from login.models import GroupPermission, UserPermission
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

# The Table roles by level. "Admin" rather than "Table admin" because the
# row is always about one Table.
ROLE_LABELS = {
    WRITE_PERM: "Data editor",
    DELETE_PERM: "Data maintainer",
    ADMIN_PERM: "Admin",
}

DRAFT, PUBLISHED, EMBARGOED = "draft", "published", "embargoed"

REVIEWED, IN_REVIEW, NOT_REVIEWED = "reviewed", "in_review", "not_reviewed"

# How many Topics a row shows as chips before "+n".
TOPICS_SHOWN = 2

# What the Table column shows and sorts by: the title, or the technical name
# for a Table without one. Lower-cased for sorting, so case does not split
# the alphabet in two.
DISPLAYED_TITLE = Lower(Coalesce(NullIf(F("human_readable_name"), Value("")), "name"))

# A peer review names its Table by name, not by key.
_REVIEWS = PeerReview.objects.filter(table=OuterRef("name"))
_FINISHED_REVIEWS = _REVIEWS.filter(is_finished=True)

# The Review state as a number, for sorting: Not reviewed < In review <
# Reviewed. A finished review outranks an open one: a later round starting
# does not retract the review that finished.
REVIEW_RANK = Case(
    When(Exists(_FINISHED_REVIEWS), then=Value(2)),
    When(Exists(_REVIEWS.filter(is_finished=False)), then=Value(1)),
    default=Value(0),
    output_field=IntegerField(),
)
REVIEW_STATES = {2: REVIEWED, 1: IN_REVIEW, 0: NOT_REVIEWED}

# Which Datasets count as published. Dataset has no lifecycle yet, so today
# every Dataset is published (they are all publicly listed). When the
# lifecycle gives Dataset its flag, this condition is the one line to change:
# the Datasets cell and its sort both read it through ``visible_datasets``.
PUBLISHED_DATASETS = Q(uuid__isnull=False)


@dataclass(frozen=True)
class GateCheck:
    """One check of the Publish gate: ``name`` is what a failing row shows,
    ``label`` what the reasons popover calls it, ``run`` the check itself,
    answering ``{"status": bool, "error": str}`` like
    ``Table.validate_open_data_license``."""

    name: str
    label: str
    run: Callable[[Table], dict]


# The checks the Publish gate enforces, in the order a row names them. Today
# that is the open data license alone, the one content refusal publishing
# makes (``api.actions`` refuses a publish on exactly this check). A check
# joins this list in the same change that adds it to the gate, so ✓ keeps
# meaning "publishing will not refuse this Table on its content".
PUBLISH_GATE = (
    GateCheck("License", "Open data license", lambda t: t.validate_open_data_license()),
)


def accessible_tables(user):
    """Every non-sandbox Table ``user`` holds at least Data editor on,
    directly or through an Organization they are a member of."""
    direct = UserPermission.objects.filter(holder=user, level__gte=WRITE_PERM).values(
        "table_id"
    )
    through_organizations = GroupPermission.objects.filter(
        holder__memberships__user=user, level__gte=WRITE_PERM
    ).values("table_id")
    return Table.objects.filter(
        Q(pk__in=direct) | Q(pk__in=through_organizations), is_sandbox=False
    )


def visible_datasets(user):
    """The Datasets ``user`` may see in a row: their own, drafts included,
    and other people's published ones. Never another user's draft, because
    the dashboard must not reveal what others are preparing."""
    return Dataset.objects.filter(Q(creator=user) | PUBLISHED_DATASETS)


def visible_dataset_count(user):
    """How many of ``visible_datasets(user)`` contain the outer Table, as an
    expression: one annotated ``Count`` in a subquery, so it joins nothing
    into the outer query that could multiply its rows."""
    memberships = (
        Dataset.tables.through.objects.filter(
            table_id=OuterRef("pk"), dataset__in=visible_datasets(user)
        )
        .order_by()
        .values("table_id")
        .annotate(count=Count("dataset_id"))
        .values("count")
    )
    return Coalesce(Subquery(memberships[:1]), Value(0))


def _search(queryset, text):
    return queryset.filter(
        Q(name__icontains=text) | Q(human_readable_name__icontains=text)
    )


def tables_listing(user) -> Listing:
    """The tables tab's list as ``user`` sees it."""
    return Listing(
        singular="table",
        plural="tables",
        filters=(Filter("search", lambda raw: raw.strip() or None, _search),),
        # Embargoed counts as published: an embargo restricts the data of a
        # published Table, it is not a third state.
        segment=Segment(
            "status",
            "All",
            (
                Choice(DRAFT, "Draft", Q(is_publish=False)),
                Choice(PUBLISHED, "Published", Q(is_publish=True)),
            ),
        ),
        # Ascending is "least done first" throughout: drafts before published
        # Tables, unreviewed before reviewed, in no Dataset before in many.
        sorts=(
            Sort("table", "Table", DISPLAYED_TITLE),
            Sort("status", "Status", F("is_publish")),
            Sort("review", "Review", REVIEW_RANK),
            Sort("datasets", "Datasets", visible_dataset_count(user)),
        ),
        # Interim default until the Modified column lands (#2557), which makes
        # "-modified" the default.
        default_sort="table",
        tiebreak=(DISPLAYED_TITLE.asc(), F("pk").asc()),
    )


@dataclass(frozen=True)
class CheckResult:
    """What one Publish gate check said about one Table."""

    name: str
    label: str
    passed: bool
    reason: str = ""


@dataclass(frozen=True)
class DatasetRef:
    """A Dataset a row's Table is in, as the viewer may see it. ``owner`` is
    the creator's name, left empty for the viewer's own."""

    name: str
    own: bool
    owner: str = ""


@dataclass
class TableRow:
    """What one row of the list says about one Table."""

    table: Table
    status: str
    embargo_until: datetime = None
    direct: bool = False
    organizations: list = field(default_factory=list)
    level: int = WRITE_PERM
    checks: list = field(default_factory=list)
    review_state: str = NOT_REVIEWED
    review_badge: str = ""
    review_id: int = None
    datasets: list = field(default_factory=list)
    topics: list = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.table.human_readable_name or self.table.name

    @property
    def has_title(self) -> bool:
        """Whether a title is shown, so the technical name goes beneath it
        rather than being shown twice."""
        return bool(self.table.human_readable_name)

    @property
    def role_label(self) -> str:
        """The effective role, only when it is below Admin: the common case
        stays quiet and the unusual one stands out."""
        if self.level >= ADMIN_PERM:
            return ""
        return ROLE_LABELS.get(self.level, ROLE_LABELS[WRITE_PERM])

    @property
    def access_label(self) -> str:
        """What the Access cell says to a screen reader: the holders, the
        role if below Admin, and what a click does."""
        label = ", ".join((["You"] if self.direct else []) + self.organizations)
        if self.role_label:
            label += f", your role {self.role_label}"
        return f"Access: {label}. Manage access"

    @property
    def publishable(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_label(self) -> str:
        """What a row failing the gate shows beside ✗: the failed check, or
        "n of m" once several fail."""
        failed = [check for check in self.checks if not check.passed]
        if len(failed) == 1:
            return failed[0].name
        return f"{len(failed)} of {len(self.checks)}"

    @property
    def shown_topics(self) -> list:
        return self.topics[:TOPICS_SHOWN]

    @property
    def more_topics(self) -> list:
        return self.topics[TOPICS_SHOWN:]


def publish_checks(table) -> list:
    """Every check of the Publish gate, run on ``table`` now."""
    results = []
    for check in PUBLISH_GATE:
        outcome = check.run(table)
        passed = bool(outcome["status"])
        results.append(
            CheckResult(
                check.name, check.label, passed, "" if passed else outcome["error"]
            )
        )
    return results


def table_rows(user):
    """The ``rows`` callable for ``tables_listing(user).page``: a page of
    Tables as ``TableRow`` objects, in four queries for the page."""

    def rows(page_queryset):
        active_embargo = Embargo.objects.filter(
            table=OuterRef("pk"), date_ended__gt=Now()
        ).order_by("-date_ended")
        latest_finished = _FINISHED_REVIEWS.order_by(
            F("date_finished").desc(nulls_last=True), "-pk"
        )
        # Topic's key is its name. The draft pseudo-topic is a status, never
        # a Topic, so it is never shown as one.
        topic_names = (
            Table.topics.through.objects.filter(table_id=OuterRef("pk"))
            .exclude(topic_id=PSEUDO_TOPIC_DRAFT)
            .order_by()
            .values("table_id")
            .annotate(names=ArrayAgg("topic_id", ordering="topic_id"))
            .values("names")
        )
        tables = list(
            page_queryset.annotate(
                embargo_until=Subquery(active_embargo.values("date_ended")[:1]),
                review_rank=REVIEW_RANK,
                review_id=Subquery(latest_finished.values("pk")[:1]),
                review_badge=Subquery(latest_finished.values("review__badge")[:1]),
                topic_names=Subquery(topic_names[:1]),
            )
        )
        ids = [t.pk for t in tables]
        direct = dict(
            UserPermission.objects.filter(holder=user, table_id__in=ids).values_list(
                "table_id", "level"
            )
        )
        through = {}
        for table_id, name, level in (
            GroupPermission.objects.filter(
                holder__memberships__user=user,
                table_id__in=ids,
                level__gte=WRITE_PERM,
            )
            .order_by("holder__name")
            .values_list("table_id", "holder__name", "level")
        ):
            through.setdefault(table_id, []).append((name, level))

        in_datasets = {}
        for (
            table_id,
            name,
            creator_id,
            creator_name,
        ) in Dataset.tables.through.objects.filter(
            table_id__in=ids, dataset__in=visible_datasets(user)
        ).values_list(
            "table_id",
            "dataset__name",
            "dataset__creator_id",
            "dataset__creator__name",
        ):
            own = creator_id == user.pk
            in_datasets.setdefault(table_id, []).append(
                DatasetRef(name, own, "" if own else creator_name or "")
            )

        result = []
        for table in tables:
            direct_level = direct.get(table.pk, 0)
            organizations = through.get(table.pk, [])
            if not table.is_publish:
                status = DRAFT
            elif table.embargo_until:
                status = EMBARGOED
            else:
                status = PUBLISHED
            reviewed = table.review_rank == 2
            result.append(
                TableRow(
                    table=table,
                    status=status,
                    embargo_until=table.embargo_until,
                    direct=direct_level >= WRITE_PERM,
                    organizations=[name for name, _ in organizations],
                    level=max([direct_level] + [level for _, level in organizations]),
                    checks=publish_checks(table),
                    review_state=REVIEW_STATES[table.review_rank],
                    # the badge the linked review granted, so the pill and
                    # the review it opens describe the same record
                    review_badge=(
                        badge_label(normalize_badge(table.review_badge))
                        if reviewed
                        else ""
                    ),
                    review_id=table.review_id if reviewed else None,
                    # the viewer's own Datasets first, each group by name
                    datasets=sorted(
                        in_datasets.get(table.pk, []),
                        key=lambda d: (not d.own, d.name),
                    ),
                    topics=table.topic_names or [],
                )
            )
        return result

    return rows
