"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import TYPE_CHECKING, List

from login.models import GroupPermission, UserGroup, UserPermission
from login.models import myuser as User
from login.permissions import ADMIN_PERM

if TYPE_CHECKING:
    # only import for static typechecking
    # TODO: is there a betetr way of doing this?
    from dataedit.models import Table

###############################################################
# Utilities mainly used for the Group Management profile page #
###############################################################


def get_tables_if_group_assigned(group: UserGroup) -> List["Table"]:
    """
    Get all tables assinged to a group
    """

    group_table_relation = GroupPermission.objects.filter(
        holder_id=group.pk
    ).prefetch_related("table")

    group_tables = []

    for rel in group_table_relation:
        group_tables.append(rel.table)
    return group_tables


def assign_table_holder(user: User, table: "Table") -> None:
    """
    Grant ADMIN permission level to user for the specified table.
    """

    perm, created = UserPermission.objects.get_or_create(
        table=table,
        holder=user,
        defaults={"level": ADMIN_PERM},
    )
    if not created:
        perm.level = ADMIN_PERM
        perm.save()
