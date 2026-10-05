"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The permission service (spec #2551, WF-08): who holds which Table role on a
Table, and every rule about changing that. One module, so the access drawer,
the Table's permission page (#2567) and the REST API (#2570) cannot disagree
about a rule.

- ``ROLES``: the roles a Holder can be given, read off the model's choices
  minus "None", each with its label and one line on what it allows. Nothing
  here assumes which rung is lowest, so a new rung in the model's choices
  needs no change here or in the drawer (it is labelled by the model until
  it is given its own text).
- ``table_access(viewer, table)``: the Table's Holders as ``viewer`` sees
  them (``Access``): users and Organizations with their roles and member
  counts, the viewer's own entries marked, whether the viewer may change
  anything, and which of their Organizations they could still share with.
- ``add``, ``change``, ``remove``, ``leave``: the writes. Each returns a
  ``Change`` (``change`` returns None when the Holder already holds that
  role, and writes nothing), or raises:

  - ``InvalidRequest`` (the request itself is unusable: a role outside
    ``ROLES``, Admin for an Organization, an Organization the viewer is not
    a member of, a user who does not exist);
  - ``NotAllowed`` (the viewer is not a Table admin, or "leaves" a Table on
    which they hold no direct grant);
  - ``LastAdmin`` (the change would leave the Table without a user holding
    direct Admin);
  - ``ConfirmationNeeded`` (the viewer would lose their own Admin, or all
    access, and has not confirmed).

The rules:

- **Admin is granted to users only**, each by name. Every Table admin is an
  equal co-admin: a co-admin may remove the user who uploaded the Table.
- **Organizations stop at Data maintainer** (``ORGANIZATION_CEILING``). An
  Organization grant at Admin from before this rule stays as it is (no
  migration) and may only be lowered or removed.
- **A Table admin shares only with Organizations they are a member of**, at
  any membership level, because a share puts the Table on every member's
  dashboard. Changing or removing an Organization that already holds a role
  needs no membership: that is how an old grant gets cleaned up.
- **Last-admin guard:** a Table keeps at least one user with direct Admin.
  A change that would take the last one away is refused, and that is
  checked BEFORE the self-demotion confirmation, so nobody confirms a change
  that is then refused. A Table that has no such user already (its only
  Admin is an old Organization grant) is not made worse by any change, so
  the guard does not fire there.
- **Self-demotion:** a change that takes the viewer's own Admin, or all of
  their access, away needs one confirmation (``confirmed=True``). Leaving a
  Table always does.
- **Leave this table:** any user may drop their own direct grant, whatever
  its role, under the guard. Access through an Organization is left by
  leaving the Organization.

Who counts as a Table admin is ``table_levels``, the platform's rule stated
set-based: the highest of the user's direct grant and their Organizations'
grants, and Table admin on every Table for a platform admin or a member of
an admin Organization. ``myuser.get_table_permission_level`` states the same
rule for one Table, and the API's permission decorators read that.

Every write holds a row lock on the Table for its checks and its write, so
two admins removing each other at the same moment cannot both pass the
guard. One log line per change, on the ``oeplatform.table_permissions``
logger, once it has committed::

    table_permission_write table=<name> holder=user:<pk>|org:<pk>
        action=add|change|remove|leave before=<level>|- after=<level>|-
        by=<user pk> via=dashboard|table-page|api

``-`` is "no grant". The levels are the stored numbers, so a change can be
undone by hand from the line. No model, no migration: the lines are the
record.
"""  # noqa: 501

import logging
from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import Count

from login.models import (
    GroupPermission,
    Membership,
    Organization,
    TablePermission,
    UserPermission,
    myuser,
)
from login.permissions import ADMIN_PERM, DELETE_PERM, NO_PERM, WRITE_PERM

logger = logging.getLogger("oeplatform.table_permissions")

# What each role is called and allows, by stored level. "Admin" rather than
# "Table admin" because the drawer is always about one Table.
ROLE_TEXT = {
    WRITE_PERM: ("Data editor", "Edits the metadata, adds and changes rows."),
    DELETE_PERM: ("Data maintainer", "Also deletes rows and the table itself."),
    ADMIN_PERM: ("Admin", "Also publishes, unpublishes and decides who has access."),
}

# The highest role an Organization may be given: every member gets it, and
# nobody becomes a Table admin through a group.
ORGANIZATION_CEILING = DELETE_PERM

ADD, CHANGE, REMOVE, LEAVE = "add", "change", "remove", "leave"
USER, ORGANIZATION = "user", "org"

LAST_ADMIN = "This table needs a user with Admin. Give someone else Admin first."
ONLY_ADMINS = "Only Admins can change access."


@dataclass(frozen=True)
class Role:
    level: int
    label: str
    description: str


ROLES = tuple(
    Role(level, *ROLE_TEXT.get(level, (label, "")))
    for level, label in TablePermission.choices
    if level != NO_PERM
)
ROLE_OF = {role.level: role for role in ROLES}
ORGANIZATION_ROLES = tuple(r for r in ROLES if r.level <= ORGANIZATION_CEILING)


def role_label(level) -> str:
    """The role's name, or "No role" for a grant below every role."""
    role = ROLE_OF.get(level)
    return role.label if role else "No role"


