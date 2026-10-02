"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
from functools import wraps

from django.http import HttpResponseForbidden

from factsheet.models import ScenarioBundleAccessControl


def only_if_user_is_owner_of_scenario_bundle(view_func):
    """
    Wrapper that checks if the current user is among the owners of
    the Scenario bundle.

    It determines the owner of the Scenario bundle by checking
    the ScenarioBundleEditAccess model. The uid of the scenario
    bundle is passed as a URL parameter or in the request body.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Parse uid robustly (avoid json.loads twice)
        payload = {}
        if request.body:
            try:
                payload = json.loads(request.body)
            except Exception:
                payload = {}

        uid = (
            kwargs.get("uid")
            or payload.get("uid")
            or payload.get("id")
            or request.GET.get("id")
        )

        if not uid:
            return HttpResponseForbidden("Missing bundle uid. Access denied")

        user = request.user
        if not getattr(user, "is_authenticated", False):
            return HttpResponseForbidden("Not authenticated. Access denied")

        # Admin bypass
        if getattr(user, "is_admin", False):
            return view_func(request, *args, **kwargs)

        # Bundle must exist at all (optional but keeps your old behavior/messages)
        if not ScenarioBundleAccessControl.objects.filter(bundle_id=uid).exists():
            return HttpResponseForbidden(
                "UID not available or scenario bundle does not exist. Access denied"
            )

        # The actual access check (this is the key change)
        if ScenarioBundleAccessControl.user_has_access(user, uid):
            return view_func(request, *args, **kwargs)

        return HttpResponseForbidden("Access Denied")

    return _wrapped_view


def post_only_if_user_is_owner_of_scenario_bundle(view_func):
    """
    Wrapper that checks if the current user is among the owners of
    the Scenario bundle. This is a decorator for POST requests.

    It differs from the only_if_user_is_owner_of_scenario_bundle
    as it depends on data from the request body instead of URL parameters.

    It determines the owner of the Scenario bundle by checking
    the ScenarioBundleEditAccess model. The uid of the scenario
    bundle is passed as a URL parameter or in the request body.
    """

    @wraps(view_func)
    def _wrapped_view(view_instance, request, *args, **kwargs):
        bundle_uid = kwargs.get("uid") or request.data.get("scenario_bundle")
        if not bundle_uid:
            return HttpResponseForbidden(
                "The bundle_uid (scenario bundle) was not found in the"
                " request body or URL parameters"
            )

        user = request.user
        if not getattr(user, "is_authenticated", False):
            return HttpResponseForbidden("Not authenticated. Access denied")

        if getattr(user, "is_admin", False):
            return view_func(view_instance, request, *args, **kwargs)

        if not ScenarioBundleAccessControl.objects.filter(
            bundle_id=bundle_uid
        ).exists():
            return HttpResponseForbidden(
                "UID not available or scenario bundle does not exist. Access denied"
            )

        if ScenarioBundleAccessControl.user_has_access(user, bundle_uid):
            return view_func(view_instance, request, *args, **kwargs)

        return HttpResponseForbidden("Access Denied")

    return _wrapped_view
