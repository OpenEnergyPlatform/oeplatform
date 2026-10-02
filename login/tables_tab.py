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
- the filters: Search, Publishable, Review, Access, Dataset, and behind
  "More filters" Modified, Topic and Tags, each one declaration. Every clause is a
  column test or a primary-key subquery, so no filter joins anything into
  the list that could multiply a row or a count. Each option source is scoped to the viewer's whole list and
  does not narrow as other filters change, and each costs one query (Access
  two), run only when the request names that filter or the bar is rendered.
- ``table_rows``: one page of Tables as ``TableRow`` objects. The embargo,
  the Review state and the Topics are read in the page query; the Access cell
  and the Datasets cell in three more queries for the whole page, whatever
  its size. The Publish gate is computed live for the rows on the page only.

The Publish gate is ``dataedit.publish_gate``. Its stored verdict,
``Table.publishable``, decides what the Publishable filter and sort see; the
row runs the same checks live for its reasons. Where the two disagree,
something wrote metadata past the one write path: the row shows the live
result and a warning names the Table. A Table whose flag is still NULL
(before the recompute command ran) shows the live result too, and is matched
by neither filter value and sorted last both ways, because nothing is known
about it that a filter could rely on.

Modified is the later of a Table's two stamps, ``data_modified`` and
``metadata_modified`` (``MODIFIED``), which the write paths set. It is the
default sort, newest first, and like every date the list cannot know it sorts
last in both directions and matches no Modified range.
"""  # noqa: 501

import logging
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache

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
from django.db.models.functions import Coalesce, Greatest, Lower, Now, NullIf

from dataedit.models import Dataset, Embargo, PeerReview, Table, Tag
from dataedit.peer_review.badges import badge_label, normalize_badge
from dataedit.publish_gate import passes, publish_checks
from login.listing import (
    Choice,
    ChoiceFilter,
    Filter,
    Listing,
    Option,
    RangeFilter,
    Segment,
    Sort,
    dates_within,
)
from login.models import GroupPermission, UserPermission
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

logger = logging.getLogger("oeplatform.publish_gate")

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

# What the Modified column shows, sorts and filters by: the later of the two
# stamps. Postgres's GREATEST ignores NULLs, so a Table with one half stamped
# shows that half, and one with neither is NULL.
MODIFIED = Greatest(F("data_modified"), F("metadata_modified"))

# The release that started recording Modifications. What the column says
# when it knows nothing, or only the data half (which #2558 backfills from
# the Edit Journals and Bulk Load Events; metadata edits were never
# recorded before). Check it names the release that ships dataedit.0056.
MODIFIED_RECORDED_SINCE = "v1.11.0"
DATA_ONLY_NOTE = (
    f"Last data change. Metadata edits are recorded since {MODIFIED_RECORDED_SINCE}."
)
UNKNOWN_NOTE = f"No change recorded since {MODIFIED_RECORDED_SINCE}."

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
REVIEW_RANK_OF = {state: rank for rank, state in REVIEW_STATES.items()}
REVIEW_OPTIONS = (
    Option(REVIEWED, "Reviewed"),
    Option(IN_REVIEW, "In review"),
    Option(NOT_REVIEWED, "Not reviewed"),
)

# The Publishable filter's values. Fixed, so naming the filter costs no
# query.
YES, NO = "yes", "no"
PUBLISHABLE_OPTIONS = (
    Option(YES, "Publishable", chip="Publishable"),
    Option(NO, "Not publishable", chip="Not publishable"),
)

# The Access filter's value for "a grant of my own", beside Organization ids.
DIRECT = "direct"
# The Dataset filter's two values beside a Dataset name.
IN_ANY, IN_NONE = "any", "none"

# Which Datasets count as published. Dataset has no lifecycle yet, so today
# every Dataset is published (they are all publicly listed). When the
# lifecycle gives Dataset its flag, this condition is the one line to change:
# the Datasets cell and its sort both read it through ``visible_datasets``.
PUBLISHED_DATASETS = Q(uuid__isnull=False)


def accessible_tables(user):
    """Every non-sandbox Table ``user`` holds at least Data editor on,
    directly or through an Organization they are a member of."""
    direct = _direct_grants(user).values("table_id")
    through_organizations = _organization_grants(user).values("table_id")
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


def _publishable(queryset, value):
    """The stored verdict. A NULL flag matches neither value: until the
    recompute ran nothing is known about that Table."""
    return queryset.filter(publishable=value == YES)


def _review(queryset, state):
    """The Review filter reads ``REVIEW_RANK``, the expression the column and
    its sort read, so the filter cannot disagree with the pill."""
    return queryset.alias(review_filter=REVIEW_RANK).filter(
        review_filter=REVIEW_RANK_OF[state]
    )


def _direct_grants(user):
    return UserPermission.objects.filter(holder=user, level__gte=WRITE_PERM)


def _organization_grants(user):
    return GroupPermission.objects.filter(
        holder__memberships__user=user, level__gte=WRITE_PERM
    )


def access_options(user) -> list:
    """Direct, if the user holds a grant of their own on any listed Table,
    then each Organization through which they reach at least one. Two
    queries."""
    options = []
    if _direct_grants(user).filter(table__is_sandbox=False).exists():
        options.append(Option(DIRECT, "Direct", chip="Access: direct"))
    organizations = (
        _organization_grants(user)
        .filter(table__is_sandbox=False)
        .order_by("holder__name", "holder_id")
        .values_list("holder_id", "holder__name")
        .distinct()
    )
    options.extend(
        Option(str(pk), name, group="Your organizations") for pk, name in organizations
    )
    return options


def _access(user):
    def apply(queryset, value):
        if value == DIRECT:
            grants = _direct_grants(user)
        else:
            grants = GroupPermission.objects.filter(
                holder_id=int(value), level__gte=WRITE_PERM
            )
        return queryset.filter(pk__in=grants.values("table_id"))

    return apply


def _memberships():
    return Dataset.tables.through.objects


def dataset_options(user) -> list:
    """In any, In none, then each Dataset the user may see that holds at
    least one of their Tables, their own first, each group by name. One
    query."""
    datasets = visible_datasets(user).filter(
        pk__in=_memberships()
        .filter(table__in=accessible_tables(user))
        .values("dataset_id")
    )
    rows = sorted(
        datasets.values_list("name", "creator_id", "creator__name"),
        key=lambda row: (row[1] != user.pk, row[0]),
    )
    options = [
        Option(IN_ANY, "In any dataset", chip="In any dataset"),
        Option(IN_NONE, "In no dataset", chip="In no dataset"),
    ]
    for name, creator_id, creator_name in rows:
        # A Dataset named "any" or "none" is a legal name the spec's URL
        # contract cannot address: the keyword wins. It is left out rather
        # than offered as an option that would select something else.
        if name in (IN_ANY, IN_NONE):
            continue
        own = creator_id == user.pk
        options.append(
            Option(
                name,
                name if own or not creator_name else f"{name} ({creator_name})",
                group="Your datasets" if own else "Other people's datasets",
                chip=f"Dataset: {name}",
            )
        )
    return options


def _dataset(user):
    """In any and In none read ``visible_datasets``, the rule the Datasets
    cell reads, so "In none" is exactly the rows whose cell reads "–"."""

    def apply(queryset, value):
        if value in (IN_ANY, IN_NONE):
            members = _memberships().filter(dataset__in=visible_datasets(user))
            members = members.values("table_id")
            if value == IN_ANY:
                return queryset.filter(pk__in=members)
            return queryset.exclude(pk__in=members)
        members = _memberships().filter(dataset__name=value).values("table_id")
        return queryset.filter(pk__in=members)

    return apply


def _topic_links():
    return Table.topics.through.objects


def topic_options(user) -> list:
    """The Topics on the user's Tables. The draft pseudo-topic is a status,
    never a Topic, so it is never offered. One query."""
    names = (
        _topic_links()
        .filter(table__in=accessible_tables(user))
        .exclude(topic_id=PSEUDO_TOPIC_DRAFT)
        .order_by("topic_id")
        .values_list("topic_id", flat=True)
        .distinct()
    )
    return [Option(name, name) for name in names]


def _topics(queryset, names):
    """Any of the chosen Topics."""
    links = _topic_links().filter(topic_id__in=names).values("table_id")
    return queryset.filter(pk__in=links)


def _tag_links():
    return Table.tags.through.objects


def tag_options(user) -> list:
    """The tags on the user's Tables. A tag's key is its normalised name
    (``Tag.get_name_normalized``), the value ``dataedit``'s table list puts
    in its URL too, matched as it is there: verbatim, since a stored key need
    not be in today's normal form. One query."""
    tags = (
        Tag.objects.filter(
            pk__in=_tag_links()
            .filter(table__in=accessible_tables(user))
            .values("tag_id")
        )
        .order_by(Lower("name"), "pk")
        .values_list("pk", "name")
    )
    return [Option(pk, name) for pk, name in tags]