class AccessError(Exception):
    """Base of the ways a write can decline. ``message`` is what the user is
    told; nothing was written. A bulk write names the Tables it declined
    for in ``tables``."""

    def __init__(self, message, tables=()):
        super().__init__(message)
        self.message = message
        self.tables = list(tables)


class InvalidRequest(AccessError):
    """The request is unusable as it stands; ``field`` names the input."""

    def __init__(self, message, field=""):
        super().__init__(message)
        self.field = field


class NotAllowed(AccessError):
    """The viewer may not make this change."""


class LastAdmin(AccessError):
    """The change would leave the Table without a user holding direct
    Admin (in a bulk removal: without any Admin at all)."""

    def __init__(self, message=LAST_ADMIN, tables=()):
        super().__init__(message, tables)


class ConfirmationNeeded(AccessError):
    """The change would take the viewer's own Admin, or all their access,
    away. Sent again with ``confirmed=True`` it is made."""


@dataclass
class Holder:
    """One user or Organization holding a role on the Table."""

    kind: str
    pk: int
    name: str
    level: int
    you: bool = False
    members: int = 0
    image: str = ""

    @property
    def key(self) -> str:
        """How a request names this Holder: ``user:<pk>`` or ``org:<pk>``."""
        return f"{self.kind}:{self.pk}"

    @property
    def dom_id(self) -> str:
        """The key as it can stand in an element id."""
        return f"{self.kind}-{self.pk}"

    @property
    def role(self) -> str:
        return role_label(self.level)

    @property
    def has_role(self) -> bool:
        """False for a grant stored below every role ("None")."""
        return self.level in ROLE_OF

    @property
    def roles(self) -> tuple:
        """The roles this Holder may be changed to. An Organization stops at
        Data maintainer; one holding Admin from before that rule keeps it in
        the list, so the choice shows what it holds, and can only lower it.
        """
        if self.kind == USER:
            return ROLES
        if self.level in ROLE_OF and self.level > ORGANIZATION_CEILING:
            return ORGANIZATION_ROLES + (ROLE_OF[self.level],)
        return ORGANIZATION_ROLES


@dataclass
class Access:
    """A Table's Holders as one viewer sees them. ``own_groups`` are the ids
    of every group the viewer is a member of."""

    table: object
    viewer: object
    users: list
    organizations: list
    level: int
    everywhere_admin: bool = False
    own_groups: frozenset = frozenset()
    shareable: list = field(default_factory=list)

    @property
    def holders(self) -> list:
        return self.users + self.organizations

    @property
    def can_manage(self) -> bool:
        """Whether the viewer is a Table admin here."""
        return self.level >= ADMIN_PERM

    @property
    def admins(self) -> list:
        """The users holding direct Admin: whom a non-admin asks."""
        return [h for h in self.users if h.level >= ADMIN_PERM]

    @property
    def own_grant(self):
        """The viewer's own direct grant, which they may leave."""
        return next((h for h in self.users if h.you), None)

    def holder(self, key):
        return next((h for h in self.holders if h.key == key), None)

    def _grants_after(self, kind, pk, level) -> list:
        """The viewer's own grant levels once ``kind:pk`` holds ``level``
        (None: no grant), every other grant as it is."""
        levels = [
            h.level for h in self.holders if h.you and (h.kind, h.pk) != (kind, pk)
        ]
        mine = pk == self.viewer.pk if kind == USER else pk in self.own_groups
        if level is not None and mine:
            levels.append(level)
        return levels

    def level_after(self, kind, pk, level) -> int:
        """The viewer's effective role once ``kind:pk`` holds ``level``."""
        if self.everywhere_admin:
            return ADMIN_PERM
        return max([NO_PERM] + self._grants_after(kind, pk, level))

    def listed_after(self, kind, pk, level) -> bool:
        """Whether the Table is still on the viewer's dashboard once
        ``kind:pk`` holds ``level``: a grant of Data editor or above, their
        own or an Organization's. Being a platform admin does not list a
        Table."""
        return max([NO_PERM] + self._grants_after(kind, pk, level)) >= WRITE_PERM


