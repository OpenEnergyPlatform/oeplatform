"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Who may reach a view under ``profile/<user_id>/``: its owner, and nobody else.

A profile page is a user's own dashboard. There is no public profile and no
"someone else's dashboard" to show, so every route carrying a ``user_id``
answers only when that id is the caller's own:

- anonymous, full page: 302 to the login page, with ``next``
- anonymous, htmx request: 401, no body
- logged in with another id: 404, page and htmx alike
- the owner: the view runs

Platform admins are not exempt: support goes through the Django shell, not
through someone's dashboard.

A foreign id answers 404, never 403, and the same 404 for an id that exists
and one that does not, so the answer does not reveal which accounts exist. On
a match the view is handed ``request.user``; the user named in the URL is
never loaded.

An htmx request gets a bare 401 rather than the login redirect, because htmx
follows a redirect and would swap the login page into the fragment it was
asked to fill.

This lives in its own module rather than in ``login/permissions.py`` because
that one holds the permission levels and is imported by ``login/models.py`` at
app-loading time, before the auth views this module needs can be imported.

``enforces_owner_rule`` tells whether the rule actually runs for a URL
callback. ``login/tests/test_profile_owner_rule`` walks every URL pattern and
fails for a ``user_id`` route on which it does not.
"""  # noqa: 501

from functools import wraps
from weakref import WeakSet

from django.contrib.auth.views import redirect_to_login
from django.http import Http404, HttpResponse


def _is_htmx(request) -> bool:
    return "HX-Request" in request.headers


def _refusal(request, user_id):
    """The response that refuses this caller, or None for the owner.

    Raises Http404 for a logged-in caller with another id.
    """
    if not request.user.is_authenticated:
        if _is_htmx(request):
            return HttpResponse(status=401)
        return redirect_to_login(request.get_full_path())
    if str(request.user.pk) != str(user_id):
        raise Http404
    return None


class ProfileOwnerRequiredMixin:
    """The owner rule for class-based views.

    List it FIRST in the bases: ``View.dispatch`` does not call further along
    the MRO, so a mixin placed after the view class never runs.

    On a match ``self.profile_user`` is the caller.
    """

    def dispatch(self, request, *args, **kwargs):
        refusal = _refusal(request, kwargs.get("user_id"))
        if refusal is not None:
            return refusal
        self.profile_user = request.user
        return super().dispatch(request, *args, **kwargs)


def profile_owner_required(view_func):
    """The owner rule for function views.

    The view is called as ``view_func(request, profile_user, ...)`` without
    the ``user_id``, and ``profile_user`` is the caller.
    """

    @wraps(view_func)
    def wrapper(request, user_id, *args, **kwargs):
        refusal = _refusal(request, user_id)
        if refusal is not None:
            return refusal
        return view_func(request, request.user, *args, **kwargs)

    _GUARDED_FUNCTIONS.add(wrapper)
    return wrapper


# The wrappers profile_owner_required made. A registry rather than an
# attribute, because functools.wraps copies attributes onto whatever wraps a
# view, so an attribute would also mark a function that never runs the rule.
_GUARDED_FUNCTIONS = WeakSet()


def enforces_owner_rule(view) -> bool:
    """Whether the owner rule runs first for this URL callback.

    A class-based view must resolve ``dispatch`` to the mixin's own: that
    rejects the mixin listed after ``View`` (``View.dispatch`` wins and never
    calls along the MRO) and a ``dispatch`` override that could skip it. A
    function view must be the decorator's wrapper itself, the outermost layer,
    so nothing runs before the rule.
    """
    view_class = getattr(view, "view_class", None)
    if view_class is not None:
        return view_class.dispatch is ProfileOwnerRequiredMixin.dispatch
    return view in _GUARDED_FUNCTIONS
