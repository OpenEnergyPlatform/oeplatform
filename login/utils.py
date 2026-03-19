"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import TYPE_CHECKING

from login.models import UserPermission
from login.models import myuser as User
from login.permissions import ADMIN_PERM

if TYPE_CHECKING:
    # only import for static typechecking
    from dataedit.models import Table

###############################################################
# Utilities mainly used for the Group Management profile page #
###############################################################


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