def _everywhere_admin(user) -> bool:
    if not user.is_authenticated:
        return False
    return bool(user.is_admin) or (
        Organization.objects.filter(is_admin=True, memberships__user=user).exists()
    )


def table_levels(user, tables) -> dict:
    """The user's effective Table role on each of ``tables``, by primary
    key. See the module docstring for the rule. Three queries whatever the
    number of Tables (one for a platform admin)."""
    ids = [table.pk for table in tables]
    if _everywhere_admin(user):
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


def _image(user) -> str:
    try:
        return user.profile_img.url if user.profile_img else ""
    except ValueError:
        return ""


def table_access(viewer, table) -> Access:
    """``table``'s Holders as ``viewer`` sees them. Users first, then
    Organizations, each by role (highest first) and name. Five queries.
    An anonymous viewer (the Table's permission page is public) sees the
    same Holders, none of them their own, and may change nothing."""
    own_groups = (
        set(Membership.objects.filter(user=viewer).values_list("group_id", flat=True))
        if viewer.is_authenticated
        else set()
    )
    users = [
        Holder(
            USER,
            grant.holder_id,
            grant.holder.name,
            grant.level,
            you=grant.holder_id == viewer.pk,
            image=_image(grant.holder),
        )
        for grant in UserPermission.objects.filter(table=table)
        .select_related("holder")
        .order_by("-level", "holder__name")
    ]
    organizations = [
        Holder(
            ORGANIZATION,
            grant.holder_id,
            grant.holder.name,
            grant.level,
            you=grant.holder_id in own_groups,
            members=grant.members,
        )
        for grant in GroupPermission.objects.filter(table=table)
        .select_related("holder")
        .annotate(members=Count("holder__memberships"))
        .order_by("-level", "holder__name")
    ]
    everywhere = _everywhere_admin(viewer)
    level = ADMIN_PERM if everywhere else NO_PERM
    for holder in users + organizations:
        if holder.you:
            level = max(level, holder.level)
    access = Access(
        table=table,
        viewer=viewer,
        users=users,
        organizations=organizations,
        level=level,
        everywhere_admin=everywhere,
        own_groups=frozenset(own_groups),
    )
    if access.can_manage:
        held = {h.pk for h in organizations}
        access.shareable = list(
            Organization.objects.filter(memberships__user=viewer)
            .exclude(pk__in=held)
            .order_by("name")
        )
    return access


@dataclass(frozen=True)
class Change:
    """What a write did: which Holder now holds which role (None: no
    grant)."""

    action: str
    table: object
    kind: str
    pk: int
    name: str
    before: int
    after: int

    @property
    def role(self) -> str:
        return role_label(self.after)

    @property
    def message(self) -> str:
        """What was done, in one sentence, the same wherever it was done."""
        title = _title(self.table)
        if self.action == ADD and self.kind == USER:
            return f"Gave {self.name} {self.role} on {title}."
        if self.action == ADD:
            return f"Shared {title} with {self.name} as {self.role}."
        if self.action == CHANGE:
            return f"{self.name} is now {self.role} on {title}."
        if self.action == LEAVE:
            return f"You left {title}."
        return f"Removed {self.name} from {title}."


def _level(raw, roles) -> int:
    """``raw`` as one of ``roles``' levels, or ``InvalidRequest``."""
    try:
        level = int(raw)
    except (TypeError, ValueError):
        level = None
    if level not in {role.level for role in roles}:
        offered = ", ".join(role.label for role in roles)
        raise InvalidRequest(f"Choose one of the roles: {offered}.", "level")
    return level


