# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 jh-RLI <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

import json
from functools import wraps

from django.http import HttpResponse, HttpResponseForbidden

from factsheet.models import ScenarioBundleAccessControl


def only_if_user_is_owner_of_scenario_bundle(view_func):
    """
    Wrapper that checks if the current user is the owner of
    the Scenario bundle.

    It determines the owner of the Scenario bundle by checking
    the ScenarioBundleEditAccess model. The uid of the scenario
    bundle is passed as a URL parameter or in the request body.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get the uid from the URL parameters or any other source.
        try:
            uid = (
                kwargs.get("uid")
                or json.loads(request.body).get("uid")
                or json.loads(request.body).get("id")
                or request.GET.get("id")
            )
        except Exception:
            uid = request.GET.get("id")

        try:
            # Retrieve the ScenarioBundleEditAccess object based on the uid.
            scenario_bundle_access = ScenarioBundleAccessControl.objects.get(
                bundle_id=uid
            )
        except ScenarioBundleAccessControl.DoesNotExist:
            # Handle the case where the ScenarioBundleEditAccess with the
            # provided uid is not found.
            return HttpResponseForbidden(
                "UID not available or scenario bundle does not exist. Access denied"
            )

        # Check if the current user is the owner (creator) of the Scenario bundle.
        if request.user == scenario_bundle_access.owner_user:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("Access Denied")

    return _wrapped_view


def post_only_if_user_is_owner_of_scenario_bundle(view_func):
    """
    Wrapper that checks if the current user is the owner of
    the Scenario bundle. This is a decorator for POST requests.

    It differs from the only_if_user_is_owner_of_scenario_bundle
    as it depends on data from the request body instead of URL parameters.

    It determines the owner of the Scenario bundle by checking
    the ScenarioBundleEditAccess model. The uid of the scenario
    bundle is passed as a URL parameter or in the request body.
    """

    @wraps(view_func)
    def _wrapped_view(view_instance, request, *args, **kwargs):
        # Get the uid from the URL parameters or any other source.

        bundle_uid = kwargs.get("uid") or request.data.get("scenario_bundle")
        if not bundle_uid:
            return HttpResponse(
                "The bundle_uid (scenario bundle) was not found in"
                "the request body or URL parameters",
            )

        user_id = request.user
        if not user_id:
            return HttpResponse(
                "The user id was not found in the request body or URL parameters",
            )

        try:
            # Retrieve the ScenarioBundleEditAccess object based on the uid.
            scenario_bundle_access = ScenarioBundleAccessControl.objects.get(
                bundle_id=bundle_uid
            )
        except ScenarioBundleAccessControl.DoesNotExist:
            # Handle the case where the ScenarioBundleEditAccess with the
            # provided uid is not found.
            return HttpResponseForbidden(
                "UID not available or scenario bundle does not exist. Access denied"
            )

        # Check if the current user is the owner (creator) of the Scenario bundle.
        if request.user == scenario_bundle_access.owner_user:
            return view_func(view_instance, request, *args, **kwargs)
        else:
            return HttpResponseForbidden("Access Denied")

    return _wrapped_view
