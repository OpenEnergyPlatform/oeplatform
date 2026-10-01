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

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import (
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

import login.permissions
from api.serializers import DatasetCreateSerializer, DatasetUpdateSerializer
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
from login.forms import EditUserForm, OrganizationForm
from login.models import Membership, Organization
from login.models import myuser as OepUser
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM
from login.utils import get_tables_for_organization
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

# Pagination
ITEMS_PER_PAGE = 8


# NO_PERM = 0/None WRITE_PERM = 4 DELETE_PERM = 8 ADMIN_PERM = 12

###########################################################################
#            User Tables related views & partial views for htmx           #
###########################################################################


class TablesView(View):

    def _get_filtered_tables(self, user, search_query=""):
        """Return filtered querysets for draft and published tables."""
        tables_set = user.get_tables_queryset(min_permission_level=WRITE_PERM)

        draft_tables = tables_set.filter(is_publish=False).order_by(
            F("date_updated").desc(nulls_last=True), "human_readable_name"
        )
        published_tables = tables_set.filter(is_publish=True).order_by(
            F("date_updated").desc(nulls_last=True), "human_readable_name"
        )

        if search_query:

            q_filter = Q(name__icontains=search_query) | Q(
                human_readable_name__icontains=search_query
            )
            draft_tables = draft_tables.filter(q_filter)
            published_tables = published_tables.filter(q_filter)

        return draft_tables, published_tables

    @method_decorator(never_cache)
    def get(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        search_query = request.GET.get("search", "").strip()
        has_search_param = "search" in request.GET

        draft_tables, published_tables = self._get_filtered_tables(user, search_query)

        # Paginate tables
        published_paginator = Paginator(published_tables, ITEMS_PER_PAGE)
        draft_paginator = Paginator(draft_tables, ITEMS_PER_PAGE)

        published_page = request.GET.get("published_page", 1)
        published_page_obj = published_paginator.get_page(published_page)

        draft_page = request.GET.get("draft_page", 1)
        draft_page_obj = draft_paginator.get_page(draft_page)

        context = {
            "profile_user": user,
            "draft_tables_page": draft_page_obj,
            "published_tables_page": published_page_obj,
            "topics": [t.name for t in Topic.objects.all()],
            "draft_page": draft_page,
            "published_page": published_page,
            "search_query": search_query,
        }

        if "HX-Request" in request.headers and not has_search_param:
            return render(
                request,
                "login/partials/tables_sections.html",
                context,
            )
        else:
            return render(request, "login/user_tables.html", context)


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
    """Resolve profile user and dataset for the dataset partial views and
    enforce that only the dataset's creator may act (403 otherwise)."""

    @wraps(view_func)
    def wrapper(request, user_id, dataset_name, *args, **kwargs):
        dataset = get_object_or_404(Dataset, name=dataset_name)
        if dataset.creator is None or dataset.creator != request.user:
            return HttpResponseForbidden(
                "Only the dataset creator may manage this dataset."
            )
        profile_user = get_object_or_404(OepUser, pk=user_id)
        return view_func(request, profile_user, dataset, *args, **kwargs)

    return wrapper


class DatasetsView(LoginRequiredMixin, View):
    """Dataset-first dashboard view: list the user's datasets and create
    new ones via HTMX without page reloads. The name is immutable after
    creation; title and description stay editable."""

    @method_decorator(never_cache)
    def get(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        context = _datasets_context(request, user)
        if "HX-Request" in request.headers:
            return render(request, "login/partials/datasets_sections.html", context)
        return render(request, "login/user_datasets.html", context)

    def post(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        if user != request.user:
            return HttpResponseForbidden(
                "Datasets can only be created on your own dashboard."
            )

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


@login_required
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


@login_required
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


@login_required
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


@login_required
@dataset_creator_required
def dataset_manage_view(request, profile_user, dataset):
    """Manage panel for a dataset's resources: current tables with draft
    badges and links, plus the picker for adding tables. Creator only."""
    return _render_dataset_manage(request, profile_user, dataset)


@login_required
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


@login_required
@require_POST
@dataset_creator_required
def dataset_assign_view(request, profile_user, dataset):
    table = get_object_or_404(Table, name=request.POST.get("table", ""))
    if not user_may_assign_table(request.user, table):
        return HttpResponseForbidden(
            "Draft or embargoed tables require write permission on the table."
        )
    assign_table(dataset, table)
    return _render_dataset_manage(request, profile_user, dataset)


@login_required
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


class ReviewsView(View):
    @method_decorator(never_cache)
    def get(self, request, user_id):
        """
        Load the reviews the user identifyes as reviewer and contributor for.

        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """
        user = get_object_or_404(OepUser, pk=user_id)

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


class SettingsView(View):
    @method_decorator(never_cache)
    def get(self, request, user_id):
        """
        Load the user identified by user_id and is OAuth-token.
            If latter does not exist yet, create one.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """

        from rest_framework.authtoken.models import Token

        for user in OepUser.objects.all():
            Token.objects.get_or_create(user=user)
        user = get_object_or_404(OepUser, pk=user_id)
        token = None
        user_organizations = None
        if request.user.is_authenticated:
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


class OrganizationsView(View):
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

        user = get_object_or_404(OepUser, pk=user_id)

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
    organization = get_object_or_404(Organization, id=organization_id)
    membership = get_object_or_404(Membership, group=organization, user=request.user)

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
    response["HX-Redirect"] = f"/user/profile/{user_id}/organizations"
    return response


@login_required
def organization_delete_view(request, organization_id: int):
    """View to delete an organization."""
    organization = get_object_or_404(Organization, id=organization_id)
    membership = get_object_or_404(Membership, group=organization, user=request.user)
    if membership.level < login.permissions.ADMIN_PERM:
        raise PermissionDenied
    organization.delete()
    messages.add_message(
        request,
        level=messages.INFO,
        message="Organization deleted!",
        extra_tags="primary",
    )
    response = HttpResponse()
    response["HX-Redirect"] = f"/user/profile/{request.user.id}/organizations"
    return response


class OrganizationListView(View):
    @method_decorator(never_cache)
    def get(self, request, user_id: int):
        """
        TBD
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """
        user = get_object_or_404(OepUser, pk=user_id)

        return render(
            request,
            "login/partials/organizations.html",
            {"profile_user": user},
        )


class OrganizationManagementView(View, LoginRequiredMixin):
    form_is_valid = False

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
            organization = Organization.objects.get(id=organization_id)
            membership = get_object_or_404(
                Membership, group=organization, user=request.user
            )

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
        if "HX-Request" not in request.headers:
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
        self.form_is_valid = False
        user = request.user.id
        organization = (
            Organization.objects.get(id=organization_id) if organization_id else None
        )
        form = OrganizationForm(request.POST, instance=organization)
        status = None
        if form.is_valid():
            self.form_is_valid = True

        if not self.form_is_valid:
            return render(
                request,
                "login/partials/organization_form.html",
                {"form": form},
            )

        if self.form_is_valid:
            # status = 201
            if organization_id:
                organization = form.save()
                membership = get_object_or_404(
                    Membership, group=organization, user=request.user
                )
                if membership.level < ADMIN_PERM:
                    raise PermissionDenied
                return render(
                    request,
                    "login/partials/organization_form.html",
                    {"form": form, "organization": organization},
                    status=status,
                )
            else:
                organization = form.save()
                membership = Membership.objects.create(
                    user=request.user, group=organization, level=ADMIN_PERM
                )
                membership.save()
                messages.add_message(
                    request,
                    level=messages.INFO,
                    message=(
                        "Organization created! "
                        "Edit the organization to invite members."
                    ),
                    extra_tags="primary",
                )
                response = HttpResponse()
                # response["profile_user"] = user
                response["HX-Redirect"] = f"/user/profile/{user}/organizations"
                return response


class OrganizationMembersView(TemplateView, LoginRequiredMixin):
    template_name = "login/partials/organization_members.html"

    def get_context_data(self, **kwargs):
        """Render context."""
        context = super(OrganizationMembersView, self).get_context_data(**kwargs)

        organization = get_object_or_404(
            Organization, pk=self.kwargs["organization_id"]
        )
        is_admin = False
        membership = Membership.objects.filter(
            group=organization, user=self.request.user
        ).first()
        if membership:
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

        organization = get_object_or_404(Organization, id=organization_id)
        membership = get_object_or_404(
            Membership, group=organization, user=request.user
        )

        error_message = None
        if mode == "add_user":
            if membership.level < login.permissions.WRITE_PERM:
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
            if membership.level < login.permissions.DELETE_PERM:
                raise PermissionDenied

            user_to_remove: OepUser = OepUser.objects.get(id=request.POST["user_id"])
            target_membership = Membership.objects.get(
                group=organization.group_ptr, user=user_to_remove
            )

            if request.user.id == user_to_remove.pk:
                error_message = (
                    "Please leave the organization to remove your own membership."
                )

            elif target_membership.level >= ADMIN_PERM:
                admins = (
                    Membership.objects.filter(group=organization, level=ADMIN_PERM)
                    .exclude(user=user_to_remove)
                    .count()
                )
                if admins == 0:
                    error_message = "A organization needs at least one admin"
            elif membership.level < target_membership.level:
                error_message = (
                    "You cant remove memberships with higher permission level."
                )

            target_membership.delete()

        elif mode == "alter_user":
            if membership.level < login.permissions.ADMIN_PERM:
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


class EditUserView(View):
    @method_decorator(never_cache)
    def get(self, request, user_id):
        if not request.user.id == int(user_id):
            raise PermissionDenied
        form = EditUserForm(instance=request.user)
        return render(request, "login/oepuser_edit_form.html", {"form": form})

    def post(self, request, user_id):
        if not request.user.id == int(user_id):
            raise PermissionDenied
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


@never_cache
def metadata_review_badge_indicator_icon_file_view(request, user_id, table_name):
    # is_badge : bool , msg : string -> either error msg or badge name
    table = get_object_or_404(Table, name=table_name)
    context = table.get_review_badge_from_table_metadata()

    return render(
        request,
        "login/partials/badge_icon.html",
        context=context,  # type: ignore (we have Literals in type signature)
    )