def organization_level(raw, roles=ORGANIZATION_ROLES) -> int:
    """``raw`` as a role an Organization may be given. A known role above
    the ceiling gets its own reason rather than the list of roles."""
    try:
        level = int(raw)
    except (TypeError, ValueError):
        level = None
    if level in ROLE_OF and level not in {role.level for role in roles}:
        raise InvalidRequest(
            "An organization can be given Data maintainer at most. "
            "Admin is given to users, by name.",
            "level",
        )
    return _level(raw, roles)


def _parse_key(raw):
    kind, _, pk = (raw or "").partition(":")
    if kind not in (USER, ORGANIZATION) or not pk.isdigit():
        raise InvalidRequest("Name a holder of this table.", "holder")
    return kind, int(pk)


def _guard(access, kind, pk, after):
    """The last-admin guard: refuse a change that takes direct Admin from
    the last user holding it."""
    if kind != USER or (after is not None and after >= ADMIN_PERM):
        return
    admins = access.admins
    if [h.pk for h in admins] == [pk]:
        raise LastAdmin()


def _title(table) -> str:
    """A Table's title, or an Organization's name, in quotation marks."""
    name = getattr(table, "human_readable_name", None) or table.name
    return f"\u201c{name}\u201d"


def _confirm(access, kind, pk, after, confirmed, action):
    """Ask before the viewer leaves, or loses their own Admin, or loses the
    Table from their dashboard."""
    if confirmed:
        return
    listed = access.listed_after(kind, pk, after)
    if action == LEAVE:
        raise ConfirmationNeeded(
            f"Leave {_title(access.table)}? "
            + (
                "You keep access through an organization."
                if listed
                else "It will disappear from your dashboard."
            )
        )
    if not listed and access.listed_after(None, None, None):
        raise ConfirmationNeeded(
            f"You will hold no role on {_title(access.table)} any more. "
            "It will disappear from your dashboard."
        )
    if access.level_after(kind, pk, after) < ADMIN_PERM <= access.level:
        raise ConfirmationNeeded(
            "You will no longer be able to manage this table's access."
        )


def _write(viewer, table, action, kind, pk, name, before, after, via, access):
    model = UserPermission if kind == USER else GroupPermission
    if after is None:
        model.objects.filter(table=table, holder_id=pk).delete()
    elif before is None:
        model.objects.create(table=table, holder_id=pk, level=after)
    else:
        model.objects.filter(table=table, holder_id=pk).update(level=after)
    change = Change(
        action=action,
        table=table,
        kind=kind,
        pk=pk,
        name=name,
        before=before,
        after=after,
    )
    transaction.on_commit(lambda: _log(change, viewer, via))
    return change


def _log(change, viewer, via):
    def shown(level):
        return "-" if level is None else str(level)

    logger.info(
        "table_permission_write table=%s holder=%s:%s action=%s before=%s "
        "after=%s by=%s via=%s",
        change.table.name,
        change.kind,
        change.pk,
        change.action,
        shown(change.before),
        shown(change.after),
        viewer.pk,
        via,
    )


def _locked(viewer, table):
    """The Table locked for this transaction, and its Holders read under
    the lock."""
    list(
        type(table)
        .objects.select_for_update()
        .filter(pk=table.pk)
        .values_list("pk", flat=True)
    )
    return table_access(viewer, table)


def _managed(viewer, table):
    access = _locked(viewer, table)
    if not access.can_manage:
        raise NotAllowed(ONLY_ADMINS)
    return access


def add(viewer, table, kind, who, level, via="dashboard"):
    """Give a new Holder a role: a user by name (``who`` is the user name),
    or one of the viewer's Organizations (``who`` is its id)."""
    with transaction.atomic():
        access = _managed(viewer, table)
        if kind == USER:
            level = _level(level, ROLES)
            holder = myuser.objects.filter(name=(who or "").strip()).first()
            if holder is None:
                shown = (who or "").strip()
                raise InvalidRequest(
                    (
                        f"There is no user named “{shown}”."
                        if shown
                        else "Name the user to add."
                    ),
                    "name",
                )
            pk, name = holder.pk, holder.name
        elif kind == ORGANIZATION:
            level = organization_level(level)
            organization = (
                Organization.objects.filter(pk=who, memberships__user=viewer).first()
                if str(who or "").isdigit()
                else None
            )
            if organization is None:
                raise InvalidRequest(
                    "You can share a table only with organizations you are a "
                    "member of.",
                    "organization",
                )
            pk, name = organization.pk, organization.name
        else:
            raise InvalidRequest("Add a user or an organization.", "kind")
        existing = access.holder(f"{kind}:{pk}")
        if existing is not None:
            raise InvalidRequest(
                f"{name} already holds {existing.role}. "
                "Change their role in the list instead.",
                "name" if kind == USER else "organization",
            )
        # adding never lowers anyone, so it asks no confirmation
        return _write(viewer, table, ADD, kind, pk, name, None, level, via, access)


