"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from rest_framework.permissions import BasePermission


class CanEditScenarioBundle(BasePermission):
    """
    Custom permission to allow editing a ScenarioBundle only for users
    in the 'ScenarioBundleAccess' group.
    Assumes the ScenarioBundle model has a 'created_by' foreign key field pointing
    to the User model.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is in the 'ScenarioBundleAccess' group
        if request.user.groups.filter(name="ScenarioBundleAccess").exists():
            return True

        return False
