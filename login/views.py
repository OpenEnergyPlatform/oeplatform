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
from functools import wraps
from itertools import groupby
from urllib.parse import urlsplit

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    QueryDict,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.cache import patch_vary_headers
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import RedirectView, TemplateView, View
from django.views.generic.edit import DeleteView
from rest_framework.authtoken.models import Token

from api.serializers import DatasetCreateSerializer, DatasetUpdateSerializer
from api.services import table_actions
from api.services.dataset_creation import (
    DatasetNameTaken,
    assign_table,
    assignable_tables_for,
    create_dataset,
    normalize_dataset_name,
    set_dataset_topics,
    update_dataset,
    user_may_assign_table,
)
from dataedit.helper import delete_peer_review
from dataedit.models import Dataset, PeerReviewManager, Table, Topic
from login.access import (
    ProfileOwnerRequiredMixin,
    is_htmx,
    membership_or_404,
    profile_owner_required,
)
from login.forms import EditUserForm, OrganizationForm
from login.models import Membership
from login.models import myuser as OepUser
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM
from login.tables_tab import accessible_tables, table_rows, tables_listing
from login.utils import get_tables_for_organization
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

# Pagination
ITEMS_PER_PAGE = 8


# NO_PERM = 0/None WRITE_PERM = 4 DELETE_PERM = 8 ADMIN_PERM = 12

###########################################################################
#            User Tables related views & partial views for htmx           #
###########################################################################


# The results region's id: when it is the element that triggered a request,
# the request is its re-fetch after an action.
REGION_ID = "tables-results"


class TablesView(ProfileOwnerRequiredMixin, View):
    """The tables tab: one list of every Table the user may write.

    A direct load renders the whole page; an htmx request gets only the
    results region, carrying the canonical address of what it shows in
    ``HX-Push-Url`` (defaults left out, the page clamped), so the address bar
    always names the state on screen; the region's own re-fetch after an
    action (``tables-changed``) gets ``HX-Replace-Url`` instead. A history
    restore is a full page, because htmx swaps it into the body.
    """

    @method_decorator(never_cache)
    def get(self, request, user_id):
        user = self.profile_user
        page = tables_listing(user).page(
            accessible_tables(user), request.GET, request.path, rows=table_rows(user)
        )
        context = {
            "profile_user": user,
            "page": page,
            "gates": table_actions.ROLE_GATES,
        }
        if is_htmx(request) and "HX-History-Restore-Request" not in request.headers:
            response = render(request, "login/partials/tables_region.html", context)
            # The region re-fetching itself after an action changes nothing
            # the user navigated to, so it replaces the history entry rather
            # than adding one per action.
            if request.headers.get("HX-Trigger") == REGION_ID:
                response["HX-Replace-Url"] = page.url
            else:
                response["HX-Push-Url"] = page.url
        else:
            response = render(request, "login/user_tables.html", context)
        patch_vary_headers(response, ["HX-Request"])
        return response


class TableActionView(ProfileOwnerRequiredMixin, View):
    """One action on Tables from the dashboard, for a row (one name) or a
    batch: GET is the preflight, POST the execution. Both take the Tables as
    repeated ``table`` parameters and answer HTML for the action dialog.

    - GET: the dialog, from ``table_actions.preflight``.
    - POST, done: 204 with ``HX-Trigger: tables-changed``, carrying the
      message and, for one Table, the id of the row's menu to focus. The
      results region re-fetches itself on that event.
    - POST, refused (a named Table is no longer allowed): 409, the dialog
      re-run with "Nothing was changed: …", and ``HX-Trigger:
      tables-refused`` for the persistent message.
    - POST, unusable parameters (no Topic, the draft pseudo-topic, a
      Dataset that is not the user's own): 400, the dialog with the error
      beside its field.

    The parameters are ``topic`` and ``embargo`` (publish) and ``dataset``
    (the Dataset actions); the preflight reads ``dataset`` too, to leave out
    the Tables already in it or not in it.

    Whether a changed Table is still shown is read off ``HX-Current-URL``,
    the address the request was sent from, through the list's own filters.
    """

    PARAMS = ("topic", "embargo", "dataset")

    def _names(self, data):
        return data.getlist("table")

    def _params(self, data):
        return {key: data.get(key, "") for key in self.PARAMS}

    def _dialog(self, request, check, status=200, **extra):
        context = {
            "profile_user": self.profile_user,
            "preflight": check,
            "topics": table_actions.publish_topics(),
            "embargo_periods": table_actions.EMBARGO_PERIODS,
            "errors": {},
            "values": {},
            **extra,
        }
        return render(
            request, "login/partials/table_action_dialog.html", context, status=status
        )

    def _action(self, action):
        if action not in table_actions.ACTIONS:
            raise Http404
        return action

    @method_decorator(never_cache)
    def get(self, request, user_id, action):
        action = self._action(action)
        params = self._params(request.GET)
        check = table_actions.preflight(
            self.profile_user, action, self._names(request.GET), params
        )
        return self._dialog(request, check, values=params)

    def post(self, request, user_id, action):
        action = self._action(action)
        user = self.profile_user
        names = self._names(request.POST)
        params = self._params(request.POST)
        try:
            outcome = table_actions.execute(
                user, action, names, params, via="dashboard"
            )
        except table_actions.InvalidParameters as error:
            check = table_actions.preflight(user, action, names)
            return self._dialog(
                request, check, status=400, errors=error.errors, values=params
            )
        except table_actions.ActionRefused as refusal:
            response = self._dialog(
                request, refusal.preflight, status=409, notice=refusal.message
            )
            response["HX-Trigger"] = json.dumps(
                {"tables-refused": {"message": refusal.message}}
            )
            return response

        hidden = _not_shown(request, user, outcome.tables)
        detail = {"message": _done_message(outcome, hidden)}
        if len(outcome.tables) == 1:
            detail["focus"] = f"menu-{outcome.tables[0].pk}"
        response = HttpResponse(status=204)
        response["HX-Trigger"] = json.dumps({"tables-changed": detail})
        return response


