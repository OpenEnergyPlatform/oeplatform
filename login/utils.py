"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import TYPE_CHECKING, List

from login.models import Organization, OrganizationPermission, UserPermission
from login.models import myuser as User
from login.permissions import ADMIN_PERM

if TYPE_CHECKING:
    # only import for static typechecking
    from dataedit.models import Table

###############################################################
# Utilities mainly used for the Group Management profile page #
###############################################################


def get_tables_for_organization(organization: Organization) -> List["Table"]:
    """
    Get all tables assigned to a organization
    """

    organization_table_relation = OrganizationPermission.objects.filter(
        holder_id=organization.pk
    ).prefetch_related("table")

    organization_tables = []

    for rel in organization_table_relation:
        organization_tables.append(rel.table)
    return organization_tables


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