def _tags(queryset, keys):
    """All of the chosen tags, the platform's tag convention: one subquery
    per tag, ANDed."""
    for key in keys:
        queryset = queryset.filter(
            pk__in=_tag_links().filter(tag_id=key).values("table_id")
        )
    return queryset


def tables_listing(user) -> Listing:
    """The tables tab's list as ``user`` sees it."""
    return Listing(
        singular="table",
        plural="tables",
        filters=(
            Filter("search", lambda raw: raw.strip() or None, _search, label="Search"),
            ChoiceFilter(
                "publishable", "Publishable", PUBLISHABLE_OPTIONS, _publishable
            ),
            ChoiceFilter("review", "Review", REVIEW_OPTIONS, _review),
            ChoiceFilter(
                "access",
                "Access",
                cache(lambda: access_options(user)),
                _access(user),
            ),
            ChoiceFilter(
                "dataset",
                "Dataset",
                cache(lambda: dataset_options(user)),
                _dataset(user),
                blank="Dataset: any or none",
            ),
            RangeFilter(
                "modified",
                "Modified",
                dates_within(MODIFIED, "modified_range"),
                more=True,
            ),
            ChoiceFilter(
                "topics",
                "Topic",
                cache(lambda: topic_options(user)),
                _topics,
                multiple=True,
                more=True,
                hint="any of the ticked",
            ),
            ChoiceFilter(
                "tags",
                "Tag",
                cache(lambda: tag_options(user)),
                _tags,
                multiple=True,
                more=True,
                hint="all of the ticked",
            ),
        ),
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
        # Tables, not publishable before publishable, unreviewed before
        # reviewed, in no Dataset before in many.
        sorts=(
            Sort("table", "Table", DISPLAYED_TITLE, "A to Z", "Z to A"),
            Sort(
                "status",
                "Status",
                F("is_publish"),
                "drafts first",
                "published first",
            ),
            Sort(
                "publishable",
                "Publishable",
                F("publishable"),
                "not publishable first",
                "publishable first",
                nulls_last=True,
            ),
            Sort(
                "review",
                "Review",
                REVIEW_RANK,
                "not reviewed first",
                "reviewed first",
            ),
            Sort(
                "datasets",
                "Datasets",
                visible_dataset_count(user),
                "fewest first",
                "most first",
            ),
            Sort(
                "modified",
                "Modified",
                MODIFIED,
                "oldest first",
                "newest first",
                nulls_last=True,
            ),
        ),
        default_sort="-modified",
        tiebreak=(DISPLAYED_TITLE.asc(), F("pk").asc()),
    )


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
    def in_own_dataset(self) -> bool:
        """Whether one of the viewer's own Datasets holds the Table, so the
        menu can offer to remove it from one."""
        return any(dataset.own for dataset in self.datasets)

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
        """What the Publishable cell shows. Normally the stored verdict and
        the live ``checks`` agree, and this is both. Where they disagree,
        live wins, so the cell never contradicts the reasons beneath it
        (``table_rows`` logs the disagreement); a NULL verdict shows the live
        result too. The filter and the sort read the stored verdict."""
        return passes(self.checks)

    @property
    def failed_label(self) -> str:
        """What a row failing the gate shows beside ✗: the failed check, or
        "n of m" once several fail."""
        failed = [check for check in self.checks if not check.passed]
        if len(failed) == 1:
            return failed[0].name
        return f"{len(failed)} of {len(self.checks)}"

    @property
    def modified(self):
        """When the Table's content last changed, as far as recorded: the
        later of its two stamps, None when neither is known. ``MODIFIED``,
        which the list sorts and filters by, says the same in SQL."""
        stamps = [self.table.data_modified, self.table.metadata_modified]
        return max((stamp for stamp in stamps if stamp), default=None)

    @property
    def data_only(self) -> bool:
        """Whether only the data half is known, so a metadata edit before
        recording began may be later than the date shown."""
        return bool(self.table.data_modified and not self.table.metadata_modified)

    @property
    def modified_note(self) -> str:
        """What the Modified cell explains on hover and to a screen reader:
        why the date may be early, or why there is none."""
        if self.modified is None:
            return UNKNOWN_NOTE
        return DATA_ONLY_NOTE if self.data_only else ""

    @property
    def shown_topics(self) -> list:
        return self.topics[:TOPICS_SHOWN]

    @property
    def more_topics(self) -> list:
        return self.topics[TOPICS_SHOWN:]


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
            checks = publish_checks(table)
            live = passes(checks)
            if table.publishable is not None and table.publishable != live:
                # something wrote metadata past api.actions.set_table_metadata
                logger.warning(
                    "publish_gate_disagreement table=%s stored=%s live=%s",
                    table.name,
                    str(table.publishable).lower(),
                    str(live).lower(),
                )
            result.append(
                TableRow(
                    table=table,
                    status=status,
                    embargo_until=table.embargo_until,
                    direct=direct_level >= WRITE_PERM,
                    organizations=[name for name, _ in organizations],
                    level=max([direct_level] + [level for _, level in organizations]),
                    checks=checks,
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