def _not_shown(request, user, tables) -> list:
    """Which of ``tables`` the list the request came from no longer shows
    under its filters. Empty when the request does not say where it came
    from."""
    current = request.headers.get("HX-Current-URL")
    if not current:
        return []
    query = QueryDict(urlsplit(current).query)
    shown = set(
        tables_listing(user)
        .matching(accessible_tables(user), query)
        .filter(pk__in=[table.pk for table in tables])
        .values_list("pk", flat=True)
    )
    return [table for table in tables if table.pk not in shown]


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
        embargo = dict(table_actions.EMBARGO_PERIODS)[outcome.params["embargo"]]
        if outcome.params["embargo"] != "none":
            message += f", embargoed for {embargo}"
        message += "."
    elif outcome.action == table_actions.UNPUBLISH:
        their = "its" if count == 1 else "their"
        message = f"Unpublished {what}. No longer listed under {their} topics."
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
    elif hidden:
        message += (
            f" Not shown under the current filter: "
            f"{', '.join(_title(table) for table in hidden)}."
        )
    return message


##############################################################################
#           User Datasets related views & partial views for htmx            #
##############################################################################


def _datasets_context(request, profile_user, form_errors=None, form_values=None):
    """Context for the dashboard datasets sections: only ever lists the
    requesting user's own datasets, searchable and paginated so a creator
    with many datasets can still browse them."""
    if profile_user == request.user:
        datasets = (
            Dataset.objects.filter(creator=request.user)
            .order_by("-created_at")
            .prefetch_related("tables", "topics")
        )
    else:
        datasets = Dataset.objects.none()

    search_query = request.GET.get("search", "").strip()
    if search_query:
        datasets = datasets.filter(
            Q(name__icontains=search_query)
            | Q(metadata__title__icontains=search_query)
            | Q(metadata__description__icontains=search_query)
        )

    paginator = Paginator(datasets, ITEMS_PER_PAGE)
    datasets_page = paginator.get_page(request.GET.get("datasets_page", 1))

    return {
        "profile_user": profile_user,
        "datasets_page": datasets_page,
        "search_query": search_query,
        "form_errors": form_errors or {},
        "form_values": form_values or {},
    }


def _serializer_errors(serializer):
    """Flatten DRF serializer errors into one message per field."""
    return {
        field: " ".join(str(message) for message in messages)
        for field, messages in serializer.errors.items()
    }


def dataset_creator_required(view_func):
    """Resolve the dataset for the dataset partial views and enforce that
    only the dataset's creator may act (403 otherwise).

    Stacks under ``profile_owner_required``, which has already settled that
    ``profile_user`` is the caller."""

    @wraps(view_func)
    def wrapper(request, profile_user, dataset_name, *args, **kwargs):
        dataset = get_object_or_404(Dataset, name=dataset_name)
        if dataset.creator is None or dataset.creator != request.user:
            return HttpResponseForbidden(
                "Only the dataset creator may manage this dataset."
            )
        return view_func(request, profile_user, dataset, *args, **kwargs)

    return wrapper


class DatasetsView(ProfileOwnerRequiredMixin, View):
    """Dataset-first dashboard view: list the user's datasets and create
    new ones via HTMX without page reloads. The name is immutable after
    creation; title and description stay editable."""

    @method_decorator(never_cache)
    def get(self, request, user_id):
        user = self.profile_user
        context = _datasets_context(request, user)
        if is_htmx(request):
            return render(request, "login/partials/datasets_sections.html", context)
        return render(request, "login/user_datasets.html", context)

    def post(self, request, user_id):
        user = self.profile_user

        # the permanent URL name is derived from the title, so users can
        # style the title freely without thinking in slugs
        derived_name = normalize_dataset_name(request.POST.get("title", ""))
        data = request.POST.dict()
        if derived_name:
            data["name"] = derived_name

        serializer = DatasetCreateSerializer(data=data)
        form_errors = {}
        if derived_name is None:
            form_errors["title"] = (
                "The title needs at least one letter or number so a web "
                "address name can be derived from it."
            )
        elif serializer.is_valid():
            try:
                create_dataset(serializer.validated_data, creator=request.user)
            except DatasetNameTaken:
                form_errors["title"] = (
                    f"This title gives the web address name '{derived_name}', "
                    "which is already taken. Please choose a different title."
                )
        else:
            form_errors = _serializer_errors(serializer)

        form_values = request.POST if form_errors else {}
        context = _datasets_context(request, user, form_errors, form_values)
        return render(request, "login/partials/datasets_sections.html", context)


