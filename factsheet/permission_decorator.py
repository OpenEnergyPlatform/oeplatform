import json
from functools import wraps

from django.http import HttpResponseForbidden

from factsheet.models import ScenarioBundleAccessControl


def only_if_user_is_owner_of_scenario_bundle(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get the uid from the URL parameters or any other source.
        try:
            uid = (
                kwargs.get("uid")
                or json.loads(request.body).get("uid")
                or json.loads(request.body).get("id")
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