def change(viewer, table, key, level, via="dashboard", confirmed=False):
    """Give an existing Holder another role."""
    with transaction.atomic():
        access = _managed(viewer, table)
        kind, pk = _parse_key(key)
        holder = access.holder(f"{kind}:{pk}")
        if holder is None:
            raise InvalidRequest("They no longer hold a role on this table.", "holder")
        if kind == ORGANIZATION:
            level = organization_level(level, holder.roles)
        else:
            level = _level(level, holder.roles)
        if level == holder.level:
            return None
        _guard(access, kind, pk, level)
        _confirm(access, kind, pk, level, confirmed, CHANGE)
        return _write(
            viewer,
            table,
            CHANGE,
            kind,
            pk,
            holder.name,
            holder.level,
            level,
            via,
            access,
        )


def remove(viewer, table, key, via="dashboard", confirmed=False):
    """Take a Holder's role away."""
    with transaction.atomic():
        access = _managed(viewer, table)
        kind, pk = _parse_key(key)
        holder = access.holder(f"{kind}:{pk}")
        if holder is None:
            raise InvalidRequest("They no longer hold a role on this table.", "holder")
        _guard(access, kind, pk, None)
        _confirm(access, kind, pk, None, confirmed, REMOVE)
        return _write(
            viewer,
            table,
            REMOVE,
            kind,
            pk,
            holder.name,
            holder.level,
            None,
            via,
            access,
        )


def leave(viewer, table, via="dashboard", confirmed=False):
    """Drop the viewer's own direct grant, whatever its role."""
    with transaction.atomic():
        access = _locked(viewer, table)
        own = access.own_grant
        if own is None:
            raise NotAllowed(
                "You hold no role of your own on this table. Access through "
                "an organization is left by leaving the organization."
            )
        _guard(access, USER, own.pk, None)
        _confirm(access, USER, own.pk, None, confirmed, LEAVE)
        return _write(
            viewer, table, LEAVE, USER, own.pk, own.name, own.level, None, via, access
        )


# --------------------------------------------------------------------------
# Bulk: one Organization across many Tables (#2568, WF-08 decisions 11-15).
#
# Organizations only: a bulk grant to a user would mostly be a bulk Admin
# grant, around "Admin is given by name". Both writes are all or nothing in
# one transaction holding a row lock on every Table, with the checks in the
# single-Table order: parameters, Table admin on EVERY Table (``NotAllowed``,
# naming the Tables, nothing written), the guard, the confirmation. One log
# line per Table written; a Table left as it is writes nothing and logs
# nothing.
#
# - Sharing only ever raises: where the Organization holds the role or more
#   already (an old Admin grant included) the Table stays unchanged, because
#   "set exactly this role" would quietly take a delete right away. Lowering
#   stays a per-Table change in the drawer.
# - Removing leaves out a Table whose only Admin is that Organization's old
#   Admin grant (``LastAdmin``). This is stricter than ``remove`` for one
#   Table, whose guard counts users only and so lets that grant go; WF-08
#   decision 15 asks for it here, where a batch would otherwise strip the last
#   Admin from Tables nobody looked at one by one.
# - Removing an Organization the viewer belongs to can take Tables off their
#   dashboard, or take their Admin on Tables they keep. That is one
#   confirmation for the batch, naming those Tables (``ConfirmationNeeded``),
#   as losing one's own Admin or access is for one Table; ``confirmed`` is
#   the names the viewer was shown, or True for all, so a Table that joins
#   that list after the viewer confirmed is asked about again rather than
#   lost unseen.
# --------------------------------------------------------------------------

ONLY_ADMIN_THERE = (
    "{organization}'s Admin is the only Admin there. Give someone Admin there first"
)
NOT_HELD = "{organization} holds no role on it"