@profile_owner_required
@dataset_creator_required
def dataset_edit_view(request, profile_user, dataset):
    """Inline edit of a dataset card: title, description and topics; the
    name is immutable. GET returns the form partial, POST saves and
    returns the refreshed card."""
    if request.method == "POST":
        serializer = DatasetUpdateSerializer(data=request.POST)
        if serializer.is_valid():
            update_dataset(dataset, serializer.validated_data)
            set_dataset_topics(dataset, request.POST.getlist("topics"))
            return render(
                request,
                "login/partials/dataset_card.html",
                {"dataset": dataset, "profile_user": profile_user},
            )
        form_errors = _serializer_errors(serializer)
        form_values = request.POST
        selected_topics = set(request.POST.getlist("topics"))
    else:
        form_errors = {}
        form_values = {
            "title": dataset.metadata.get("title", ""),
            "description": dataset.metadata.get("description", ""),
        }
        selected_topics = set(dataset.topics.values_list("name", flat=True))

    return render(
        request,
        "login/partials/dataset_edit_form.html",
        {
            "dataset": dataset,
            "profile_user": profile_user,
            "form_errors": form_errors,
            "form_values": form_values,
            "available_topics": Topic.objects.exclude(name=PSEUDO_TOPIC_DRAFT).order_by(
                "name"
            ),
            "selected_topics": selected_topics,
        },
    )


@profile_owner_required
@dataset_creator_required
def dataset_card_view(request, profile_user, dataset):
    """A single dataset card, used to close an open edit or manage panel
    back to its card without re-rendering the whole container (which
    would collapse every other open panel)."""
    return render(
        request,
        "login/partials/dataset_card.html",
        {"dataset": dataset, "profile_user": profile_user},
    )


@profile_owner_required
@require_POST
@dataset_creator_required
def dataset_delete_view(request, profile_user, dataset):
    """Delete a dataset (creator only). Member tables are never deleted.
    Returns an empty swap so only this card disappears and other open
    panels keep their state."""
    dataset.delete()
    return HttpResponse("")


PICKER_MAX_RESULTS = 20


def _picker_context(request, dataset, search=""):
    """Picker results capped at PICKER_MAX_RESULTS, with a flag telling
    the template that more matches exist (hint to refine the search)."""
    tables = list(
        assignable_tables_for(request.user, dataset, search)[: PICKER_MAX_RESULTS + 1]
    )
    return {
        "picker_tables": tables[:PICKER_MAX_RESULTS],
        "picker_truncated": len(tables) > PICKER_MAX_RESULTS,
    }


def _render_dataset_manage(request, profile_user, dataset, search=""):
    context = {
        "profile_user": profile_user,
        "dataset": dataset,
        "resources": dataset.tables.all().order_by("name").prefetch_related("topics"),
        "search": search,
        **_picker_context(request, dataset, search),
    }
    return render(request, "login/partials/dataset_manage.html", context)


@profile_owner_required
@dataset_creator_required
def dataset_manage_view(request, profile_user, dataset):
    """Manage panel for a dataset's resources: current tables with draft
    badges and links, plus the picker for adding tables. Creator only."""
    return _render_dataset_manage(request, profile_user, dataset)


@profile_owner_required
@dataset_creator_required
def dataset_table_search_view(request, profile_user, dataset):
    """Picker search: only tables the user may assign under the curation
    rules, minus already assigned ones."""
    search = request.GET.get("q", "").strip()
    context = {
        "profile_user": profile_user,
        "dataset": dataset,
        **_picker_context(request, dataset, search),
    }
    return render(request, "login/partials/dataset_table_search_results.html", context)


@profile_owner_required
@require_POST
@dataset_creator_required
def dataset_assign_view(request, profile_user, dataset):
    table = get_object_or_404(Table, name=request.POST.get("table", ""))
    if not user_may_assign_table(request.user, table):
        return HttpResponseForbidden(
            "Draft or embargoed tables require Data editor on the table, "
            "directly or through an organization."
        )
    assign_table(dataset, table)
    return _render_dataset_manage(request, profile_user, dataset)


@profile_owner_required
@require_POST
@dataset_creator_required
def dataset_unassign_view(request, profile_user, dataset):
    table = dataset.tables.filter(name=request.POST.get("table", "")).first()
    if table is not None:
        dataset.tables.remove(table)
    return _render_dataset_manage(request, profile_user, dataset)


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
