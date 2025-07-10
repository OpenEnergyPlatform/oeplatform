# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from enum import Enum, auto
from typing import List

from django.http import Http404
from django.templatetags.static import static
from omi.license import LicenseError, validate_oemetadata_licenses

from dataedit.models import Table
from login.models import GroupPermission, UserGroup
from login.models import myuser as OEPUser

#####################################################
# Utilities mainly used for the Tables profile page #
#####################################################


def get_user_tables(user_id: int) -> List[Table]:
    """
    Collects all tables to which the current user has access rights.
    This includes tables 1. that the user has created 2. to which the
    user have been added, and tables in which a PermissionGroup to which
    the user belongs has been added.
    """
    try:
        user = OEPUser.objects.get(id=user_id)
    except OEPUser.DoesNotExist:
        # Consider logging this exception
        raise Http404

    # All tables where the user holds access permissions
    direct_memberships = user.get_table_memberships()
    tables = [membership.table for membership in direct_memberships]
    user_groups = user.memberships.all()
    for g in user_groups:
        group_permissions = None
        group_permissions = GroupPermission.objects.filter(
            holder_id=g.group.id
        ).prefetch_related("table")
        # add table if it is part of the user group with any
        # permission level above 0|None
        if group_permissions:
            group_memberships = [perm.table for perm in group_permissions]
            tables.extend(group_memberships)

    # Remove duplicates
    tables = list(set(tables))
    return tables


# Functions below implement the automated license check
# based on license check implemented in OMI


def validate_open_data_license(django_table_obj):
    metadata = django_table_obj.oemetadata

    try:
        validate_oemetadata_licenses(metadata)
    except LicenseError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

    return True, None


# The following functions implement the retrieval of review badges
# from the oemetadata and handle the case when no sticker is available.


# TODO Refactor this to dataedit app?
class PeerReviewBadge(Enum):
    IRON = auto()
    BRONZE = auto()
    SILVER = auto()
    GOLD = auto()
    PLATINUM = auto()


def validate_badge_name_match(badge_name_normalized):
    matched_badge = None
    for badge in PeerReviewBadge:
        if badge_name_normalized == badge.name:
            matched_badge = badge
            break

    return matched_badge


def get_review_badge_from_table_metadata(django_table_obj: Table):
    metadata = django_table_obj.oemetadata

    if metadata is None:
        return False, "Metadata is empty!"

    review = metadata.get("review")

    if not review:
        return False, "No review information available in the metadata."

    badge = review.get("badge")

    if badge is None and badge != "":
        return (
            False,
            "No badge information available in the metadata.Please start "
            "a community-based open peer review for this table first.",
        )

    badge_name_normalized = badge.upper()
    check_is_badge = validate_badge_name_match(badge_name_normalized)

    if check_is_badge:
        return True, check_is_badge.name
    else:
        return False, f"No match found for badge name: {badge}"


def get_badge_icon_path(badge_name):
    # Convert the badge name to lowercase and append "_badge.png"
    normalized_name = f"badge_{badge_name.lower()}.png"

    # Use the Django static function to get the correct static path
    icon_path = static(f"img/badges/{normalized_name}")

    return icon_path


#####################################################
# Utilities mainly used for the Review profile page #
#####################################################

# Add functionality here

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
