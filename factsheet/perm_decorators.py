from django.http import HttpResponseForbidden
from functools import wraps
from factsheet.models import ScenarioBundleAccessControl


def only_if_user_is_owner_of_scenario_bundle(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get the uid from the URL parameters or any other source.
        uid = kwargs.get("uid")  # Assuming it's a URL parameter

        try:
            # Retrieve the ScenarioBundleEditAccess object based on the uid.
            scenario_bundle_access = ScenarioBundleAccessControl.objects.get(uid=uid)
        except ScenarioBundleAccessControl.DoesNotExist:
            # Handle the case where the ScenarioBundleEditAccess with the
            # provided uid is not found.
            return HttpResponseForbidden("Access Denied")

        # Check if the current user is the owner (creator) of the ScenarioBundle.
        if request.user == scenario_bundle_access.owner_user:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("Access Denied")

    return _wrapped_view
