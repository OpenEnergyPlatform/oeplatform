"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The datasets tab of the profile dashboard (spec #2613): which Datasets a user
sees there, how the list filters and sorts, and what each row says.

- ``own_datasets``: the user's own Datasets, drafts and published, by
  creator. A column test, so the list joins nothing and needs no
  ``distinct()``: an annotation or a sort cannot multiply a row.
- ``datasets_listing``: the tab's ``login.listing.Listing`` for one viewer.
  The Topic and Tag options are scoped to that viewer's own Datasets.
- the filters: Search, Topic and Tag, and behind "More filters" Created and
  Modified, each one declaration. Topic is any of the chosen Topics; Tag is
  every chosen tag, each carried by some member (not necessarily the same
  one), the public dataset list's rule. Every clause is a primary-key
  subquery over a link table, never a join. Tags stay on their Tables:
  nothing is copied onto the Dataset.
- ``dataset_rows``: one page of Datasets as ``DatasetRow`` objects. The
  member count and the popover's draft and embargoed counts ride in the page
  query as subqueries; the members the popover names come from one windowed
  query capped at ``MEMBERS_SHOWN`` per Dataset, and the Topics from one
  prefetch, so a page costs the same whether a Dataset holds 3 members or
  2,500.

A page through htmx costs 6 queries: the session and the user, the faceted
segment aggregate, the page, the member titles and the Topics. Naming the
Topic or the Tag filter adds its option source, one query each, so 8 with
both (``login/tests/test_datasets_tab.py`` pins both numbers).

Modified is ``Dataset.modified_at``, a Modification of the Dataset itself
(its description, Topics and membership), never of its member Tables. It is
the default sort, newest first; a Dataset whose changes were never recorded
(NULL) sorts last in both directions and matches no Modified range. Created
is ``created_at``, always known.
"""  # noqa: 501

from dataclasses import dataclass, field
from datetime import datetime
from functools import cache

from django.db.models import (
    Count,
    Exists,
    F,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
    Window,
)
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce, Lower, Now, NullIf, RowNumber

from dataedit.models import Dataset, Embargo, Table, Tag, Topic
from login.listing import (
    NULLS_LAST,
    NULLS_LOWEST,
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
from login.tables_tab import DRAFT, PUBLISHED, TOPICS_SHOWN, table_status
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

# How many members the Tables popover names before "and n more". The tables
# tab's bulk "Add to dataset…" adds up to 2,500 Tables at once, so the cap is
# in the query, not in the template.
MEMBERS_SHOWN = 10

# What the Dataset column shows and sorts by: the title, or the technical
# name for a Dataset without one, lower-cased so that case does not split the
# alphabet in two.
DISPLAYED_TITLE = Lower(
    Coalesce(NullIf(KeyTextTransform("title", "metadata"), Value("")), F("name"))
)

# What the Modified cell says when no change was recorded: a Dataset older
# than the field (dataedit.0058) reads it until its next change.
MODIFIED_UNKNOWN_NOTE = (
    "Not changed since the platform began recording changes to datasets."
)


def _memberships():
    return Dataset.tables.through.objects


def own_datasets(user):
    """The Datasets ``user`` created, drafts and published."""
    return Dataset.objects.filter(creator=user)


def _active_embargo(table_ref):
    return Embargo.objects.filter(table_id=table_ref, date_ended__gt=Now())


def _member_count(*conditions):
    """How many members of the outer Dataset meet ``conditions``, as one
    ``Count`` in a subquery, so it joins nothing into the outer query."""
    members = (
        _memberships()
        .filter(dataset_id=OuterRef("pk"), *conditions)
        .order_by()
        .values("dataset_id")
        .annotate(count=Count("table_id"))
        .values("count")
    )
    return Coalesce(Subquery(members[:1]), Value(0))


# The Tables column's number, and what its sort orders by.
MEMBER_COUNT = _member_count()
# The popover's mix line. A member is embargoed when it is published and an
# embargo on it is still running, as on the tables tab: a draft is a draft.
DRAFT_MEMBER_COUNT = _member_count(Q(table__is_publish=False))
EMBARGOED_MEMBER_COUNT = _member_count(
    Q(table__is_publish=True), Exists(_active_embargo(OuterRef("table_id")))
)


def _search(queryset, text):
    return queryset.filter(
        Q(name__icontains=text)
        | Q(metadata__title__icontains=text)
        | Q(metadata__description__icontains=text)
    )


def _topic_links():
    return Dataset.topics.through.objects


def topic_options(user) -> list:
    """The Topics on the user's own Datasets. A Dataset never holds the draft
    pseudo-topic, and it is never offered. One query."""
    names = (
        _topic_links()
        .filter(dataset__creator=user)
        .exclude(topic_id=PSEUDO_TOPIC_DRAFT)
        .order_by("topic_id")
        .values_list("topic_id", flat=True)
        .distinct()
    )
    return [Option(name, name) for name in names]


def _topics(queryset, names):
    """Any of the chosen Topics, the Dataset's own."""
    links = _topic_links().filter(topic_id__in=names).values("dataset_id")
    return queryset.filter(pk__in=links)


