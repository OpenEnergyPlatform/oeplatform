__license__ = """
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Marco Finkendei <https://github.com/MFinkendei>
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
from itertools import groupby

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.text import capfirst
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import RedirectView, TemplateView, View
from django.views.generic.edit import DeleteView
from rest_framework.authtoken.models import Token

from api.services import dataset_actions, table_actions
from api.services.dataset_creation import dataset_title, normalize_dataset_name
from dataedit.helper import delete_peer_review
from dataedit.models import PeerReviewManager, Table, Topic
from dataedit.publish_gate import DATASET_GATE
from login import dataset_members, table_roles
from login.access import (
    ProfileOwnerRequiredMixin,
    is_htmx,
    membership_or_404,
    profile_owner_required,
)
from login.datasets_tab import (
    dataset_rows,
    datasets_listing,
    name_preview,
    own_dataset_pk,
    own_datasets,
    topic_choices,
)
from login.forms import EditUserForm, OrganizationForm
from login.list_views import (
    ActionCheckView,
    ActionView,
    ListFrame,
    ListNamesView,
    ListTabView,
    not_shown,
)
from login.models import Membership
from login.models import myuser as OepUser
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM
from login.tables_tab import accessible_tables, table_rows, tables_listing
from login.utils import get_tables_for_organization

# NO_PERM = 0/None WRITE_PERM = 4 DELETE_PERM = 8 ADMIN_PERM = 12

###########################################################################
#            User Tables related views & partial views for htmx           #
###########################################################################


# The tables tab's ids, events and URL names (login.list_views.ListFrame).
TABLES = ListFrame(items="tables", item="table")

# The bulk bar's actions, in the order it shows them, with their labels: an
# ellipsis where the dialog asks for more than a confirmation. Delete is red
# and stays last. The Organization actions are here only: one Table's
# Holders are the access drawer's.
BULK_ACTIONS = (
    (table_actions.PUBLISH, "Publish…"),
    (table_actions.UNPUBLISH, "Unpublish"),
    (table_actions.DATASET_ADD, "Add to dataset…"),
    (table_actions.DATASET_REMOVE, "Remove from dataset…"),
    (table_actions.ORGANIZATION_SHARE, "Share with organization…"),
    (table_actions.ORGANIZATION_REMOVE, "Remove organization…"),
    (table_actions.DELETE, "Delete…"),
)


class TablesList:
    """What the tables tab lists: every Table the user may write, through
    the tab's own declarations (``login.tables_tab``)."""

    frame = TABLES

    def listing(self, user):
        return tables_listing(user)

    def base(self, user):
        return accessible_tables(user)

    def rows(self, user):
        return table_rows(user)


class TablesView(TablesList, ListTabView):
    """The tables tab: one list of every Table the user may write
    (``ListTabView``)."""

    page_template = "login/user_tables.html"
    region_template = "login/partials/tables_region.html"
    bulk_actions = BULK_ACTIONS

    def extra_context(self):
        return {"gates": table_actions.ROLE_GATES}


class TableActionView(TablesList, ActionView):
    """One action on Tables from the dashboard, for a row (one name) or a
    batch, through ``table_actions`` (``ActionView``). Both take the Tables
    as repeated ``table`` parameters or one comma-joined ``tables``.

    - POST, done: 204 with ``HX-Trigger: tables-changed``, carrying the
      message and, for one Table, the id of the row's menu to focus.
    - POST, refused (a named Table is no longer allowed): 409 and
      ``tables-refused``. Sharing with or removing an Organization answers
      403 instead when a Table is refused because the user is not a Table
      admin there.
    - POST, unusable parameters (no Topic, the draft pseudo-topic, a
      Dataset that is not the user's own, a typed confirmation that does not
      match, more Tables than the ceiling): 400.
    - POST, from a bulk dialog whose preview was checked against another
      choice than the one sent (``previewed``, ``table_actions.choice``: a
      Dataset, an Organization and its role): 200, nothing written.
    - POST, a delete whose OEDB table could not be dropped afterwards: 204
      as above, but the message says so and carries ``warning``, so it
      stays until dismissed instead of reading as a success.

    A done batch of several Tables also carries ``tables``, their titles,
    which the message lists under "Show tables"; a delete carries ``gone``,
    the names that left the dashboard, so the bulk selection drops them.
    The bulk bar's preflight is ``TableActionCheckView``, because a
    selection does not fit in a GET address. A bulk Dataset dialog asks it
    again when the user chooses a Dataset, sending the whole selection as
    ``selection`` beside the eligible ``tables``.

    The parameters are ``topic`` and ``embargo`` (publish), ``dataset`` (the
    Dataset actions), ``organization`` and ``level`` (sharing with an
    Organization), ``organization`` and ``lose_access`` (removing one: the
    Tables the dialog said the user would lose, comma-joined) and
    ``confirm`` (delete's typed confirmation); the preflight reads
    ``dataset``, ``organization`` and ``level`` too, to leave out what they
    decide. A removal that takes Tables off the dashboard carries them in
    ``gone``.

    Whether a changed Table is still shown is read off ``HX-Current-URL``,
    the address the request was sent from, through the list's own filters.
    """

    service = table_actions
    dialog_template = "login/partials/table_action_dialog.html"
    params = (
        "topic",
        "embargo",
        "dataset",
        "organization",
        "level",
        "lose_access",
        "confirm",
    )

    def dialog_context(self, check):
        return {
            "topics": table_actions.publish_topics(),
            "embargo_periods": table_actions.EMBARGO_PERIODS,
            "organization_roles": table_roles.ORGANIZATION_ROLES,
        }

    def is_forbidden(self, action, refusal):
        # A refusal for the role answers the Organization actions 403, as
        # the permission service's ``NotAllowed`` does in the access drawer
        # and the API (WF-08 decision 13); the other actions keep answering
        # every refusal 409.
        return action in table_actions.ORGANIZATION_ACTIONS and refusal.for_role

    def done_detail(self, request, outcome):
        if outcome.action == table_actions.DELETE:
            # the rows are gone: nothing to name as hidden, no ⋯ to focus,
            # and the selection lets go of them
            detail = {
                "message": _deleted_message(outcome),
                "gone": [table.name for table in outcome.tables],
            }
            if outcome.drop_failed:
                detail["warning"] = True
        else:
            lost = {table.pk for table in outcome.lost}
            kept = [table for table in outcome.tables if table.pk not in lost]
            hidden = self.hidden(request, kept)
            detail = {"message": _done_message(outcome, hidden)}
            if outcome.lost:
                # an Organization removed: those rows left the dashboard
                detail["gone"] = [table.name for table in outcome.lost]
            elif len(outcome.tables) == 1:
                detail["focus"] = f"menu-{outcome.tables[0].pk}"
        if len(outcome.tables) > 1:
            # a bulk success: the summary line, and "Show tables" lists them
            detail["tables"] = [_title(table) for table in outcome.tables]
        return detail


