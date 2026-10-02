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
A filter is one of two kinds. A ``Filter`` takes free text (a search). A
``ChoiceFilter`` takes one value, or several comma-joined ones, out of a set of
``Option`` objects; the option source may be a function of the viewer, and it is
called only when the request names that filter or the filter bar is rendered,
so a filter nobody uses costs no query. A value that is not among the options
(an Organization the user left, a deleted Dataset, an unknown tag) is ignored
and kept in ``ListState.stale``: it narrows nothing, it shows as a muted chip,
and it stays in every link the page builds until it is dismissed or reset, so
the chip does not vanish on the next unrelated click.

``Listing.matching`` narrows a base queryset by every active filter, which is
the one statement of what the URL selects: the list, its counts and (later)
"select all matching" all read it. ``Listing.page`` turns a base queryset and a
request's query string into one ``ListPage``. Its ``rows`` argument turns one page of model instances into
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

import json
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlencode

from django.db.models import Count, Q, QuerySet

PAGE_SIZE = 25


@dataclass(frozen=True)
class Reading:
    """What one filter made of a query string.

    ``value`` is what ``apply`` receives, None for "not filtering". ``raw`` is
    what the URL keeps for the filter, stale values included, None when the
    URL does not name it. ``stale`` lists the given values that no longer
    apply.
    """

    value: Any = None
    raw: Any = None
    stale: tuple = ()


@dataclass(frozen=True)
class ChipSpec:
    """A chip a filter asks for: its text, what the filter's parameter reads
    once the chip is removed (None clears it), and whether it is stale."""

    text: str
    remaining: Any = None
    stale: bool = False


@dataclass(frozen=True)
class Filter:
    """A free-text URL parameter that narrows the list.

    ``parse`` turns the raw parameter into a value, or None for "not
    filtering". ``apply`` narrows a queryset by a parsed value; ``serialize``
    writes the value back into the URL. Free text has no options, so it is
    never stale.
    """

    param: str
    parse: Callable[[str], Any]
    apply: Callable[[QuerySet, Any], QuerySet]
    serialize: Callable[[Any], str] = str
    label: str = ""
    more: bool = False

    def read(self, query) -> Reading:
        value = self.parse(query.get(self.param, ""))
        if value is None:
            return Reading()
        return Reading(value, self.serialize(value))

    def chips(self, reading: Reading) -> list:
        return [ChipSpec(f"{self.label}: \u201c{reading.raw}\u201d")]


@dataclass(frozen=True)
class Option:
    """One value a ``ChoiceFilter`` offers: what the URL carries, what the
    control shows, the group it is listed under, and what its chip says when
    "<filter label>: <label>" would read badly."""

    value: str
    label: str
    group: str = ""
    chip: str = ""


@dataclass(frozen=True)
class ChoiceFilter:
    """A URL parameter whose values come out of a set of ``Option`` objects.

    ``options`` is a sequence, or a function returning one; a function is
    called only when the request names this filter (to tell known values from
    stale ones, and to label the chips) or when the bar is rendered, so wrap
    it in ``functools.cache`` when it queries. Single-valued unless
    ``multiple``: then the values are comma-joined, the repeated form
    (``?tags=a&tags=b``) is read too, and ``apply`` receives a list.
    ``apply`` only ever receives known values. ``blank`` is what the control
    says when nothing is chosen, ``hint`` how several values combine, and
    ``more`` puts the control behind "More filters".
    """

    param: str
    label: str
    options: Any
    apply: Callable[[QuerySet, Any], QuerySet]
    multiple: bool = False
    more: bool = False
    blank: str = ""
    hint: str = ""

    def choices(self) -> list:
        return list(self.options() if callable(self.options) else self.options)

    def option(self, value):
        return next((o for o in self.choices() if o.value == value), None)

    def given(self, query) -> list:
        """The values the query names, in its order, without repeats."""
        if self.multiple:
            raws = query.getlist(self.param) if hasattr(query, "getlist") else []
            raws = raws or [query.get(self.param, "")]
            parts = [part.strip() for raw in raws for part in raw.split(",")]
        else:
            parts = [query.get(self.param, "").strip()]
        return list(dict.fromkeys(part for part in parts if part))

    def read(self, query) -> Reading:
        given = self.given(query)
        if not given:
            return Reading()
        known = {option.value for option in self.choices()}
        valid = [value for value in given if value in known]
        stale = tuple(value for value in given if value not in known)
        if self.multiple:
            value = valid or None
        else:
            value = valid[0] if valid else None
        return Reading(value, ",".join(given) if self.multiple else given[0], stale)

    def chips(self, reading: Reading) -> list:
        given = reading.raw.split(",") if self.multiple else [reading.raw]

        def without(value):
            if not self.multiple:
                return None
            return ",".join(v for v in given if v != value) or None

        if reading.value is None:
            valid = []
        else:
            valid = reading.value if self.multiple else [reading.value]
        chips = []
        for value in valid:
            option = self.option(value)
            text = option.chip or f"{self.label}: {option.label}"
            chips.append(ChipSpec(text, without(value)))
        for value in reading.stale:
            chips.append(
                ChipSpec(
                    f"Filter \u2039{self.label}: {value}\u203a no longer applies",
                    without(value),
                    stale=True,
                )
            )
        return chips


