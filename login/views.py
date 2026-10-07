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
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import RedirectView, TemplateView, View
from django.views.generic.edit import DeleteView
from rest_framework.authtoken.models import Token

from api.services import table_actions
from dataedit.helper import delete_peer_review
from dataedit.models import PeerReviewManager, Table
from login import table_roles
from login.access import (
    ProfileOwnerRequiredMixin,
    is_htmx,
    membership_or_404,
    profile_owner_required,
)
from login.datasets_tab import dataset_rows, datasets_listing, own_datasets
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

    def dialog_context(self):
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
    Datasets (``ListTabView``). It offers no actions yet, so no selection:
    its select and menu cells are empty slots."""

    page_template = "login/user_datasets.html"
    region_template = "login/partials/datasets_region.html"


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