class TableActionCheckView(ActionCheckView, TableActionView):
    """The preflight of a bulk action on Tables, sent as a POST
    (``ActionCheckView``): the largest dashboard holds 2,068 Tables, about
    58 KB of names."""


class TableNamesView(TablesList, ListNamesView):
    """The names of every Table the list's filters select, across all
    pages, by name (``ListNamesView``)."""


class TableAccessView(ProfileOwnerRequiredMixin, View):
    """The access drawer for one Table: who holds which role on it. GET
    renders the drawer; POST makes one change through the permission service
    (``login.table_roles``) and renders the drawer again in place, so it
    stays open for the next change.

    POST takes ``op``: ``add`` (``kind`` user with ``name``, or org with
    ``organization``, and ``level``), ``change`` (``holder`` as ``user:<pk>``
    or ``org:<pk>``, and ``level``), ``remove`` (``holder``) or ``leave``;
    ``confirm=yes`` once the user has confirmed losing their own Admin or
    the Table from their dashboard.

    - done: 200 with ``HX-Trigger: tables-changed``, carrying the message
      and ``stay`` (the drawer stays open and keeps focus); the results
      region re-fetches itself on that event. When the Table has left the
      user's dashboard the drawer says so instead of listing its Holders.
    - needs confirmation: 200, the drawer asking, nothing written, no event.
    - unusable request: 400, the drawer with the error beside its field.
    - not a Table admin: 403, the drawer with the reason.
    - the last user with direct Admin would lose it: 409, the drawer with
      "Give someone else Admin first". This is checked before any
      confirmation is asked for.

    A Table that is not on the user's dashboard (a name that is not a Table,
    or a Table they hold no role on) answers 404, the same for both.
    """

    def _table(self, table_name):
        table = accessible_tables(self.profile_user).filter(name=table_name).first()
        if table is None:
            raise Http404
        return table

    def _drawer(self, request, table, status=200, **extra):
        context = {
            "profile_user": self.profile_user,
            "table": table,
            "title": table.human_readable_name or table.name,
            "roles": table_roles.ROLES,
            "organization_roles": table_roles.ORGANIZATION_ROLES,
            "errors": {},
            "values": {},
            **extra,
        }
        if not context.get("gone"):
            context["access"] = table_roles.table_access(self.profile_user, table)
        return render(
            request,
            "login/partials/table_access_drawer.html",
            context,
            status=status,
        )

    @method_decorator(never_cache)
    def get(self, request, user_id, table_name):
        return self._drawer(request, self._table(table_name))

    def _write(self, table, data):
        user = self.profile_user
        op = data.get("op", "")
        confirmed = data.get("confirm") == "yes"
        if op == table_roles.ADD:
            kind = data.get("kind")
            who = data.get(
                "organization" if kind == table_roles.ORGANIZATION else "name"
            )
            return table_roles.add(user, table, kind, who, data.get("level"))
        if op == table_roles.CHANGE:
            return table_roles.change(
                user, table, data.get("holder"), data.get("level"), confirmed=confirmed
            )
        if op == table_roles.REMOVE:
            return table_roles.remove(
                user, table, data.get("holder"), confirmed=confirmed
            )
        if op == table_roles.LEAVE:
            return table_roles.leave(user, table, confirmed=confirmed)
        raise table_roles.InvalidRequest("Choose a change to make.", "op")

    def post(self, request, user_id, table_name):
        user = self.profile_user
        table = self._table(table_name)
        values = {
            key: request.POST.get(key, "")
            for key in ("op", "kind", "name", "organization", "holder", "level")
        }
        try:
            change = self._write(table, request.POST)
        except table_roles.ConfirmationNeeded as question:
            return self._drawer(
                request, table, confirm=question.message, pending=values
            )
        except table_roles.InvalidRequest as error:
            return self._drawer(
                request,
                table,
                status=400,
                errors={error.field: error.message},
                values=values,
            )
        except table_roles.NotAllowed as refusal:
            return self._drawer(request, table, status=403, notice=refusal.message)
        except table_roles.LastAdmin as refusal:
            return self._drawer(request, table, status=409, notice=refusal.message)

        if change is None:
            # the Holder already holds that role: nothing to do
            return self._drawer(request, table)
        listed = accessible_tables(user).filter(pk=table.pk).exists()
        hidden = (
            not_shown(request, tables_listing(user), accessible_tables(user), [table])
            if listed
            else []
        )
        response = self._drawer(request, table, gone=not listed)
        detail = {"message": _access_message(change, listed, hidden), "stay": True}
        if not listed:
            # the bulk selection lets go of a Table that left the dashboard
            detail["gone"] = [table.name]
        response["HX-Trigger"] = json.dumps({"tables-changed": detail})
        return response


def _access_message(change, listed, hidden) -> str:
    """What a change of access says: what was done, and whether the Table
    left the user's dashboard or is hidden by the current filter."""
    title = _title(change.table)
    message = change.message
    if not listed and change.action == table_roles.LEAVE:
        message = f"You left {title} and no longer have access to it."
    elif not listed:
        message += f" You no longer have access to {title}."
    elif hidden:
        message += " It is not shown under the current filter."
    return message


def _title(table) -> str:
    return f"\u201c{table.human_readable_name or table.name}\u201d"


def _done_message(outcome, hidden) -> str:
    """The success message: what was done, and which changed Tables the
    current filter no longer shows, so they do not seem to vanish."""
    tables = outcome.tables
    count = len(tables)
    what = _title(tables[0]) if count == 1 else f"{count} tables"
    if outcome.action == table_actions.PUBLISH:
        message = f"Published {what} under {outcome.params['topic']}"
        # ``KEEP_EMBARGO`` is not one of the periods; nothing to say then
        embargo = dict(table_actions.EMBARGO_PERIODS).get(outcome.params["embargo"])
        if embargo and outcome.params["embargo"] != "none":
            message += f", embargoed for {embargo}"
        message += "."
    elif outcome.action == table_actions.UNPUBLISH:
        their = "its" if count == 1 else "their"
        message = f"Unpublished {what}. No longer listed under {their} topics."
    elif outcome.action in table_actions.ORGANIZATION_ACTIONS:
        return _organization_message(outcome, what, hidden)
    else:
        dataset = (
            f"\u201c{table_actions.dataset_title(outcome.params['dataset'])}\u201d"
        )
        if outcome.action == table_actions.DATASET_ADD:
            message = f"Added {what} to {dataset}."
        else:
            message = f"Removed {what} from {dataset}."
    if hidden and count == 1:
        message += " It is not shown under the current filter."
    elif len(hidden) == count:
        message += " They are not shown under the current filter."
    elif hidden:
        # counted, not named: a bulk action may move hundreds out of view,
        # and "Show tables" lists what it changed
        message += f" {len(hidden)} of them are not shown under the current filter."
    return message


