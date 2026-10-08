"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The members drawer of the datasets tab (#2625, spec #2613): what it reads
about one of the user's own Datasets. The writes are the Dataset action
service's (``members_add`` / ``members_remove``); nothing here writes.

- ``member_page``: every member, ``PAGE_SIZE`` per page, searchable by title
  and name, each with its status and whether the user could add it back
  after removing it. That last answer is the curation rule
  (``assignable_tables``) read once for the page, whatever it holds.
- ``candidate_page``: the add search over ``assignable_tables(user)``, paged
  rather than capped. Before anything is typed it lists the user's own
  Tables (those they hold Data editor or more on), the most common addition.
- ``lost_member``: the same answer for one member, asked again when a
  removal arrives, because the page that offered it may be stale.
- ``own_member_count``: how many members the user holds Data editor or more
  on, which is what the tables tab can reach (its hand-off).
- ``gate_needs``: what a draft still needs to pass ``DATASET_GATE``.

A drawer page costs the same at 25 members and at 2,500: two queries for the
members (count and page), one for the "add it back" read, two for the add
search, one for the hand-off count and, on a draft, the gate's two checks
(``login/tests/test_dataset_members.py`` pins the number).
"""  # noqa: 501

from dataclasses import dataclass

from django.db.models import Exists, F, OuterRef, Q, Value
from django.db.models.functions import Coalesce, Lower, Now, NullIf

from api.services.dataset_creation import assignable_tables
from dataedit.models import Dataset, Embargo, Table
from dataedit.publish_gate import DATASET_GATE, publish_checks
from login.tables_tab import DRAFT, accessible_tables, table_status

# Members and add-search results per page.
PAGE_SIZE = 25

# What the drawer's gate line says a draft needs, by ``DATASET_GATE``'s check
# name. A Topic arrives with a member too (``assign_table`` seeds the
# member's), so the topic line names both ways.
GATE_NEEDS = {
    "members": "add at least one table",
    "topics": "choose at least one topic (Edit…, or add a table that has one)",
}

# The Tables column's title order: the human-readable name, or the technical
# one where there is none, case-insensitive; the name breaks ties.
_TITLE = Lower(Coalesce(NullIf(F("human_readable_name"), Value("")), F("name")))
_ORDER = (_TITLE.asc(), F("name").asc())


def _embargoed():
    return Exists(Embargo.objects.filter(table_id=OuterRef("pk"), date_ended__gt=Now()))


def _matching(tables, search):
    if not search:
        return tables
    return tables.filter(
        Q(name__icontains=search) | Q(human_readable_name__icontains=search)
    )


def _page_number(raw, total) -> int:
    """``raw`` as a page within ``total`` results: a page past the end shows
    the last one, anything unreadable the first."""
    pages = max(1, -(-total // PAGE_SIZE))
    try:
        number = int(raw)
    except (TypeError, ValueError):
        number = 1
    return min(max(number, 1), pages)


@dataclass(frozen=True)
class Slice:
    """One page of a drawer list: ``rows``, how many match (``total``), the
    page shown and the search it answers."""

    rows: list
    total: int
    page: int
    search: str

    @property
    def pages(self) -> int:
        return max(1, -(-self.total // PAGE_SIZE))

    @property
    def previous(self):
        return self.page - 1 if self.page > 1 else None

    @property
    def next(self):
        return self.page + 1 if self.page < self.pages else None


@dataclass(frozen=True)
class MembersSlice(Slice):
    """A page of members; ``all`` counts every member, searched or not."""

    all: int = 0


@dataclass(frozen=True)
class MemberRow:
    """One member as the drawer lists it. ``lost`` says that the user could
    not add it back after removing it (a draft or embargoed Table they hold
    no Data editor role on): its Remove asks first."""

    table: Table
    status: str
    lost: bool

    @property
    def title(self) -> str:
        return self.table.human_readable_name or self.table.name

    @property
    def lost_while(self) -> str:
        """What the question says it would stay while: "a draft",
        "embargoed"."""
        return "a draft" if self.status == DRAFT else "embargoed"


@dataclass(frozen=True)
class CandidateRow:
    """One Table the add search offers; ``member`` when it is in the Dataset
    already ("Already in")."""

    table: Table
    status: str
    member: bool

    @property
    def title(self) -> str:
        return self.table.human_readable_name or self.table.name


def member_page(user, dataset: Dataset, search="", page=None) -> MembersSlice:
    """One page of ``dataset``'s members by title, narrowed by ``search``
    over title and name. Three queries, four with a search: the count of all
    members, the count of the matching ones when searching, the page, and the
    curation rule for the page's Tables (``MemberRow.lost``)."""
    members = Table.objects.filter(datasets=dataset)
    every = members.count()
    matching = _matching(members, search)
    total = matching.count() if search else every
    number = _page_number(page, total)
    start = (number - 1) * PAGE_SIZE
    tables = list(
        matching.annotate(embargoed=_embargoed()).order_by(*_ORDER)[
            start : start + PAGE_SIZE
        ]
    )
    addable = set(
        assignable_tables(user)
        .filter(pk__in=[table.pk for table in tables])
        .values_list("pk", flat=True)
    )
    rows = [
        MemberRow(
            table=table,
            status=table_status(table.is_publish, table.embargoed),
            lost=table.pk not in addable,
        )
        for table in tables
    ]
    return MembersSlice(rows=rows, total=total, page=number, search=search, all=every)


