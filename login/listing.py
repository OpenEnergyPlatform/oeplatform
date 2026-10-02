"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The list mechanics a profile dashboard tab is built from: filters declared
once, the state they leave in the URL, a segment with faceted counts, sorting
with tie-breakers, and paging.

Nothing here knows about Tables. A tab is a ``Listing``, which declares

- its ``filters``, each a URL parameter with its parsing and its queryset
  clause;
- one ``segment``: a filter shown as buttons that carry counts;
- its ``sorts`` and the ``tiebreak`` every sort ends with, so that paging is
  deterministic;
``Listing.page`` turns a base queryset and a request's query string into one
``ListPage``. Its ``rows`` argument turns one page of model instances into
rows, which is where a tab attaches, in a fixed number of queries, what one
query per row would otherwise fetch. Every link the page offers (segment, sort headers, pager,
Reset) is built by ``ListState.url``, so the URL rules hold in one place:

- stable identifiers only, never labels;
- a default is never written: a bare URL is the unfiltered list in the
  default order;
- any filter change returns to page 1;
- an unknown value is ignored, never refused.

The segment's counts are faceted: one aggregate over every active filter
except the segment's own, so ``All (n)`` says how the filtered set splits
before the user narrows it. The total of the selected segment is read from
the same aggregate, so a page costs one aggregate plus one slice whatever the
account size.
"""  # noqa: 501

from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlencode

from django.db.models import Count, Q, QuerySet

PAGE_SIZE = 25


@dataclass(frozen=True)
class Filter:
    """One URL parameter that narrows the list.

    ``parse`` turns the raw parameter into a value, or None for "not
    filtering", which is also the answer for a value that no longer applies.
    ``apply`` narrows a queryset by a parsed value; ``serialize`` writes the
    value back into the URL.
    """

    param: str
    parse: Callable[[str], Any]
    apply: Callable[[QuerySet, Any], QuerySet]
    serialize: Callable[[Any], str] = str


@dataclass(frozen=True)
class Choice:
    """One button of a segment: its URL value, its label and its condition."""

    value: str
    label: str
    condition: Q


@dataclass(frozen=True)
class Segment:
    """A single-valued filter shown as buttons with faceted counts.

    The empty value is the "all" button, and it is the default.
    """

    param: str
    all_label: str
    choices: tuple

    def parse(self, raw):
        return raw if raw in {choice.value for choice in self.choices} else None

    def condition(self, value) -> Q:
        return next(c.condition for c in self.choices if c.value == value)


@dataclass(frozen=True)
class Sort:
    """A sortable column: its URL key, and the expression it orders by."""

    key: str
    label: str
    expression: Any

    def order(self, descending: bool) -> list:
        return [self.expression.desc() if descending else self.expression.asc()]


@dataclass(frozen=True)
class ListState:
    """What the URL says: the active filter values, the sort and the page.

    ``raw`` holds the canonical string of each active filter (the segment
    included), in declaration order; ``values`` the parsed ones.
    """

    listing: "Listing"
    raw: dict
    values: dict
    sort: str
    page: int

    @property
    def sort_key(self) -> str:
        return self.sort.lstrip("-")

    @property
    def descending(self) -> bool:
        return self.sort.startswith("-")

    @property
    def filtered(self) -> bool:
        """Whether any filter other than the segment is active."""
        return any(param != self.listing.segment.param for param in self.raw)

    def url(self, path: str, page=None, sort=None, **filters) -> str:
        """The address of this state with some of it changed.

        A changed filter (None or "" clears it) returns to page 1. Defaults
        are left out, so the bare path is the unfiltered first page.
        """
        raw = dict(self.raw)
        for param, value in filters.items():
            if value in (None, ""):
                raw.pop(param, None)
            else:
                raw[param] = value
        if filters:
            page = 1
        params = [(p, raw[p]) for p in self.listing.params if p in raw]
        sort = self.sort if sort is None else sort
        if sort != self.listing.default_sort:
            params.append(("sort", sort))
        page = self.page if page is None else page
        if page > 1:
            params.append(("page", str(page)))
        return f"{path}?{urlencode(params)}" if params else path


@dataclass(frozen=True)
class SegmentLink:
    id: str
    label: str
    count: int
    url: str
    active: bool


@dataclass(frozen=True)
class SortLink:
    id: str
    label: str
    url: str
    active: bool
    descending: bool

    @property
    def aria_sort(self) -> str:
        if not self.active:
            return ""
        return "descending" if self.descending else "ascending"


@dataclass(frozen=True)
class PagerItem:
    """A page number with its link, or a gap (``number`` None)."""

    number: Any
    url: str = ""
    current: bool = False


@dataclass
class ListPage:
    """One rendered state of a list: rows, counts, paging and every link."""

    listing: "Listing"
    state: ListState
    path: str
    rows: list
    counts: dict
    total: int
    number: int
    num_pages: int
    has_any: bool
    segment_links: list = field(default_factory=list)
    sort_links: dict = field(default_factory=dict)

    @property
    def start(self) -> int:
        return (self.number - 1) * self.listing.page_size + 1 if self.total else 0

    @property
    def end(self) -> int:
        return min(self.number * self.listing.page_size, self.total)

    @property
    def url(self) -> str:
        """The canonical address of what is shown (page clamped)."""
        return self.state.url(self.path, page=self.number)

    @property
    def reset_url(self) -> str:
        """Every filter and the segment cleared; the sort kept."""
        return self.state.url(self.path, **{p: None for p in self.state.raw})

    @property
    def range_text(self) -> str:
        """ "176–200 of 2,068"."""
        return f"{self.start:,}–{self.end:,} of {self.total:,}"

    @property
    def summary(self) -> str:
        if not self.total:
            return f"No {self.listing.plural}"
        noun = self.listing.singular if self.total == 1 else self.listing.plural
        return f"{self.range_text} {noun}"

    @property
    def announcement(self) -> str:
        """What the persistent live region reads after a change."""
        if not self.has_any:
            return f"You have no {self.listing.plural} yet"
        if not self.total:
            return f"No {self.listing.plural} match these filters"
        one = self.total == 1
        noun = self.listing.singular if one else self.listing.plural
        match = (" matches" if one else " match") if self.state.raw else ""
        return f"{self.total:,} {noun}{match}, showing {self.start:,} to {self.end:,}"

    @property
    def pager(self) -> list:
        """``‹ 1 2 … 7 [8] 9 … 83 ›``: first two, neighbours, last two."""
        n, current = self.num_pages, self.number
        shown = sorted(
            {p for p in (1, 2, current - 1, current, current + 1, n - 1, n)}
            & set(range(1, n + 1))
        )
        items, previous = [], 0
        for number in shown:
            if number - previous > 1:
                items.append(PagerItem(None))
            items.append(
                PagerItem(
                    number,
                    self.state.url(self.path, page=number),
                    number == current,
                )
            )
            previous = number
        return items

    @property
    def previous_url(self) -> str:
        if self.number <= 1:
            return ""
        return self.state.url(self.path, page=self.number - 1)

    @property
    def next_url(self) -> str:
        if self.number >= self.num_pages:
            return ""
        return self.state.url(self.path, page=self.number + 1)


@dataclass(frozen=True)
class Listing:
    """A dashboard tab's list, declared. See the module docstring."""

    singular: str
    plural: str
    filters: tuple
    segment: Segment
    sorts: tuple
    default_sort: str
    tiebreak: tuple
    page_size: int = PAGE_SIZE

    @property
    def params(self) -> list:
        """Every filter parameter, in the order a URL writes them."""
        return [f.param for f in self.filters] + [self.segment.param]

    def _sort(self, key) -> Sort:
        return next(s for s in self.sorts if s.key == key)

    def state(self, query) -> ListState:
        raw, values = {}, {}
        for f in self.filters:
            value = f.parse(query.get(f.param, ""))
            if value is not None:
                values[f.param] = value
                raw[f.param] = f.serialize(value)
        segment_value = self.segment.parse(query.get(self.segment.param, ""))
        if segment_value is not None:
            raw[self.segment.param] = values[self.segment.param] = segment_value

        sort = query.get("sort", "")
        if sort.lstrip("-") not in {s.key for s in self.sorts}:
            sort = self.default_sort

        try:
            page = max(1, int(query.get("page", "1")))
        except ValueError:
            page = 1
        return ListState(self, raw, values, sort, page)

    def page(
        self, base: QuerySet, query, path: str, rows: Callable[[QuerySet], list] = list
    ) -> ListPage:
        state = self.state(query)

        narrowed = base
        for f in self.filters:
            if f.param in state.values:
                narrowed = f.apply(narrowed, state.values[f.param])

        counts = narrowed.aggregate(
            all=Count("pk"),
            **{c.value: Count("pk", filter=c.condition) for c in self.segment.choices},
        )
        selected = state.values.get(self.segment.param)
        if selected is not None:
            narrowed = narrowed.filter(self.segment.condition(selected))
        total = counts[selected or "all"]

        if counts["all"]:
            has_any = True
        elif state.filtered:
            has_any = base.exists()
        else:
            has_any = False

        num_pages = max(1, -(-total // self.page_size))
        number = min(state.page, num_pages)
        page_rows = []
        if total:
            sort = self._sort(state.sort_key)
            offset = (number - 1) * self.page_size
            ordered = narrowed.order_by(*sort.order(state.descending), *self.tiebreak)
            page_rows = rows(ordered[offset : offset + self.page_size])

        page = ListPage(
            listing=self,
            state=state,
            path=path,
            rows=page_rows,
            counts=counts,
            total=total,
            number=number,
            num_pages=num_pages,
            has_any=has_any,
        )
        page.segment_links = [
            SegmentLink(
                f"seg-{value or 'all'}",
                label,
                counts[value or "all"],
                state.url(path, **{self.segment.param: value}),
                (selected or "") == value,
            )
            for value, label in [("", self.segment.all_label)]
            + [(c.value, c.label) for c in self.segment.choices]
        ]
        page.sort_links = {
            s.key: SortLink(
                f"sort-{s.key}",
                s.label,
                state.url(
                    path,
                    page=1,
                    sort=(
                        f"-{s.key}"
                        if state.sort_key == s.key and not state.descending
                        else s.key
                    ),
                ),
                state.sort_key == s.key,
                state.sort_key == s.key and state.descending,
            )
            for s in self.sorts
        }
        return page