def _organization_message(outcome, what, hidden) -> str:
    """The message after sharing with an Organization or removing one: what
    was done, the Tables that left the user's dashboard (counted for a
    batch) and, of the others, those the current filter no longer shows."""
    organization = f"\u201c{outcome.params['organization'].name}\u201d"
    if outcome.action == table_actions.ORGANIZATION_SHARE:
        role = table_roles.role_label(outcome.params["level"])
        message = f"Shared {what} with {organization} as {role}."
    else:
        message = f"Removed {organization} from {what}."
    count, lost = len(outcome.tables), len(outcome.lost)
    if lost and count == 1:
        message += f" You no longer have access to {_title(outcome.lost[0])}."
    elif lost == count:
        message += " You no longer have access to them."
    elif lost:
        message += f" You no longer have access to {lost} of them."
    if hidden and count == 1:
        message += " It is not shown under the current filter."
    elif hidden and len(hidden) == count - lost:
        message += " They are not shown under the current filter."
    elif hidden:
        message += f" {len(hidden)} of them are not shown under the current filter."
    return message


def _deleted_message(outcome) -> str:
    """The message after a delete. When an OEDB table could not be dropped
    it names that Table: its record is gone, its data is still in the
    database, and only an administrator can remove it now."""
    tables = outcome.tables
    count = len(tables)
    message = f"Deleted {_title(tables[0]) if count == 1 else f'{count} tables'}."
    failed = outcome.drop_failed
    if failed:
        names = ", ".join(f"{_title(table)} ({table.name})" for table in failed)
        message += (
            f" The database table of {names} could not be removed, so its data"
            " is still stored. This was logged; an administrator has to remove"
            " it."
            if len(failed) == 1
            else f" The database tables of {names} could not be removed, so"
            " their data is still stored. This was logged; an administrator"
            " has to remove them."
        )
    return message


##############################################################################
#           User Datasets related views & partial views for htmx            #
##############################################################################


# The datasets tab's ids, events and URL names (login.list_views.ListFrame).
DATASETS = ListFrame(items="datasets", item="dataset")


class DatasetsList:
    """What the datasets tab lists: the user's own Datasets, drafts and
    published, through the tab's own declarations (``login.datasets_tab``)."""

    frame = DATASETS

    def listing(self, user):
        return datasets_listing(user)

    def base(self, user):
        return own_datasets(user)

    def rows(self, user):
        return dataset_rows(user)


class DatasetsView(DatasetsList, ListTabView):
    """The datasets tab, where the profile opens: one list of the user's own
    Datasets (``ListTabView``). "New dataset" ends the filter row and
    "Create a dataset" fills the empty state; each row's ⋯ menu offers the
    row actions (``DatasetActionView``) and the members drawer
    (``DatasetMembersView``). There are no bulk actions yet, so no
    selection: the select cells are empty slots.

    ``?members=<name>`` is the open drawer, page state rather than list
    state: no list address carries it. A whole page reopens the drawer when
    it names one of the user's own Datasets (``members_open``, and the
    Dataset's ⋯ as where focus returns), and says nothing about any other
    name. The region alone never looks it up."""

    page_template = "login/user_datasets.html"
    region_template = "login/partials/datasets_region.html"
    create_action = dataset_actions.CREATE

    def extra_context(self):
        name = self.request.GET.get("members", "").strip()
        if not name or not self.renders_page(self.request):
            return {}
        pk = own_dataset_pk(self.profile_user, name)
        return {"members_open": {"name": name, "pk": pk}} if pk else {}


# What a draft failing ``DATASET_GATE`` needs, by the failed check's name,
# as the publish dialog asks for it.
GATE_NEEDS = {
    "members": "Add at least one table",
    "topics": "Choose at least one topic",
}

# The actions whose dialog is a form to fill in rather than a confirmation of
# a preflight: Create and Edit.
FORM_ACTIONS = (dataset_actions.CREATE, dataset_actions.EDIT)