@dataclass
class OrganizationPlan:
    """What sharing Tables with ``organization`` at ``level`` (removing it
    from them: ``level`` None) would do for ``viewer``, Table by Table.

    ``changes`` are the writes, ``(table, level before or None)``. The rest
    say why a Table would not be written: ``not_admin`` (the viewer is not a
    Table admin there), ``unchanged`` (sharing: the role or more is held
    already), ``not_held`` (removing: there is nothing to remove) and
    ``guarded`` (removing: the Organization's old Admin grant is the only
    Admin). ``lose_access`` are the Tables of ``changes`` a removal would take
    off the viewer's dashboard, ``lose_admin`` those it keeps there but on
    which the viewer would no longer be a Table admin. ``members`` is the
    Organization's member count: every one of them gains, or loses, what it
    holds."""

    organization: Organization
    level: int = None
    members: int = 0
    changes: list = field(default_factory=list)
    not_admin: list = field(default_factory=list)
    unchanged: list = field(default_factory=list)
    not_held: list = field(default_factory=list)
    guarded: list = field(default_factory=list)
    lose_access: list = field(default_factory=list)
    lose_admin: list = field(default_factory=list)

    @property
    def tables(self) -> list:
        return [table for table, _ in self.changes]


def _with_members(organizations):
    return organizations.annotate(members=Count("memberships", distinct=True))


def own_organizations(viewer):
    """The Organizations ``viewer`` is a member of, at any membership
    level: the ones they may share a Table with. By name, each with its
    member count (``members``)."""
    ids = Membership.objects.filter(user=viewer).values("group_id")
    return _with_members(Organization.objects.filter(pk__in=ids)).order_by("name")


def organizations_on(tables):
    """The Organizations holding a role on at least one of ``tables``: the
    ones that can be removed from them. Membership is not needed for that,
    as for one Table. By name, each with its member count."""
    ids = GroupPermission.objects.filter(table__in=tables).values("holder_id")
    return _with_members(Organization.objects.filter(pk__in=ids)).order_by("name")


def _organization_in(organizations, value):
    """The Organization ``value`` names (an Organization or its id) among
    ``organizations``, or None."""
    pk = getattr(value, "pk", value)
    return organizations.filter(pk=pk).first() if str(pk or "").isdigit() else None


def own_organization(viewer, value):
    """The Organization ``value`` names, if ``viewer`` is a member of it, or
    ``InvalidRequest`` (field ``organization``)."""
    organization = _organization_in(own_organizations(viewer), value)
    if organization is None:
        raise InvalidRequest(
            "You can share a table only with organizations you are a member of.",
            "organization",
        )
    return organization


def any_organization(value):
    """The Organization ``value`` names, or ``InvalidRequest``: removing one
    needs no membership."""
    organization = _organization_in(Organization.objects.all(), value)
    if organization is None:
        raise InvalidRequest("Choose an organization.", "organization")
    return organization


def plan_organization(viewer, tables, organization, level=None) -> OrganizationPlan:
    """What sharing ``tables`` with ``organization`` at ``level``, or
    removing it from them (``level`` None), would do. Writes nothing, and
    takes the parameters as they are: ``level`` is checked by the writes.
    A constant number of queries whatever the number of Tables."""
    ids = [table.pk for table in tables]
    levels = table_levels(viewer, tables)
    grants = dict(
        GroupPermission.objects.filter(
            holder_id=organization.pk, table_id__in=ids
        ).values_list("table_id", "level")
    )
    plan = OrganizationPlan(
        organization=organization,
        level=level,
        members=Membership.objects.filter(group_id=organization.pk).count(),
    )
    sharing = level is not None
    if not sharing:
        admins = set(
            UserPermission.objects.filter(
                table_id__in=ids, level__gte=ADMIN_PERM
            ).values_list("table_id", flat=True)
        ) | set(
            GroupPermission.objects.filter(table_id__in=ids, level__gte=ADMIN_PERM)
            .exclude(holder_id=organization.pk)
            .values_list("table_id", flat=True)
        )
        member = Membership.objects.filter(
            user=viewer, group_id=organization.pk
        ).exists()
        # the viewer's role on each Table once the Organization is gone:
        # their own grant, or another of their Organizations'
        kept = {}
        if member:
            grants_kept = list(
                UserPermission.objects.filter(
                    holder=viewer, table_id__in=ids
                ).values_list("table_id", "level")
            )
            grants_kept += (
                GroupPermission.objects.filter(
                    holder__memberships__user=viewer, table_id__in=ids
                )
                .exclude(holder_id=organization.pk)
                .values_list("table_id", "level")
            )
            for table_id, held in grants_kept:
                kept[table_id] = max(kept.get(table_id, NO_PERM), held)
        # a platform admin keeps Table admin everywhere, but not the listing
        everywhere = member and _everywhere_admin(viewer)
    for table in tables:
        before = grants.get(table.pk)
        if levels[table.pk] < ADMIN_PERM:
            plan.not_admin.append(table)
        elif sharing:
            if before is not None and before >= level:
                plan.unchanged.append(table)
            else:
                plan.changes.append((table, before))
        elif before is None:
            plan.not_held.append(table)
        elif before >= ADMIN_PERM and table.pk not in admins:
            plan.guarded.append(table)
        else:
            plan.changes.append((table, before))
            after = kept.get(table.pk, NO_PERM)
            if not member:
                continue
            if before >= WRITE_PERM and after < WRITE_PERM:
                plan.lose_access.append(table)
            elif before >= ADMIN_PERM and after < ADMIN_PERM and not everywhere:
                plan.lose_admin.append(table)
    return plan


