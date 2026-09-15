"""What a dataset link points at, resolved against the platform, per read.

A dataset link holds a name and a URL, and nothing behind either of them is
enforced: the link lives in the graph, its target lives in Postgres, and the
two have different owners. So a citation can outlive the thing it cites, and
this module is where a reader is told so.

**Never block, never collect, resolve on read.** A bundle is a published
research record -- "this scenario used that table" stays true after the table
is gone -- so a dead link is neither removed nor allowed to hold its target
hostage. A collector would falsify the record and would change a bundle its
owner never touched; blocking would let anyone make a stranger's table
undeletable, which inverts the platform's permission model. What is left is to
say, on every read, what the citation means now.

Three consequences of computing rather than storing, all of them the point:

- **Nothing can go stale**, because nothing is kept. This is the line the
  platform's own dataset resources already take -- `Dataset.resource_entries`
  assembles its list live for the same reason.
- **A catalogue reference is a live one.** `ref: table` is the reproducible
  citation; `ref: dataset` is the current one, and a read resolves it to the
  members the catalogue entry has today. That currency is why the coarser
  reference exists at all, so it is reported rather than frozen.
- **The cost is bounded by target kinds, not by links.** Three queries serve a
  bundle with one link and a bundle with fifty: the tables, the catalogue
  entries with their members, and the reviews.

**Resolving is not endorsing.** `resolvable` says the row is there, not that
anybody maintains it -- `Dataset.creator` is nulled when its owner is deleted,
so a live target can be ownerless. And a peer review is keyed by table *name*,
not by a foreign key, so reviews survive their tables; a table that is gone
carries no review here, because it is not in the resolved list at all.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from dataedit.models import Dataset, PeerReview, Table

# The review indicator is three-valued -- finished, in progress, or absent --
# and absent is `None` rather than `False` on purpose. The Open Peer Review
# process postdates most of the data on the platform, so a boolean would read
# as a quality judgement ("not reviewed" looking like "failed") on the great
# majority of links.
REVIEW_FINISHED = "finished"
REVIEW_IN_PROGRESS = "in_progress"


@dataclass(frozen=True)
class Resolution:
    """What one link resolves to right now, as a read reports it.

    ``resolvable`` and ``tables`` are both nullable, and the null means the
    same thing in both: *this server cannot say*. That happens for a link
    pointing at an address this platform has no route for -- the live graph
    holds databus URLs written long before this API -- where `ref` already
    reads back null. Answering `false` there would claim the target had been
    deleted, which is a fabrication rather than an answer.

    ``tables`` is the citation's meaning today: the one table for a table
    reference, the catalogue entry's current members for a dataset reference,
    and an empty list when the named target is gone. Each entry carries its own
    review state, because the review process is per table and there is no such
    thing as a reviewed catalogue entry.
    """

    resolvable: Optional[bool]
    tables: Optional[list]

    def as_meta(self) -> dict:
        """The read-only keys a link body gains from being resolved."""
        return {"resolvable": self.resolvable, "tables": self.tables}


# A link this platform has no route for: not resolvable, not unresolvable.
UNKNOWABLE = Resolution(resolvable=None, tables=None)


def resolve(links: Sequence[tuple]) -> list:
    """Resolve ``(ref, name)`` pairs, in order, in a fixed number of queries.

    Batched rather than per link, because the alternative is a query per
    citation on a public endpoint. Three queries at most, whatever the bundle
    holds: one for the tables named directly, one for the catalogue entries and
    their members together, and one for the reviews of everything the first two
    turned up.

    A name is looked up as it is stored. There is no normalisation and no
    guessing: a table name that no longer exists is simply not found, which is
    exactly what the caller is asking about.
    """
    named_tables = {name for ref, name in links if ref == "table"}
    members = _members_by_dataset({name for ref, name in links if ref == "dataset"})
    existing = _existing_tables(named_tables)
    reviews = _review_states(existing.union(*members.values()))

    def resolved(ref, name):
        if ref == "table":
            return _found(name in existing, [name], reviews)
        if ref == "dataset":
            return _found(name in members, sorted(members.get(name, ())), reviews)
        return UNKNOWABLE

    return [resolved(ref, name) for ref, name in links]


def _found(exists: bool, names: Sequence[str], reviews: dict) -> Resolution:
    """One resolution: whether the named target is there, and what it means.

    The empty list when it is not is deliberate and is not the same as the
    null `UNKNOWABLE` carries -- here the server looked and the target is gone,
    there it never had anywhere to look.
    """
    return Resolution(
        resolvable=exists,
        tables=[_table_entry(name, reviews) for name in names] if exists else [],
    )


def _existing_tables(names: Iterable[str]) -> set:
    names = set(names)
    if not names:
        return set()
    return set(Table.objects.filter(name__in=names).values_list("name", flat=True))


def _members_by_dataset(names: Iterable[str]) -> dict:
    """Which member tables each named catalogue entry has, as it stands.

    Existence and membership in one query: the left join answers both, and a
    catalogue entry with no members comes back as itself with a null member,
    which is how "it exists and is empty" is told apart from "it is gone".
    """
    names = set(names)
    if not names:
        return {}
    members = {}
    rows = Dataset.objects.filter(name__in=names).values_list("name", "tables__name")
    for dataset, table in rows:
        found = members.setdefault(dataset, set())
        if table is not None:
            found.add(table)
    return members


def _review_states(names: Iterable[str]) -> dict:
    """The review state of each of these tables, for the ones that have one.

    A table with several reviews counts as reviewed if any of them finished. A
    finished review is a fact that a later round does not undo, and the
    question a reader is asking -- has this data been through review -- is
    answered `finished` from then on.
    """
    names = set(names)
    if not names:
        return {}
    states = {}
    rows = PeerReview.objects.filter(table__in=names).values_list(
        "table", "is_finished"
    )
    for table, is_finished in rows:
        if is_finished:
            states[table] = REVIEW_FINISHED
        else:
            states.setdefault(table, REVIEW_IN_PROGRESS)
    return states


def _table_entry(name: str, reviews: dict) -> dict:
    return {"name": name, "peer_review": reviews.get(name)}