@dataclass(frozen=True)
class ControlOption:
    value: str
    label: str
    group: str
    selected: bool


@dataclass(frozen=True)
class FilterControl:
    """What the filter bar renders for one ``ChoiceFilter``."""

    param: str
    label: str
    blank: str
    hint: str
    multiple: bool
    more: bool
    options: list


@dataclass(frozen=True)
class Chip:
    """One removable chip: an active filter value, or a stale one."""

    id: str
    text: str
    url: str
    stale: bool = False


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
    """A sortable column: its URL key, and the expression it orders by.

    ``nulls_last`` puts rows whose value is unknown (NULL) at the end in both
    directions, rather than wherever the database's default puts them, which
    flips with the direction.
    """

    key: str
    label: str
    expression: Any
    nulls_last: bool = False

    def order(self, descending: bool) -> list:
        nulls = {"nulls_last": True} if self.nulls_last else {}
        if descending:
            return [self.expression.desc(**nulls)]
        return [self.expression.asc(**nulls)]


@dataclass(frozen=True)
class ListState:
    """What the URL says: the active filter values, the sort and the page.

    ``raw`` holds the string each filter keeps in the URL (the segment
    included), in declaration order, stale values included so that every link
    keeps them; ``values`` the parsed ones that apply; ``readings`` what each
    filter made of the query, for the chips.
    """

    listing: "Listing"
    raw: dict
    values: dict
    sort: str
    page: int
    readings: dict = field(default_factory=dict)

    @property
    def stale(self) -> list:
        """``(param, value)`` for every given value that no longer applies."""
        return [
            (param, value)
            for param, reading in self.readings.items()
            for value in reading.stale
        ]

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
        # commas stay as they are: multi-valued filters are comma-joined
        return f"{path}?{urlencode(params, safe=',')}" if params else path


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
    def chips(self) -> list:
        """A chip for every active filter value, then one for every stale
        value, each linking to this state without it. The ids are by
        position, so after a removal focus lands on the chip that moved into
        its place."""
        active, stale = [], []
        for f in self.listing.filters:
            reading = self.state.readings.get(f.param)
            if reading is None:
                continue
            for spec in f.chips(reading):
                (stale if spec.stale else active).append((f.param, spec))
        chips = []
        for n, (param, spec) in enumerate(active + stale):
            chips.append(
                Chip(
                    f"chip-{n}",
                    spec.text,
                    self.state.url(self.path, **{param: spec.remaining}),
                    spec.stale,
                )
            )
        return chips

    @property
    def controls(self) -> list:
        """The bar's control for every ``ChoiceFilter``, its options marked
        with what this state has chosen. Reading it calls every option
        source, so only a whole page does."""
        controls = []
        for f in self.listing.filters:
            if not isinstance(f, ChoiceFilter):
                continue
            chosen = self.state.values.get(f.param)
            chosen = set(chosen) if f.multiple and chosen else {chosen}
            controls.append(
                FilterControl(
                    f.param,
                    f.label,
                    f.blank or f"{f.label}: any",
                    f.hint,
                    f.multiple,
                    f.more,
                    [
                        ControlOption(o.value, o.label, o.group, o.value in chosen)
                        for o in f.choices()
                    ],
                )
            )
        return controls

    @property
    def more_count(self) -> int:
        """How many filters behind "More filters" apply."""
        return sum(
            1 for f in self.listing.filters if f.more and f.param in self.state.values
        )

    @property
    def filters_json(self) -> str:
        """What each filter keeps in the URL, for the bar outside the region
        to follow after a swap (a chip removed, a Reset)."""
        segment = self.listing.segment.param
        return json.dumps({p: v for p, v in self.state.raw.items() if p != segment})

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
        match = (" matches" if one else " match") if self.state.values else ""
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
        raw, values, readings = {}, {}, {}
        for f in self.filters:
            reading = f.read(query)
            if reading.raw is None:
                continue
            readings[f.param] = reading
            raw[f.param] = reading.raw
            if reading.value is not None:
                values[f.param] = reading.value
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
        return ListState(self, raw, values, sort, page, readings)

    def _filtered(self, base: QuerySet, state: ListState) -> QuerySet:
        """``base`` narrowed by every active filter but the segment."""
        for f in self.filters:
            if f.param in state.values:
                base = f.apply(base, state.values[f.param])
        return base

    def matching(self, base: QuerySet, query) -> QuerySet:
        """Every row of ``base`` the query selects, across all pages: the
        same filters, parsed the same way, as the list and its counts."""
        state = self.state(query)
        narrowed = self._filtered(base, state)
        selected = state.values.get(self.segment.param)
        if selected is not None:
            narrowed = narrowed.filter(self.segment.condition(selected))
        return narrowed

    def page(
        self, base: QuerySet, query, path: str, rows: Callable[[QuerySet], list] = list
    ) -> ListPage:
        state = self.state(query)

        narrowed = self._filtered(base, state)

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