def _quoted(tables) -> str:
    return ", ".join(_title(table) for table in tables)


def _lock_tables(tables):
    """Lock ``tables`` for this transaction, in one order, so two bulk
    writes over overlapping selections wait for each other instead of
    deadlocking."""
    if tables:
        model = type(tables[0])
        list(
            model.objects.select_for_update()
            .filter(pk__in=[table.pk for table in tables])
            .order_by("pk")
            .values_list("pk", flat=True)
        )


def _refuse_not_admin(plan):
    if plan.not_admin:
        raise NotAllowed(
            f"{ONLY_ADMINS} You are not a Table admin on "
            f"{_quoted(plan.not_admin)}.",
            plan.not_admin,
        )


def _write_all(viewer, plan, via) -> list:
    organization = plan.organization
    return [
        _write(
            viewer,
            table,
            REMOVE if plan.level is None else ADD if before is None else CHANGE,
            ORGANIZATION,
            organization.pk,
            organization.name,
            before,
            plan.level,
            via,
            None,
        )
        for table, before in plan.changes
    ]


def share_with_organization(viewer, tables, organization, level, via="dashboard"):
    """Give ``organization`` the role ``level`` on every one of ``tables``
    where it holds less, in one transaction. ``organization`` is one of the
    viewer's own (an Organization or its id). Returns one ``Change`` per Table
    written, an ``add`` or a ``change``; the Tables where it holds that role
    or more already are left as they are (``plan_organization``)."""
    level = organization_level(level)
    organization = own_organization(viewer, organization)
    with transaction.atomic():
        _lock_tables(tables)
        plan = plan_organization(viewer, tables, organization, level)
        _refuse_not_admin(plan)
        return _write_all(viewer, plan, via)


def remove_organization(
    viewer, tables, organization, via="dashboard", confirmed=()
) -> list:
    """Take ``organization``'s role away on every one of ``tables`` where it
    holds one, in one transaction. Refused whole (``LastAdmin``) when its old
    Admin grant is the only Admin of one of them, and asks first
    (``ConfirmationNeeded``) when the viewer would lose a Table from their
    dashboard, or their Admin on one, that ``confirmed`` (names, or True for
    all) does not hold.
    Returns one ``Change`` per Table written."""
    with transaction.atomic():
        _lock_tables(tables)
        plan = plan_organization(viewer, tables, organization)
        _refuse_not_admin(plan)
        name = _title(organization)
        if plan.guarded:
            raise LastAdmin(
                ONLY_ADMIN_THERE.format(organization=name)
                + f": {_quoted(plan.guarded)}.",
                plan.guarded,
            )
        if confirmed is not True:
            unasked = [
                table
                for table in plan.lose_access + plan.lose_admin
                if table.name not in set(confirmed)
            ]
            if unasked:
                raise ConfirmationNeeded(
                    f"You will lose access to, or Admin on, {_quoted(unasked)}.",
                    unasked,
                )
        return _write_all(viewer, plan, via)