def _tag_links():
    return Table.tags.through.objects


def tag_options(user) -> list:
    """The tags on the members of the user's own Datasets, whoever holds the
    member: a stranger's draft member contributes its tags, as its title does
    to the Tables popover. Keyed by the tag's normalised name, the tables
    tab's key. One query."""
    members = _memberships().filter(dataset__creator=user).values("table_id")
    tags = (
        Tag.objects.filter(
            pk__in=_tag_links().filter(table_id__in=members).values("tag_id")
        )
        .order_by(Lower("name"), "pk")
        .values_list("pk", "name")
    )
    return [Option(pk, name) for pk, name in tags]


def _tags(queryset, keys):
    """Every chosen tag, each carried by some member: one subquery over the
    membership table per tag, ANDed. A join would multiply rows under the
    member-count sort."""
    for key in keys:
        tagged = _tag_links().filter(tag_id=key).values("table_id")
        holders = _memberships().filter(table_id__in=tagged).values("dataset_id")
        queryset = queryset.filter(pk__in=holders)
    return queryset


def datasets_listing(user) -> Listing:
    """The datasets tab's list as ``user`` sees it."""
    return Listing(
        singular="dataset",
        plural="datasets",
        filters=(
            Filter("search", lambda raw: raw.strip() or None, _search, label="Search"),
            ChoiceFilter(
                "topics",
                "Topic",
                cache(lambda: topic_options(user)),
                _topics,
                multiple=True,
                hint="any of the ticked",
            ),
            ChoiceFilter(
                "tags",
                "Tag",
                cache(lambda: tag_options(user)),
                _tags,
                multiple=True,
                hint="all of the ticked",
            ),
            RangeFilter(
                "created",
                "Created",
                dates_within(F("created_at"), "created_range"),
                more=True,
            ),
            RangeFilter(
                "modified",
                "Modified",
                dates_within(F("modified_at"), "modified_range"),
                more=True,
            ),
        ),
        segment=Segment(
            "status",
            "All",
            (
                Choice(DRAFT, "Draft", Q(published_at__isnull=True)),
                Choice(PUBLISHED, "Published", Q(published_at__isnull=False)),
            ),
        ),
        # Status sorts on the publication date, so it is also the "published
        # since" sort: ascending puts drafts first, then the longest
        # published; descending the most recent first, drafts last.
        sorts=(
            Sort("dataset", "Dataset", DISPLAYED_TITLE, "A to Z", "Z to A"),
            Sort(
                "status",
                "Status",
                F("published_at"),
                "drafts first",
                "recently published first",
                nulls=NULLS_LOWEST,
            ),
            Sort("tables", "Tables", MEMBER_COUNT, "fewest first", "most first"),
            Sort(
                "modified",
                "Modified",
                F("modified_at"),
                "oldest first",
                "newest first",
                nulls=NULLS_LAST,
            ),
            Sort("created", "Created", F("created_at"), "oldest first", "newest first"),
        ),
        default_sort="-modified",
        tiebreak=(DISPLAYED_TITLE.asc(), F("pk").asc()),
    )


@dataclass(frozen=True)
class Member:
    """A member Table as the Tables popover names it."""

    name: str
    title: str
    status: str