class DatasetActionView(DatasetsList, ActionView):
    """One action on the user's own Datasets from the dashboard, through
    ``dataset_actions`` with ``via="dashboard"`` (``ActionView``): create
    and edit, and publish, unpublish and delete, for a row (one
    ``dataset``) or a batch (a comma-joined ``datasets``). The member
    actions are not offered here (404): the members drawer has them.

    - GET: the dialog. Publish on a draft failing the gate names what is
      missing (``GATE_NEEDS``), with "Edit…" beside a missing Topic, and
      offers no confirmation; a published Dataset is passed over, because
      the dashboard offers no republish (the API does). Unpublish states
      what happens in words; delete states that the member Tables stay and,
      for a published Dataset, asks for its name to be typed (``confirm``),
      which the service checks under the lock.
    - POST, done: 204 with ``HX-Trigger: datasets-changed``, the message
      and, for a row that is still there, its menu to focus; a delete
      carries ``gone`` instead.
    - POST, refused (the gate failing by now, say): 409 and
      ``datasets-refused``, the dialog run again.
    - POST, unusable parameters (no Dataset named, a typed confirmation that
      does not match): 400.

    Create and edit are a form, not a confirmation (``FORM_ACTIONS``,
    dataset_form_dialog.html): GET is the form, empty for a create and
    filled with what is stored for an edit; POST saves it. The name is the
    title's (``normalize_dataset_name``, the server's one name rule), never
    a field, and an edit never changes it. A refused save (a taken name, an
    unknown Topic, a missing field) answers 400 with the form as it was
    typed. A done create's ``datasets-changed`` carries ``created``, the new
    Dataset's name, which the members drawer opens on; an edit that changes
    nothing writes nothing and says so.

    A request naming a Dataset that is not the user's own answers 404 and
    writes nothing, alike for another user's draft, another user's published
    Dataset and a name nobody has (``is_unknown``): the dashboard knows only
    the user's own Datasets.
    """

    service = dataset_actions
    actions = (
        dataset_actions.CREATE,
        dataset_actions.EDIT,
        dataset_actions.PUBLISH,
        dataset_actions.UNPUBLISH,
        dataset_actions.DELETE,
    )
    dialog_template = "login/partials/dataset_action_dialog.html"
    form_template = "login/partials/dataset_form_dialog.html"
    params = ("confirm", "title", "description", "topics")
    list_params = ("topics",)

    def is_unknown(self, check):
        return any(
            group.reason in (dataset_actions.NOT_FOUND, dataset_actions.NOT_YOURS)
            for group in check.left_out
        )

    def dialog_context(self, check):
        context = {}
        if check.action == dataset_actions.PUBLISH:
            gate = check.consequences["gate"]
            failed = {name for names in gate.values() for name in names}
            context["needs"] = [
                {"check": check_.name, "text": GATE_NEEDS[check_.name]}
                for check_ in DATASET_GATE
                if check_.name in failed
            ]
            if check.total == 1 and gate:
                # what the gate's links ("Edit…", "Manage tables…") open
                # their target on
                context["gate_dataset"] = (
                    own_datasets(self.profile_user)
                    .filter(name__in=list(gate))
                    .only("pk", "name")
                    .first()
                )
            # where the Datasets will be listed: their own Topics
            context["listed_under"] = [
                capfirst(name)
                for name in Topic.objects.filter(datasets__in=check.eligible)
                .distinct()
                .order_by("name")
                .values_list("name", flat=True)
            ]
        return context

    def _own(self, names):
        """The one Dataset ``names`` names, which must be the user's own;
        anything else is the owner rule's 404."""
        if len(names) != 1:
            raise Http404
        try:
            return dataset_actions.own_dataset(self.profile_user, names[0])
        except (dataset_actions.DatasetNotFound, dataset_actions.NotYourDataset):
            raise Http404

    def _form(
        self, request, action, dataset=None, values=None, errors=None, status=200
    ):
        """The Create or Edit form: ``values`` as typed, or what ``dataset``
        holds (nothing, for a create)."""
        if values is None:
            values = {"title": "", "description": "", "topics": []}
            if dataset is not None:
                metadata = dataset.metadata or {}
                values = {
                    "title": metadata.get("title") or "",
                    "description": metadata.get("description") or "",
                    "topics": list(dataset.topics.values_list("name", flat=True)),
                }
        context = {
            "profile_user": self.profile_user,
            "action": action,
            "dataset": dataset,
            "stored_title": dataset_title(dataset) if dataset is not None else "",
            "values": values,
            "errors": errors or {},
            "topics": topic_choices(),
            "preview": (
                name_preview(values["title"])
                if action == dataset_actions.CREATE
                else None
            ),
        }
        return render(request, self.form_template, context, status=status)

    def _preflight(self, request, action, data):
        if action not in FORM_ACTIONS:
            return super()._preflight(request, action, data)
        action = self._action(action)
        if action == dataset_actions.EDIT:
            return self._form(request, action, self._own(self._names(data)))
        return self._form(request, action)

    def post(self, request, user_id, action):
        if action not in FORM_ACTIONS:
            return super().post(request, user_id, action)
        action = self._action(action)
        params = self._params(request.POST)
        # as the API's serializers take them: surrounding blanks trimmed
        values = {
            "title": params["title"].strip(),
            "description": params["description"].strip(),
            "topics": params["topics"],
        }
        dataset = None
        try:
            if action == dataset_actions.CREATE:
                names = [_created_name(values["title"])]
            else:
                dataset = self._own(self._names(request.POST))
                names = [dataset.name]
            outcome = dataset_actions.execute(
                self.profile_user, action, names, values, via="dashboard"
            )
        except dataset_actions.InvalidParameters as error:
            return self._form(request, action, dataset, values, error.errors, 400)
        except (dataset_actions.DatasetNotFound, dataset_actions.NotYourDataset):
            # gone, or no longer the user's, since the form was opened
            raise Http404
        return self._done(request, outcome)

    def done_detail(self, request, outcome):
        datasets = outcome.datasets
        if outcome.action == dataset_actions.DELETE:
            return {
                "message": _dataset_deleted_message(datasets),
                "gone": [dataset.name for dataset in datasets],
            }
        if outcome.action in FORM_ACTIONS:
            return self._saved_detail(request, outcome)
        if not datasets:
            # passed over at execute: the state asked for held already
            return {"message": _dataset_unchanged_message(outcome)}
        hidden = self.hidden(request, datasets)
        detail = {"message": _dataset_done_message(outcome, hidden)}
        if len(datasets) == 1:
            detail["focus"] = f"menu-{datasets[0].pk}"
        return detail

    def _saved_detail(self, request, outcome):
        """After a create or an edit: what was saved, focus on the row's
        menu and, for a create, the new name (``created``)."""
        dataset = outcome.datasets[0]
        what = _dataset_what([dataset])
        detail = {"focus": f"menu-{dataset.pk}"}
        if outcome.action == dataset_actions.CREATE:
            detail["created"] = dataset.name
            message = f"Created {what} as a private draft, visible only to you."
        elif outcome.changed:
            message = f"Saved {what}."
        else:
            return {
                **detail,
                "message": f"Nothing was changed: {what} is saved that way already.",
            }
        if self.hidden(request, [dataset]):
            message += " It is not shown under the current filter."
        return {**detail, "message": message}


def _created_name(title) -> str:
    """The name a create with ``title`` gets (``normalize_dataset_name``). A
    title that gives none is refused like any other unusable field: required
    when empty, and named for the name otherwise."""
    name = normalize_dataset_name(title)
    if name is None:
        raise dataset_actions.InvalidParameters(
            {"title": dataset_actions.REQUIRED}
            if not title
            else {
                "name": "The title needs a letter or number to make a web address from."
            }
        )
    return name


class DatasetNamePreviewView(ProfileOwnerRequiredMixin, View):
    """The Create form's name preview (``name_preview``): what the typed
    ``title`` would be named and whether it is free, with the Create button
    enabled or not, out of band (dataset_name_preview.html). Reads one
    query and writes nothing; a name taken by another user's draft reads as
    taken and nothing more."""

    @method_decorator(never_cache)
    def get(self, request, user_id):
        return render(
            request,
            "login/partials/dataset_name_preview.html",
            {"preview": name_preview(request.GET.get("title", ""))},
        )


class DatasetMembersBase(ProfileOwnerRequiredMixin, View):
    """What the members drawer's two views share: the Dataset the address
    names, which must be one of the user's own (else 404, alike for another
    user's draft, another user's published Dataset and a name nobody has),
    and the drawer's state as a request carries it: ``search`` and ``page``
    (the members), ``add_search`` and ``add_page`` (the add search)."""

    def _dataset(self, name):
        try:
            return dataset_actions.own_dataset(self.profile_user, name)
        except (dataset_actions.DatasetNotFound, dataset_actions.NotYourDataset):
            raise Http404

    @staticmethod
    def _state(data) -> dict:
        return {
            key: data.get(key, "").strip()
            for key in ("search", "page", "add_search", "add_page")
        }