def candidate_page(user, dataset: Dataset, search="", page=None) -> Slice:
    """One page of the Tables the user may add to ``dataset``
    (``assignable_tables``), by title: those matching ``search`` over title
    and name, or, with nothing typed, the user's own. Members stay in the
    results and read "Already in". Two queries: the count and the page."""
    pool = Table.objects.filter(pk__in=assignable_tables(user).values("pk"))
    if search:
        pool = _matching(pool, search)
    else:
        pool = pool.filter(pk__in=accessible_tables(user).values("pk"))
    total = pool.count()
    number = _page_number(page, total)
    start = (number - 1) * PAGE_SIZE
    member = Dataset.tables.through.objects.filter(
        dataset_id=dataset.pk, table_id=OuterRef("pk")
    )
    tables = pool.annotate(embargoed=_embargoed(), member=Exists(member)).order_by(
        *_ORDER
    )[start : start + PAGE_SIZE]
    rows = [
        CandidateRow(
            table=table,
            status=table_status(table.is_publish, table.embargoed),
            member=table.member,
        )
        for table in tables
    ]
    return Slice(rows=rows, total=total, page=number, search=search)


def lost_member(user, dataset: Dataset, name) -> MemberRow:
    """The member ``name`` of ``dataset`` as a ``MemberRow`` when the user
    could not add it back after removing it, else None (not a member, or one
    they could add again). Two queries."""
    table = dataset.tables.filter(name=name).annotate(embargoed=_embargoed()).first()
    if table is None or assignable_tables(user).filter(pk=table.pk).exists():
        return None
    return MemberRow(table, table_status(table.is_publish, table.embargoed), lost=True)


def own_member_count(user, dataset: Dataset) -> int:
    """How many of ``dataset``'s members the user holds Data editor or more
    on, directly or through an Organization: what the tables tab lists of
    them. One query."""
    return dataset.tables.filter(pk__in=accessible_tables(user).values("pk")).count()


def gate_needs(dataset: Dataset) -> list:
    """What a draft still needs to pass ``DATASET_GATE``, in the gate's order
    (``GATE_NEEDS``); nothing for a published Dataset, whose state no member
    change alters. Two queries for a draft, none otherwise."""
    if dataset.is_published:
        return []
    return [
        GATE_NEEDS[check.name]
        for check in publish_checks(dataset, DATASET_GATE)
        if not check.passed
    ]
