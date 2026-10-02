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
- ``TABLES``: the tab's ``login.listing.Listing``.
- ``table_rows``: one page of Tables as ``TableRow`` objects, with the
  embargo read in the page query and the Access cell in two more queries for
  the whole page, whatever its size.
"""  # noqa: 501

from dataclasses import dataclass, field
from datetime import datetime

from django.db.models import F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce, Lower, Now, NullIf

from dataedit.models import Embargo, Table
from login.listing import Choice, Filter, Listing, Segment, Sort
from login.models import GroupPermission, UserPermission
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM

# The Table roles by level. "Admin" rather than "Table admin" because the
# row is always about one Table.
ROLE_LABELS = {
    WRITE_PERM: "Data editor",
    DELETE_PERM: "Data maintainer",
    ADMIN_PERM: "Admin",
}

DRAFT, PUBLISHED, EMBARGOED = "draft", "published", "embargoed"

# What the Table column shows and sorts by: the title, or the technical name
# for a Table without one. Lower-cased for sorting, so case does not split
# the alphabet in two.
DISPLAYED_TITLE = Lower(Coalesce(NullIf(F("human_readable_name"), Value("")), "name"))


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


def _search(queryset, text):
    return queryset.filter(
        Q(name__icontains=text) | Q(human_readable_name__icontains=text)
    )


TABLES = Listing(
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
    sorts=(
        Sort("table", "Table", DISPLAYED_TITLE),
        # ascending is "least done first": drafts before published Tables
        Sort("status", "Status", F("is_publish")),
    ),
    # Interim default until the Modified column lands (#2557), which makes
    # "-modified" the default.
    default_sort="table",
    tiebreak=(DISPLAYED_TITLE.asc(), F("pk").asc()),
)


@dataclass
class TableRow:
    """What one row of the list says about one Table."""

    table: Table
    status: str
    embargo_until: datetime = None
    direct: bool = False
    organizations: list = field(default_factory=list)
    level: int = WRITE_PERM

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


def table_rows(user):
    """The ``rows`` callable for ``TABLES.page``: a page of Tables as
    ``TableRow`` objects, in three queries for the page."""

    def rows(page_queryset):
        active_embargo = Embargo.objects.filter(
            table=OuterRef("pk"), date_ended__gt=Now()
        ).order_by("-date_ended")
        tables = list(
            page_queryset.annotate(
                embargo_until=Subquery(active_embargo.values("date_ended")[:1])
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
            result.append(
                TableRow(
                    table=table,
                    status=status,
                    embargo_until=table.embargo_until,
                    direct=direct_level >= WRITE_PERM,
                    organizations=[name for name, _ in organizations],
                    level=max([direct_level] + [level for _, level in organizations]),
                )
            )
        return result

    return rows