class DatasetMembersView(DatasetMembersBase):
    """The members drawer for one of the user's own Datasets (#2625): every
    member, 25 per page with a search over them, an add search over the
    Tables the user may assign, and the hand-off to the tables tab. GET
    renders it; POST makes one change through the Dataset action service
    (``members_add`` / ``members_remove``, ``via="dashboard"``) and renders
    it again in place, so it stays open for the next change.

    The drawer's state travels with every request, so an answer shows the
    lists as they were: ``search`` and ``page`` (the members), ``add_search``
    and ``add_page`` (the add search). A request whose ``HX-Target`` is one
    of the two lists (``dataset-members-list``) gets that list alone.

    POST takes ``op`` (``add`` or ``remove``) and ``table``:

    - done: 200, the drawer saying what was done (and which Topics an add
      brought along, and that a published Dataset left without members stays
      published), with ``HX-Trigger: datasets-changed`` carrying ``stay``:
      the list re-fetches behind the drawer, which neither closes nor moves
      focus.
    - nothing to do (already in, not in, no such Table): 200, the drawer
      saying so, no event; nothing is written or stamped.
    - removing a member the user could not add back (a draft or embargoed
      Table they hold no Data editor role on) without ``confirm=yes``: 200,
      the drawer asking, nothing written, no event. GET with ``ask=<table>``
      asks the same without trying, which is what that member's Remove does,
      since the page knows.
    - refused (a Table no longer assignable once locked): 409, the drawer
      with the refusal.
    - unusable (no Table named, an unknown ``op``): 400.

    A Dataset that is not the user's own answers 404 alike for another
    user's draft, another user's published Dataset and a name nobody has:
    the dashboard knows only the user's own Datasets.
    """

    template = "login/partials/dataset_members_drawer.html"
    list_template = "login/partials/dataset_members_list.html"

    def _drawer(self, request, dataset, state, status=200, at=None, kept="", **extra):
        """The drawer, or its member list alone for a request aimed at it.
        ``at`` (the index of a member just removed) and ``kept`` (a member
        the user chose to keep) say where focus goes (``_members_focus``);
        ``extra`` goes to the template: ``message``, ``added``, ``ask``."""
        user = self.profile_user
        members = dataset_members.member_page(
            user, dataset, state["search"], state["page"]
        )
        focus_id = _members_focus(members.rows, at, kept)
        context = {
            "profile_user": user,
            "dataset": dataset,
            "members": members,
            "state": state,
            "focus_id": focus_id,
            **extra,
        }
        if request.headers.get("HX-Target") == "dataset-members-list":
            return render(request, self.list_template, context, status=status)
        context.update(
            title=dataset_title(dataset),
            candidates=dataset_members.candidate_page(
                user, dataset, state["add_search"], state["add_page"]
            ),
            own_count=dataset_members.own_member_count(user, dataset),
            needs=dataset_members.gate_needs(dataset),
        )
        ask = context.get("ask")
        if ask is not None:
            context["ask_row"] = ask
            context["ask_at"] = next(
                (
                    index
                    for index, row in enumerate(members.rows)
                    if row.table.pk == ask.table.pk
                ),
                0,
            )
        return render(request, self.template, context, status=status)

    @method_decorator(never_cache)
    def get(self, request, user_id, dataset_name):
        dataset = self._dataset(dataset_name)
        state = self._state(request.GET)
        extra = {"kept": request.GET.get("kept", "").strip()}
        asked = request.GET.get("ask", "").strip()
        if asked:
            extra["ask"] = dataset_members.lost_member(
                self.profile_user, dataset, asked
            )
        return self._drawer(request, dataset, state, **extra)

    def post(self, request, user_id, dataset_name):
        user = self.profile_user
        dataset = self._dataset(dataset_name)
        state = self._state(request.POST)
        op = request.POST.get("op", "")
        name = request.POST.get("table", "").strip()
        if op not in ("add", "remove"):
            return self._drawer(
                request,
                dataset,
                state,
                status=400,
                message=_problem("Choose a change to make."),
            )
        if op == "remove" and request.POST.get("confirm") != "yes":
            lost = dataset_members.lost_member(user, dataset, name)
            if lost is not None:
                return self._drawer(request, dataset, state, ask=lost)
        action = (
            dataset_actions.MEMBERS_ADD
            if op == "add"
            else dataset_actions.MEMBERS_REMOVE
        )
        topics_before = (
            set(dataset.topics.values_list("name", flat=True)) if op == "add" else None
        )
        try:
            outcome = dataset_actions.execute(
                user,
                action,
                [name] if name else [],
                {"dataset": dataset.name},
                via="dashboard",
            )
        except (dataset_actions.DatasetNotFound, dataset_actions.NotYourDataset):
            # deleted, or no longer the user's, since the drawer opened
            raise Http404
        except dataset_actions.InvalidParameters as error:
            message = " ".join(str(text) for text in error.errors.values())
            return self._drawer(
                request, dataset, state, status=400, message=_problem(message)
            )
        except dataset_actions.ActionRefused as refusal:
            return self._drawer(
                request, dataset, state, status=409, message=_problem(refusal.message)
            )

        if not outcome.tables:
            return self._drawer(
                request,
                dataset,
                state,
                message=_note(_members_unchanged_message(op, name, outcome)),
            )
        table = outcome.tables[0]
        extra = {}
        if op == "add":
            seeded = sorted(
                set(dataset.topics.values_list("name", flat=True)) - topics_before
            )
            message = _members_added_message(table, seeded)
            extra["added"] = table.pk
        else:
            message = _members_removed_message(table, dataset)
            extra["at"] = request.POST.get("at", "")
        response = self._drawer(
            request, dataset, state, message=_done(message), **extra
        )
        response["HX-Trigger"] = json.dumps({"datasets-changed": {"stay": True}})
        return response


class DatasetMembersSearchView(DatasetMembersBase):
    """The members drawer's add search (``DatasetMembersView``): one page of
    the Tables the user may add, for ``add_search`` and ``add_page``. With
    nothing typed it lists the user's own Tables. GET only."""

    @method_decorator(never_cache)
    def get(self, request, user_id, dataset_name):
        dataset = self._dataset(dataset_name)
        state = self._state(request.GET)
        return render(
            request,
            "login/partials/dataset_members_results.html",
            {
                "profile_user": self.profile_user,
                "dataset": dataset,
                "candidates": dataset_members.candidate_page(
                    self.profile_user, dataset, state["add_search"], state["add_page"]
                ),
                "state": state,
            },
        )


def _members_focus(rows, at, kept) -> str:
    """The id of the control the drawer should focus after a change took
    away the one that was focused, or "" to keep the same id: after a
    removal the Remove now at the removed member's place (``at``), or the
    add search when no member is left on the page; after "Keep it" the kept
    member's Remove (``kept``)."""
    if at is not None:
        if not rows:
            return "dataset-members-add-search"
        try:
            index = int(at)
        except ValueError:
            index = 0
        row = rows[min(max(index, 0), len(rows) - 1)]
        return f"dataset-members-remove-{row.table.pk}"
    for row in rows:
        if kept and row.table.name == kept:
            return f"dataset-members-remove-{row.table.pk}"
    return ""


