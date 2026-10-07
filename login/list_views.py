"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The views a list tab of the profile dashboard is made of, as bases that know
nothing about what is listed (spec #2613, prefactor). The tables tab is the
first consumer (``login/views.py``); a second tab subclasses the same bases
instead of copying them.

- ``ListFrame``: the two words that tell one tab's page apart from another's,
  and every id, event and URL name derived from them.
- ``ListTabView``: the tab itself, a whole page or, for htmx, the results
  region alone.
- ``ListNamesView``: the keys of everything the list's filters select, across
  pages, for "Select all N matching".
- ``ActionView`` and ``ActionCheckView``: one action on one item or a batch,
  through an action service; the preflight as GET (a row) or POST (the bulk
  bar), the execution as POST.

A subclass supplies ``frame``, ``listing(user)`` (a ``login.listing.Listing``)
and ``base(user)`` (the queryset the listing filters), and each view the hooks
its docstring names. Put the class supplying ``listing`` and ``base`` before
the base in the bases, so it is found first.

Every base starts with ``ProfileOwnerRequiredMixin``, so the owner rule runs
for every subclass (``login/access.py``).
"""  # noqa: 501

import json
from dataclasses import dataclass
from urllib.parse import urlsplit

from django.http import Http404, HttpResponse, JsonResponse, QueryDict
from django.shortcuts import render
from django.utils.cache import patch_vary_headers
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import View

from login.access import ProfileOwnerRequiredMixin, is_htmx

# What the dialog says when it was confirmed before the check for what was
# just chosen in it (a Dataset, an Organization, a role) had come back.
RECHECKED = (
    "Nothing was changed: the check for your choice had not come back yet."
    " Look it over and confirm again."
)


@dataclass(frozen=True)
class ListFrame:
    """What tells one list tab apart from another on the page: ``items``,
    the plural (``"tables"``), and ``item``, the singular (``"table"``).

    The plural prefixes the tab's own ids (``<items>-results``,
    ``<items>-bulk``, ...), names its events and is the comma-joined
    selection parameter; the singular prefixes the action dialog's ids, is
    the repeated parameter a row's menu sends and is the stem of the tab's
    URL names. The base templates read every id from here, so two tabs can
    share them and neither id set changes.
    """

    items: str
    item: str

    @property
    def region_id(self) -> str:
        """The results region: when it is the element that triggered a
        request, the request is its re-fetch after an action."""
        return f"{self.items}-results"

    @property
    def changed_event(self) -> str:
        return f"{self.items}-changed"

    @property
    def refused_event(self) -> str:
        return f"{self.items}-refused"

    @property
    def dialog(self) -> str:
        return f"{self.item}-action"

    @property
    def action_url(self) -> str:
        return f"login:{self.item}-action"

    @property
    def check_url(self) -> str:
        return f"login:{self.item}-action-check"

    @property
    def names_url(self) -> str:
        return f"login:{self.item}-names"


def joined(data, key) -> list:
    """The names in one comma-joined parameter."""
    return [name.strip() for name in data.get(key, "").split(",") if name.strip()]


def not_shown(request, listing, base, items) -> list:
    """Which of ``items`` the list the request came from no longer shows
    under its filters. Empty when the request does not say where it came
    from (``HX-Current-URL``)."""
    current = request.headers.get("HX-Current-URL")
    if not current:
        return []
    query = QueryDict(urlsplit(current).query)
    shown = set(
        listing.matching(base, query)
        .filter(pk__in=[item.pk for item in items])
        .values_list("pk", flat=True)
    )
    return [item for item in items if item.pk not in shown]


class ListTabView(ProfileOwnerRequiredMixin, View):
    """A list tab: one list of the user's items.

    A direct load renders the whole page; an htmx request gets only the
    results region, carrying the canonical address of what it shows in
    ``HX-Push-Url`` (defaults left out, the page clamped), so the address bar
    always names the state on screen; the region's own re-fetch after an
    action (``<items>-changed``) gets ``HX-Replace-Url`` instead. A history
    restore is a full page, because htmx swaps it into the body.

    Hooks: ``page_template``, ``region_template``, ``bulk_actions`` (the bulk
    bar's ``(action, label)`` pairs, in order), ``rows(user)`` (the
    ``rows`` callable for ``Listing.page``) and ``extra_context()``.
    """

    frame: ListFrame
    page_template: str
    region_template: str
    bulk_actions = ()

    def extra_context(self) -> dict:
        return {}

    @method_decorator(never_cache)
    def get(self, request, user_id):
        user = self.profile_user
        page = self.listing(user).page(
            self.base(user), request.GET, request.path, rows=self.rows(user)
        )
        context = {
            "profile_user": user,
            "page": page,
            "frame": self.frame,
            "bulk_actions": self.bulk_actions,
            **self.extra_context(),
        }
        if is_htmx(request) and "HX-History-Restore-Request" not in request.headers:
            response = render(request, self.region_template, context)
            # The region re-fetching itself after an action changes nothing
            # the user navigated to, so it replaces the history entry rather
            # than adding one per action.
            if request.headers.get("HX-Trigger") == self.frame.region_id:
                response["HX-Replace-Url"] = page.url
            else:
                response["HX-Push-Url"] = page.url
        else:
            response = render(request, self.page_template, context)
        patch_vary_headers(response, ["HX-Request"])
        return response


class ListNamesView(ProfileOwnerRequiredMixin, View):
    """The keys of every item the list's filters select, across all pages:
    what "Select all N matching" puts in the selection.

    The query is the list's own, parsed by the same declarations
    (``Listing.matching``), so the names and the list cannot disagree; a
    sort or a page in it is ignored. JSON: ``{"names": [...], "total": n}``,
    ordered by ``key``, the field a selection carries (default ``name``).
    """

    key = "name"

    @method_decorator(never_cache)
    def get(self, request, user_id):
        user = self.profile_user
        names = list(
            self.listing(user)
            .matching(self.base(user), request.GET)
            .order_by(self.key)
            .values_list(self.key, flat=True)
        )
        return JsonResponse({"names": names, "total": len(names)})


class ActionView(ProfileOwnerRequiredMixin, View):
    """One action from the dashboard, for a row (one item) or a batch: GET
    is the preflight, POST the execution. Both answer HTML for the action
    dialog.

    - GET: the dialog, from ``service.preflight``.
    - POST, done: 204 with ``HX-Trigger: <items>-changed`` carrying
      ``done_detail(request, outcome)``. The results region re-fetches
      itself on that event.
    - POST, refused (``service.ActionRefused``): 409, or 403 where
      ``is_forbidden`` says so, the dialog re-run with the refusal's message,
      and ``HX-Trigger: <items>-refused`` for the persistent message.
    - POST, unusable parameters (``service.InvalidParameters``): 400, the
      dialog with the error beside its field, and no toast.
    - POST from a dialog whose preview was checked against another choice
      than the one sent (``previewed``, ``service.choice``): 200, nothing
      written, the dialog checked against the choice sent, with a notice.

    The items come as repeated ``<item>`` parameters (a row's menu) or as
    one comma-joined ``<items>`` (the bulk bar and the dialog's form). A
    selection goes joined because Django refuses a request with more than
    ``DATA_UPLOAD_MAX_NUMBER_FIELDS`` (1,000) parameters, so an item's key
    must never hold a comma. A re-check from the open dialog carries the
    names it was opened with as ``selection``, a superset of what its form
    posts, so an item left out before is still named as left out.

    Hooks: ``service`` (a module offering ``ACTIONS``, ``preflight``,
    ``execute``, ``choice``, ``InvalidParameters`` and ``ActionRefused``),
    ``dialog_template``, ``params`` (the parameters passed to the service),
    ``dialog_context()``, ``done_detail(request, outcome)`` and
    ``is_forbidden(action, refusal)``.
    """

    frame: ListFrame
    service = None
    dialog_template: str
    params = ()

    def dialog_context(self) -> dict:
        return {}

    def done_detail(self, request, outcome) -> dict:
        raise NotImplementedError

    def is_forbidden(self, action, refusal) -> bool:
        return False

    def hidden(self, request, items) -> list:
        """Which of ``items`` the list the request came from no longer
        shows under its filters."""
        user = self.profile_user
        return not_shown(request, self.listing(user), self.base(user), items)

    def _names(self, data):
        return data.getlist(self.frame.item) + joined(data, self.frame.items)

    def _params(self, data):
        return {key: data.get(key, "") for key in self.params}

    def _dialog(self, request, check, status=200, **extra):
        context = {
            "profile_user": self.profile_user,
            "preflight": check,
            **self.dialog_context(),
            "errors": {},
            "values": {},
            **extra,
        }
        return render(request, self.dialog_template, context, status=status)

    def _action(self, action):
        if action not in self.service.ACTIONS:
            raise Http404
        return action

    def _preflight(self, request, action, data):
        """The dialog for what ``data`` names, run on ``selection`` when the
        open dialog asks again."""
        action = self._action(action)
        params = self._params(data)
        names = joined(data, "selection") or self._names(data)
        check = self.service.preflight(self.profile_user, action, names, params)
        return self._dialog(request, check, values=params)

    @method_decorator(never_cache)
    def get(self, request, user_id, action):
        return self._preflight(request, action, request.GET)

    def post(self, request, user_id, action):
        service = self.service
        action = self._action(action)
        user = self.profile_user
        names = self._names(request.POST)
        params = self._params(request.POST)
        # a dialog re-run after a refusal is checked against everything it
        # was opened with, so what was left out before is still named
        again = joined(request.POST, "selection") or names
        previewed = request.POST.get("previewed")
        if previewed is not None and previewed != service.choice(action, params):
            # confirmed in the moment between choosing and its re-check
            # coming back: the names were checked against another choice, so
            # nothing runs and the dialog shows the check for this one
            check = service.preflight(user, action, again, params)
            return self._dialog(request, check, values=params, notice=RECHECKED)
        try:
            outcome = service.execute(user, action, names, params, via="dashboard")
        except service.InvalidParameters as error:
            check = service.preflight(user, action, again, params)
            return self._dialog(
                request, check, status=400, errors=error.errors, values=params
            )
        except service.ActionRefused as refusal:
            check = refusal.preflight
            if again != names:
                check = service.preflight(user, action, again, params)
            response = self._dialog(
                request,
                check,
                status=403 if self.is_forbidden(action, refusal) else 409,
                notice=refusal.message,
            )
            response["HX-Trigger"] = json.dumps(
                {self.frame.refused_event: {"message": refusal.message}}
            )
            return response

        response = HttpResponse(status=204)
        response["HX-Trigger"] = json.dumps(
            {self.frame.changed_event: self.done_detail(request, outcome)}
        )
        return response


class ActionCheckView(ActionView):
    """The preflight of a bulk action, sent as a POST: the bulk bar sends
    the whole selection, which may be every item on the dashboard, more than
    any GET address can carry. It answers exactly what ``ActionView``'s GET
    answers, the dialog, and writes nothing. List it before the tab's own
    action view in the bases, so its ``post`` is the one found."""

    http_method_names = ["post"]

    def post(self, request, user_id, action):
        return self._preflight(request, action, request.POST)