@dataclass
class DatasetRow:
    """What one row of the list says about one Dataset."""

    dataset: Dataset
    member_count: int = 0
    draft_members: int = 0
    embargoed_members: int = 0
    members: list = field(default_factory=list)
    topics: list = field(default_factory=list)

    @property
    def key(self) -> str:
        """What the row's and its cells' ids are built from
        (``list_region.html``)."""
        return str(self.dataset.pk)

    @property
    def name(self) -> str:
        """What a selection and an action carry for this row."""
        return self.dataset.name

    @property
    def title(self) -> str:
        return self.dataset.metadata.get("title") or self.dataset.name

    @property
    def has_title(self) -> bool:
        """Whether a title is shown, so the technical name goes beneath it
        rather than being shown twice."""
        return bool(self.dataset.metadata.get("title"))

    @property
    def status(self) -> str:
        return PUBLISHED if self.dataset.is_published else DRAFT

    @property
    def is_draft(self) -> bool:
        """Whether an empty Tables or Topics cell says it is needed to
        publish: the gate judges the step to published only."""
        return not self.dataset.is_published

    @property
    def published_at(self) -> datetime:
        return self.dataset.published_at

    @property
    def mix(self) -> str:
        """The popover's neutral summary, naming only the parts there are:
        "2 drafts · 1 embargoed"."""
        parts = []
        if self.draft_members:
            noun = "draft" if self.draft_members == 1 else "drafts"
            parts.append(f"{self.draft_members} {noun}")
        if self.embargoed_members:
            parts.append(f"{self.embargoed_members} embargoed")
        return " · ".join(parts)

    @property
    def count_label(self) -> str:
        """The Tables cell: "1 table", "2,500 tables"."""
        noun = "table" if self.member_count == 1 else "tables"
        return f"{self.member_count:,} {noun}"

    @property
    def more_members(self) -> int:
        """How many members the popover does not name."""
        return self.member_count - len(self.members)

    @property
    def more_label(self) -> str:
        """The popover's last line: "and 2,490 more"."""
        return f"and {self.more_members:,} more"

    @property
    def shown_topics(self) -> list:
        return self.topics[:TOPICS_SHOWN]

    @property
    def more_topics(self) -> list:
        return self.topics[TOPICS_SHOWN:]

    # What the shared date cells (``cells/modified.html``, ``created.html``)
    # read. A Dataset has one Modified stamp, not a data and a metadata half.

    @property
    def modified(self) -> datetime:
        return self.dataset.modified_at

    data_only = False

    @property
    def modified_note(self) -> str:
        return "" if self.modified else MODIFIED_UNKNOWN_NOTE

    @property
    def created(self) -> datetime:
        return self.dataset.created_at

    created_note = ""


def member_titles(dataset_ids) -> dict:
    """The first ``MEMBERS_SHOWN`` members of each Dataset in
    ``dataset_ids``, by title then name, as ``Member`` lists keyed by the
    Dataset's pk. One query: a row number per Dataset, cut in SQL, so a
    Dataset of 2,500 members reads ten."""
    title = Lower(
        Coalesce(NullIf(F("table__human_readable_name"), Value("")), "table__name")
    )
    rows = (
        _memberships()
        .filter(dataset_id__in=dataset_ids)
        .annotate(
            position=Window(
                RowNumber(),
                partition_by=[F("dataset_id")],
                order_by=[title.asc(), F("table__name").asc()],
            ),
            embargoed=Exists(_active_embargo(OuterRef("table_id"))),
        )
        .filter(position__lte=MEMBERS_SHOWN)
        .order_by("dataset_id", "position")
        .values_list(
            "dataset_id",
            "table__name",
            "table__human_readable_name",
            "table__is_publish",
            "embargoed",
        )
    )
    members = {}
    for dataset_id, name, human_name, published, embargoed in rows:
        members.setdefault(dataset_id, []).append(
            Member(name, human_name or name, table_status(published, embargoed))
        )
    return members


def dataset_rows(user):
    """The ``rows`` callable for ``datasets_listing(user).page``: a page of
    Datasets as ``DatasetRow`` objects, in three queries for the page."""

    def rows(page_queryset):
        topics = Topic.objects.exclude(name=PSEUDO_TOPIC_DRAFT).order_by("name")
        datasets = list(
            page_queryset.annotate(
                member_count=MEMBER_COUNT,
                draft_members=DRAFT_MEMBER_COUNT,
                embargoed_members=EMBARGOED_MEMBER_COUNT,
            ).prefetch_related(Prefetch("topics", queryset=topics))
        )
        members = member_titles([dataset.pk for dataset in datasets])
        return [
            DatasetRow(
                dataset=dataset,
                member_count=dataset.member_count,
                draft_members=dataset.draft_members,
                embargoed_members=dataset.embargoed_members,
                members=members.get(dataset.pk, []),
                topics=[topic.name for topic in dataset.topics.all()],
            )
            for dataset in datasets
        ]

    return rows