def _done(text) -> dict:
    return {"level": "success", "text": text}


def _note(text) -> dict:
    return {"level": "info", "text": text}


def _problem(text) -> dict:
    return {"level": "danger", "text": text}


def _members_added_message(table, seeded) -> str:
    """What an add says: the Table, and the Topics it brought along, which
    may be what the Dataset still needed to be published."""
    message = f"Added {_title(table)}."
    if len(seeded) == 1:
        message += f" Its topic {seeded[0]} was added to the dataset."
    elif seeded:
        message += f" Its topics {', '.join(seeded)} were added to the dataset."
    return message


def _members_removed_message(table, dataset) -> str:
    """What a removal says, and that a published Dataset left without
    members stays published: the gate judges publishing, not what follows."""
    message = f"Removed {_title(table)}."
    if dataset.is_published and not dataset.tables.exists():
        message += (
            " The dataset holds no tables now and stays published; unpublish it"
            " from the list if that is not what you want."
        )
    return message


def _members_unchanged_message(op, name, outcome) -> str:
    reasons = {group.reason for group in outcome.left_out}
    if dataset_actions.NO_SUCH_TABLE in reasons:
        return f"Nothing was changed: there is no table \u201c{name}\u201d."
    if op == "add":
        return f"Nothing was changed: \u201c{name}\u201d is already in this dataset."
    return f"Nothing was changed: \u201c{name}\u201d is not in this dataset."


def _dataset_what(datasets) -> str:
    if len(datasets) == 1:
        return f"\u201c{dataset_title(datasets[0])}\u201d"
    return f"{len(datasets)} datasets"


def _dataset_done_message(outcome, hidden) -> str:
    """The message after a publish or an unpublish, and whether the rows it
    changed still show under the current filter."""
    datasets = outcome.datasets
    what = _dataset_what(datasets)
    if outcome.action == dataset_actions.PUBLISH:
        message = f"Published {what}. Anyone can now find it under its topics."
        if len(datasets) > 1:
            message = f"Published {what}. Anyone can now find them under their topics."
    elif len(datasets) == 1:
        message = f"Unpublished {what}. It is a draft again, visible only to you."
    else:
        message = f"Unpublished {what}. They are drafts again, visible only to you."
    if hidden and len(datasets) == 1:
        message += " It is not shown under the current filter."
    elif hidden and len(hidden) == len(datasets):
        message += " They are not shown under the current filter."
    elif hidden:
        message += f" {len(hidden)} of them are not shown under the current filter."
    return message


def _dataset_unchanged_message(outcome) -> str:
    names = [name for group in outcome.left_out for name in group.names]
    what = f"\u201c{names[0]}\u201d" if len(names) == 1 else "These datasets"
    if outcome.action == dataset_actions.PUBLISH:
        return f"Nothing was changed: {what} was published already."
    return f"Nothing was changed: {what} was a draft already."


def _dataset_deleted_message(datasets) -> str:
    """The message after a delete: the member Tables were kept."""
    members = sum(dataset.members for dataset in datasets)
    kept = (
        " Its member tables were kept."
        if len(datasets) == 1
        else " Their member tables were kept."
    )
    return f"Deleted {_dataset_what(datasets)}.{kept if members else ''}"


##############################################################################
#          User Open Peer Review related views & partial views for htmx      #
##############################################################################


class ReviewsView(ProfileOwnerRequiredMixin, View):
    @method_decorator(never_cache)
    def get(self, request, user_id):
        """
        Load the reviews the user identifyes as reviewer and contributor for.

        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """
        user = self.profile_user

        ##################################################################
        # get reviewer pov reviews
        ##################################################################
        reviewed_context = {}

        # get all reviews where current user is the reviewer
        peer_review_reviews = PeerReviewManager.filter_opr_by_reviewer(
            reviewer_user=user
        )

        latest_review = peer_review_reviews.last()
        if latest_review is not None:
            reviewed_context.update(
                {"reviews_available": True}
            )  # TODO: use this in template

            # Get the latest open peer review (where this user is the reviewer)
            active_peer_review_revewier = (
                PeerReviewManager.filter_latest_open_opr_by_reviewer(reviewer_user=user)
            )

            # if active_peer_review_revewier is not None:
            #     review_history = peer_review_reviews.exclude(
            #         pk=active_peer_review_revewier.pk
            #     )  # noqa
            # else:
            # Handle the case when active_peer_review_revewier is None.
            # Maybe set review_history to some default value or just leave
            # it as None.
            # review_history = None

            # Context da for the "All reviews" section on the profile page
            reviewed_context.update(
                {
                    "latest": latest_review,  # mainly used to check if review exists
                    # "history": review_history,
                }
            )

            if active_peer_review_revewier is not None:
                current_manager = PeerReviewManager.load(active_peer_review_revewier)
                # Update days open value stored in peerReviewManager table
                current_manager.update_open_since(opr=active_peer_review_revewier)
                latest_review_status = current_manager.status
                latest_review_days_open = current_manager.is_open_since
                current_reviewer = current_manager.current_reviewer

                # All data in this dict is related to the latest active opr
                # Context da for the "Active reviews" section on the profile page
                reviewed_context.update(
                    {
                        # will always be updated if there is another opr available
                        "latest_active": active_peer_review_revewier,
                        "latest_status": latest_review_status,
                        "current_reviewer": current_reviewer,
                        "latest_days_open": latest_review_days_open,
                    }
                )
            else:  # TODO remove else if not causes error in template
                reviewed_context.update(
                    {
                        "latest_active": None,
                        "latest_status": None,
                        "current_reviewer": None,
                        "latest_days_open": None,
                    }
                )
        else:
            reviewed_context.update(
                {"reviews_available": False}
            )  # TODO: use this in template

        # Sort the reviews by table name
        sorted_reviews = sorted(peer_review_reviews, key=lambda x: x.table)
        # Group the reviews by table name
        organizationed_reviews = {
            k: list(v) for k, v in groupby(sorted_reviews, key=lambda x: x.table)
        }

        ##################################################################
        # get contributor pov reviews
        ##################################################################
        reviewed_contributions_context = {}
        peer_review_contributions = PeerReviewManager.filter_opr_by_contributor(
            contributor_user=user
        )
        latest_reviewed_contribution = peer_review_contributions.last()
        if latest_reviewed_contribution is not None:
            reviewed_contributions_context.update(
                {"reviews_available": True}
            )  # TODO: use this in template

            # Get the latest open peer review (where this user is the contributor)
            active_peer_review_contributor = (
                PeerReviewManager.filter_latest_open_opr_by_contributor(
                    contributor_user=user
                )
            )
            if active_peer_review_contributor is not None:
                reviewed_contribution_history = peer_review_contributions.exclude(
                    pk=active_peer_review_contributor.pk
                )
            else:
                # Handle the case when active_peer_review_contributor is None.
                # Maybe set reviewed_contribution_history to some default
                # value or just leave it as None.
                reviewed_contribution_history = None

            reviewed_contributions_context = {
                # mainly used to check if review exists
                "latest": latest_reviewed_contribution,
                "history": reviewed_contribution_history,
            }

            if active_peer_review_contributor is not None:
                current_manager = PeerReviewManager.load(active_peer_review_contributor)
                # Update days open value stored in peerReviewManager table
                current_manager.update_open_since(opr=active_peer_review_contributor)
                latest_reviewed_contribution_status = current_manager.status
                latest_reviewed_contribution_days_open = current_manager.is_open_since
                current_reviewer = current_manager.current_reviewer

                # All data in this dict is related to the latest active opr
                # Context da for the "Active reviews" section on the profile page
                reviewed_contributions_context.update(
                    {
                        # will always be updated if there is another opr available
                        "latest_active": active_peer_review_contributor,
                        "latest_status": latest_reviewed_contribution_status,
                        "current_reviewer": current_reviewer,
                        "latest_days_open": latest_reviewed_contribution_days_open,
                    }
                )
            else:  # TODO remove else if not causes error in template
                reviewed_contributions_context.update(
                    {
                        "latest_active": None,
                        "latest_status": None,
                        "current_reviewer": None,
                        "latest_days_open": None,
                    }
                )
        else:
            reviewed_contributions_context.update(
                {"reviews_available": False}
            )  # TODO: use this in template

        # Sort the reviews by table name
        sorted_contributions = sorted(peer_review_contributions, key=lambda x: x.table)
        # Group the reviews by table name
        organizationed_contributions = {
            k: list(v) for k, v in groupby(sorted_contributions, key=lambda x: x.table)
        }
        latest_review_id = latest_review.pk if latest_review is not None else None

        return render(
            request,
            "login/user_review.html",
            {
                "profile_user": user,
                "reviewer_reviewed": reviewed_context,
                "reviewer_reviewed_organizationed": organizationed_reviews,
                "contributor_reviewed": reviewed_contributions_context,
                "contributor_reviewed_organizationed": organizationed_contributions,
                "latest_review_id": latest_review_id,
            },
        )


