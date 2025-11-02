"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import List

from dataedit.models import Table
from login.models import GroupPermission, UserGroup

###############################################################
# Utilities mainly used for the Group Management profile page #
###############################################################


def get_tables_if_group_assigned(group: UserGroup) -> List[Table]:
    """
    Get all tables assinged to a group
    """

    group_table_relation = GroupPermission.objects.filter(
        holder_id=group.id
    ).prefetch_related("table")

    group_tables = []

    for rel in group_table_relation:
        group_tables.append(rel.table)
    return group_tables


#######################################################
# Utilities mainly used for the Settings profile page #
#######################################################

# Add functionality here