@require_POST
def delete_peer_review_simple_view(request):
    """
    Delete a peer review by ``review_id`` read from the JSON request body
    (used by the profile page). Delegates to the single ``delete_peer_review``
    implementation so both delete entry points behave identically.
    """
    data = json.loads(request.body)
    review_id = data.get("review_id")
    return delete_peer_review(review_id, request.user)


class SettingsView(ProfileOwnerRequiredMixin, View):
    @method_decorator(never_cache)
    def get(self, request, user_id):
        """
        Load the user identified by user_id and is OAuth-token.
            If latter does not exist yet, create one.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """

        for user in OepUser.objects.all():
            Token.objects.get_or_create(user=user)
        user = self.profile_user
        token = Token.objects.get(user=request.user)
        user_organizations = request.user.memberships
        return render(
            request,
            "login/user_settings.html",
            {"profile_user": user, "token": token, "organizations": user_organizations},
        )


###########################################################################
#            Organization related views & partial views for htmx          #
###########################################################################


class OrganizationsView(ProfileOwnerRequiredMixin, View):
    @method_decorator(never_cache)
    def get(self, request, user_id: int):
        """
        Get all organizations where the current user is listed as member. Also
        indicate weather the user is the organization Admin or Member.
        Additionally provide context information like member count or
        Group description.

        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """

        user = self.profile_user

        return render(
            request,
            "login/organizations.html",
            {"profile_user": user},
        )


# TODO: should be require_POST?
@login_required
def organization_leave_view(request, organization_id: int):
    """ """
    user: OepUser = request.user
    user_id: int = request.user.id
    organization, membership = membership_or_404(request.user, organization_id)

    members = (
        Membership.objects.filter(group=organization).exclude(user=user.pk).count()
    )
    if members == 0:
        return HttpResponse(
            "Please delete the organization instead (you are the only member)."
        )

    if membership.level >= ADMIN_PERM:
        admins = (
            Membership.objects.filter(group=organization, level=ADMIN_PERM)
            .exclude(user=user.pk)
            .count()
        )
        if admins == 0:
            return HttpResponse("An organization needs at least one admin!")

    membership.delete()
    response = HttpResponse()
    response["HX-Redirect"] = reverse(
        "login:organizations", kwargs={"user_id": user_id}
    )
    return response


@login_required
def organization_delete_view(request, organization_id: int):
    """View to delete an organization."""
    organization, _ = membership_or_404(
        request.user, organization_id, min_level=ADMIN_PERM
    )
    organization.delete()
    messages.add_message(
        request,
        level=messages.INFO,
        message="Organization deleted!",
        extra_tags="primary",
    )
    response = HttpResponse()
    response["HX-Redirect"] = reverse(
        "login:organizations", kwargs={"user_id": request.user.id}
    )
    return response


class OrganizationListView(ProfileOwnerRequiredMixin, View):
    @method_decorator(never_cache)
    def get(self, request, user_id: int):
        """
        TBD
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """
        user = self.profile_user

        return render(
            request,
            "login/partials/organizations.html",
            {"profile_user": user},
        )


class OrganizationManagementView(LoginRequiredMixin, View):
    """Create an organization, or edit one the caller administers.

    The login mixin comes first in the bases, see ProfileOwnerRequiredMixin.
    """

    @method_decorator(never_cache)
    def get(self, request, organization_id=None):
        """
        Load the chosen action(create or edit) for an organization.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param organization_id: An organization id
        :return: Profile renderer
        """
        is_admin = False
        can_delete = False
        can_edit = False
        organization = None
        if organization_id:
            organization, membership = membership_or_404(request.user, organization_id)

            # In case the organization is down to one member make sure
            # the remaining user gets admin permissions
            if len(organization.memberships.all()) == 1:
                membership.level = ADMIN_PERM
                membership.save()

            if membership.level < WRITE_PERM:
                raise PermissionDenied
            elif membership.level == ADMIN_PERM:
                is_admin = True
            elif membership.level == DELETE_PERM:
                can_delete = True
            elif membership.level == WRITE_PERM:
                can_edit = WRITE_PERM

            form = OrganizationForm(instance=organization)
        else:
            form = OrganizationForm()

        organization_tables = None
        if organization:
            organization_tables = get_tables_for_organization(organization=organization)

        # Redirect if the request is not triggered using htmx methods
        if not is_htmx(request):
            return redirect("login:organizations", user_id=request.user.id)

        return render(
            request,
            "login/partials/organization_management.html",
            {
                "form": form,
                "organization": organization,
                "choices": Membership.choices,
                "organization_tables": organization_tables,
                "is_admin": is_admin,
                "can_delete": can_delete,
                "can_edit": can_edit,
            },
        )

    def post(self, request, organization_id=None):
        """
        Performs selected action(save or delete) for an organization.
        If an organization name already exists, then a error will be output.
        The selected users become members of this organization.
        The organization admin is already set.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param organization_id: An organization id
        :return: Profile renderer
        """
        organization = None
        if organization_id:
            # who may edit is settled before the form touches the instance
            organization, _ = membership_or_404(
                request.user, organization_id, min_level=ADMIN_PERM
            )

        form = OrganizationForm(request.POST, instance=organization)
        if not form.is_valid():
            return render(
                request,
                "login/partials/organization_form.html",
                {"form": form},
            )

        if organization_id:
            organization = form.save()
            return render(
                request,
                "login/partials/organization_form.html",
                {"form": form, "organization": organization},
            )

        # a new organization and its first admin are one write, so an
        # organization never exists without an owner
        with transaction.atomic():
            organization = form.save()
            Membership.objects.create(
                user=request.user, group=organization, level=ADMIN_PERM
            )
        messages.add_message(
            request,
            level=messages.INFO,
            message="Organization created! Edit the organization to invite members.",
            extra_tags="primary",
        )
        response = HttpResponse()
        response["HX-Redirect"] = reverse(
            "login:organizations", kwargs={"user_id": request.user.pk}
        )
        return response


class OrganizationMembersView(LoginRequiredMixin, TemplateView):
    """The member list of an organization, for its members only, and the
    member changes their level allows.

    The login mixin comes first in the bases, see ProfileOwnerRequiredMixin.
    """

    template_name = "login/partials/organization_members.html"

    def get_context_data(self, **kwargs):
        """Render context."""
        context = super(OrganizationMembersView, self).get_context_data(**kwargs)

        organization, membership = membership_or_404(
            self.request.user, self.kwargs["organization_id"]
        )
        is_admin = membership.level >= ADMIN_PERM

        context["organization"] = organization
        context["choices"] = Membership.choices
        context["is_admin"] = is_admin
        return context

    def post(self, request, organization_id: int):
        """
        Performs selected action(save or delete) for an organization.
        If a organization name already exists, then a error will be output.
        The selected users become members of this organization.
        The organization admin is already set.
        :param request: A HTTP-request object sent by the Django framework.
        :param organization_id: An organization id
        :return: get-request -> Profile renderer, post-request ->
        """
        mode = request.POST["mode"]
        if mode is None:
            return HttpResponseNotAllowed(
                "Post request required field 'mode' not specified!"
            )

        organization, membership = membership_or_404(request.user, organization_id)

        error_message = None
        if mode == "add_user":
            if membership.level < WRITE_PERM:
                raise PermissionDenied
            try:
                user = OepUser.objects.get(name=request.POST["name"])
                membership, _ = Membership.objects.get_or_create(
                    group=organization, user=user
                )
                membership.save()
            except OepUser.DoesNotExist:
                error_message = "User does not exist"

        elif mode == "remove_user":
            if membership.level < DELETE_PERM:
                raise PermissionDenied

            user_to_remove: OepUser = OepUser.objects.get(id=request.POST["user_id"])
            target_membership = Membership.objects.get(
                group=organization.group_ptr, user=user_to_remove
            )

            if request.user.id == user_to_remove.pk:
                error_message = (
                    "Please leave the organization to remove your own membership."
                )
            elif membership.level < target_membership.level:
                error_message = (
                    "You cant remove memberships with higher permission level."
                )
            elif target_membership.level >= ADMIN_PERM:
                admins = (
                    Membership.objects.filter(group=organization, level=ADMIN_PERM)
                    .exclude(user=user_to_remove)
                    .count()
                )
                if admins == 0:
                    error_message = "A organization needs at least one admin"

            # a refusal above is a refusal: nothing is removed
            if error_message is None:
                target_membership.delete()

        elif mode == "alter_user":
            if membership.level < ADMIN_PERM:
                raise PermissionDenied
            user = OepUser.objects.get(id=request.POST["user_id"])
            if user == request.user:
                error_message = "You can not change your own permissions"
            else:
                membership = Membership.objects.get(group=organization, user=user)
                membership.level = request.POST["selected_value"]
                membership.save()
        else:
            raise PermissionDenied
        context = self.get_context_data()
        context["error_message"] = error_message
        return self.render_to_response(context)


##############################################################################
#                    User Profile/Account related views                      #
##############################################################################


class EditUserView(ProfileOwnerRequiredMixin, View):
    @method_decorator(never_cache)
    def get(self, request, user_id):
        form = EditUserForm(instance=request.user)
        return render(request, "login/oepuser_edit_form.html", {"form": form})

    def post(self, request, user_id):
        form = EditUserForm(
            instance=request.user,
            files=request.FILES or None,
            data=request.POST or None,
        )
        if form.is_valid():
            form.save()
            return redirect("login:profile", request.user.id)
        else:
            return render(request, "login/oepuser_edit_form.html", {"form": form})


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("login:settings", kwargs={"user_id": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


class AccountDeleteView_TODO_UNUSED(LoginRequiredMixin, DeleteView):
    """
    TODO: implement tests before we allow user deletion
    see: https://github.com/OpenEnergyPlatform/oeplatform/pull/1181
    """

    model = OepUser
    template_name = "login/delete_account.html"
    success_url = reverse_lazy("logout")

    def get(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        return render(request, "login/delete_account.html", {"profile_user": user})


@profile_owner_required
def account_delete_view(request, profile_user):
    """Account deletion is not offered yet (see AccountDeleteView_TODO_UNUSED).

    The route exists so its link resolves; it answers 404, to its owner too.
    """
    raise Http404


# TODO: should be require_POST?
def token_reset_view(request):
    if request.user.is_authenticated:
        user_token = get_object_or_404(
            Token, user=request.user.id
        )  # Get the current user's token
        user_token.delete()  # Delete the existing token

        new_token = Token.objects.create(user=request.user)

        return HttpResponse(new_token)
    else:
        return HttpResponseForbidden("You are not authorized to reset the token.")


@profile_owner_required
@never_cache
def metadata_review_badge_indicator_icon_file_view(request, profile_user, table_name):
    # is_badge : bool , msg : string -> either error msg or badge name
    table = get_object_or_404(Table, name=table_name)
    context = table.get_review_badge_from_table_metadata()

    return render(
        request,
        "login/partials/badge_icon.html",
        context=context,  # type: ignore (we have Literals in type signature)
    )
