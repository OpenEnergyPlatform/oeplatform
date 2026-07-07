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

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import RedirectView, View
from django.views.generic.edit import DeleteView
from rest_framework.authtoken.models import Token

import login.permissions
from api.serializers import DatasetCreateSerializer, DatasetUpdateSerializer
from api.services.dataset_creation import (
    DatasetNameTaken,
    assignable_tables_for,
    create_dataset,
    update_dataset,
    user_may_assign_table,
)
from dataedit.helper import delete_peer_review
from dataedit.models import Dataset, PeerReviewManager, Table, Topic
from login.forms import EditUserForm, GroupForm
from login.models import GroupMembership, UserGroup
from login.models import myuser as OepUser
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM
from login.utils import get_tables_if_group_assigned

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
    requesting user's own datasets."""
    if profile_user == request.user:
        datasets = (
            Dataset.objects.filter(creator=request.user)
            .order_by("-created_at")
            .prefetch_related("tables")
        )
    else:
        datasets = Dataset.objects.none()
    return {
        "profile_user": profile_user,
        "datasets": datasets,
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

        serializer = DatasetCreateSerializer(data=request.POST)
        form_errors = {}
        if serializer.is_valid():
            try:
                create_dataset(serializer.validated_data, creator=request.user)
            except DatasetNameTaken as error:
                form_errors["name"] = str(error)
        else:
            form_errors = _serializer_errors(serializer)

        form_values = request.POST if form_errors else {}
        context = _datasets_context(request, user, form_errors, form_values)
        return render(request, "login/partials/datasets_sections.html", context)


@login_required
@dataset_creator_required
def dataset_edit_view(request, profile_user, dataset):
    """Inline edit of a dataset card: title and description only, the
    name is immutable. GET returns the form partial, POST saves and
    returns the refreshed card."""
    if request.method == "POST":
        serializer = DatasetUpdateSerializer(data=request.POST)
        if serializer.is_valid():
            update_dataset(dataset, serializer.validated_data)
            return render(
                request,
                "login/partials/dataset_card.html",
                {"dataset": dataset, "profile_user": profile_user},
            )
        form_errors = _serializer_errors(serializer)
        form_values = request.POST
    else:
        form_errors = {}
        form_values = {
            "title": dataset.metadata.get("title", ""),
            "description": dataset.metadata.get("description", ""),
        }

    return render(
        request,
        "login/partials/dataset_edit_form.html",
        {
            "dataset": dataset,
            "profile_user": profile_user,
            "form_errors": form_errors,
            "form_values": form_values,
        },
    )


@login_required
@require_POST
@dataset_creator_required
def dataset_delete_view(request, profile_user, dataset):
    """Delete a dataset (creator only). Member tables are never deleted.
    Returns the refreshed datasets container for the HTMX swap."""
    dataset.delete()
    context = _datasets_context(request, profile_user)
    return render(request, "login/partials/datasets_sections.html", context)


def _render_dataset_manage(request, profile_user, dataset, search=""):
    context = {
        "profile_user": profile_user,
        "dataset": dataset,
        "resources": dataset.tables.all().order_by("name"),
        "picker_tables": assignable_tables_for(request.user, dataset, search)[:20],
        "search": search,
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
        "picker_tables": assignable_tables_for(request.user, dataset, search)[:20],
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
    dataset.tables.add(table)
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
        grouped_reviews = {
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
        grouped_contributions = {
            k: list(v) for k, v in groupby(sorted_contributions, key=lambda x: x.table)
        }
        latest_review_id = latest_review.pk if latest_review is not None else None

        return render(
            request,
            "login/user_review.html",
            {
                "profile_user": user,
                "reviewer_reviewed": reviewed_context,
                "reviewer_reviewed_grouped": grouped_reviews,
                "contributor_reviewed": reviewed_contributions_context,
                "contributor_reviewed_grouped": grouped_contributions,
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
    return delete_peer_review(review_id)


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
        user_groups = None
        if request.user.is_authenticated:
            token = Token.objects.get(user=request.user)
            user_groups = request.user.memberships
        return render(
            request,
            "login/user_settings.html",
            {"profile_user": user, "token": token, "groups": user_groups},
        )


###########################################################################
#            User Group related views & partial views for htmx            #
###########################################################################


class GroupsView(View):
    @method_decorator(never_cache)
    def get(self, request, user_id: int):
        """
        Get all groups where the current user is listed as member. Also
        indicate weather the user is the group Admin or Member.
        Additionally provide context information like member count or
        Group description.

        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """

        # Retrieve the profile owner after a htmx redirect:
        # In case a new Group is created or deleted,
        # check lookup query parameters for user id.
        if request.GET.get("profile_user"):
            user_id = request.GET.get("profile_user")

        user = get_object_or_404(OepUser, pk=user_id)

        return render(
            request,
            "login/user_groups.html",
            {"profile_user": user},
        )


@never_cache
def group_member_count_view(request, group_id: int):
    """
    Return the member count for the current group.

    :param request: A HTTP-request object sent by the Django framework.
    :params group_id: Group id

    :returns: Django HttpResponse with member count
    """
    group = get_object_or_404(UserGroup, id=group_id)
    mem = group.memberships.all()
    member_count = len(mem)

    return HttpResponse(f"{member_count} member")


# TODO: should be require_POST?
@login_required
def group_leave_view(request, group_id: int):
    """ """
    user: OepUser = request.user
    user_id: int = request.user.id
    group = get_object_or_404(UserGroup, id=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)

    errors: dict = {}
    members = GroupMembership.objects.filter(group=group).exclude(user=user.pk).count()
    if members == 0:
        errors["err_leave"] = (
            "Please delete the group instead (you are the only member)."
        )
        return JsonResponse(errors, status=400)

    if membership.level >= ADMIN_PERM:
        admins = (
            GroupMembership.objects.filter(group=group, level=ADMIN_PERM)
            .exclude(user=user.pk)
            .count()
        )
        if admins == 0:
            errors["err_leave"] = "A group needs at least one admin!"
            return JsonResponse(errors, status=400)

    membership.delete()
    response = HttpResponse()
    response["HX-Redirect"] = f"/user/profile/1/groups?profile_user={user_id}"
    return response


class PartialGroupsView(View):
    @method_decorator(never_cache)
    def get(self, request, user_id: int):
        """
        TBD
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """
        user = get_object_or_404(OepUser, pk=user_id)
        user_groups = None
        if request.user.is_authenticated:
            user_groups = request.user.memberships

        return render(
            request,
            "login/partials/groups.html",
            {"profile_user": user, "groups": user_groups},
        )


class GroupManagementView(View, LoginRequiredMixin):
    form_is_valid = False

    @method_decorator(never_cache)
    def get(self, request, group_id=None):
        """
        Load the chosen action(create or edit) for a group.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer
        """
        is_admin = False
        can_delete = False
        can_edit = False
        group = None
        if group_id:
            group = UserGroup.objects.get(id=group_id)
            membership = get_object_or_404(
                GroupMembership, group=group, user=request.user
            )

            # In case the group is down to one member make sure
            # the remaining user gets admin permissions
            if len(group.memberships.all()) == 1:
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

            form = GroupForm(instance=group)
        else:
            form = GroupForm()

        group_tables = None
        if group:
            group_tables = get_tables_if_group_assigned(group=group)

        # Redirect if the request is not triggered using htmx methods
        if "HX-Request" not in request.headers:
            return redirect("login:groups", user_id=request.user.id)

        return render(
            request,
            "login/partials/group_management.html",
            {
                "form": form,
                "group": group,
                "choices": GroupMembership.choices,
                "group_tables": group_tables,
                "is_admin": is_admin,
                "can_delete": can_delete,
                "can_edit": can_edit,
            },
        )

    def post(self, request, group_id=None):
        """
        Performs selected action(save or delete) for a group.
        If a groupname already exists, then a error will be output.
        The selected users become members of this group. The groupadmin is already set.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer
        """
        self.form_is_valid = False
        user = request.user.id
        group = UserGroup.objects.get(id=group_id) if group_id else None
        form = GroupForm(request.POST, instance=group)
        status = None
        if form.is_valid():
            self.form_is_valid = True

        if not self.form_is_valid:
            return render(
                request,
                "login/partials/group_component_form_edit.html",
                {"form": form},
            )

        if self.form_is_valid:
            # status = 201
            if group_id:
                group = form.save()
                membership = get_object_or_404(
                    GroupMembership, group=group, user=request.user
                )
                if membership.level < ADMIN_PERM:
                    raise PermissionDenied
                return render(
                    request,
                    "login/partials/group_component_form_edit.html",
                    {"form": form, "group": group},
                    status=status,
                )
            else:
                group = form.save()
                membership = GroupMembership.objects.create(
                    user=request.user, group=group, level=ADMIN_PERM
                )
                membership.save()
                response = HttpResponse()
                # response["profile_user"] = user
                response["HX-Redirect"] = (
                    f"/user/profile/1/groups?create_msg=True&profile_user={user}"
                )
                return response


class PartialGroupMemberManagementView(View, LoginRequiredMixin):
    @method_decorator(never_cache)
    def get(self, request, group_id: int):
        """
        Renders the group detail page component for user invites and
        permissions.

        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer
        """
        group = get_object_or_404(UserGroup, pk=group_id)
        is_admin = False
        membership = GroupMembership.objects.filter(
            group=group, user=request.user
        ).first()
        if membership:
            is_admin = membership.level >= ADMIN_PERM
        return render(
            request,
            "login/partials/group_component_membership.html",
            {"group": group, "choices": GroupMembership.choices, "is_admin": is_admin},
        )

    def post(self, request, group_id: int):
        """
        Performs selected action(save or delete) for a group.
        If a groupname already exists, then a error will be output.
        The selected users become members of this group. The groupadmin is already set.
        :param request: A HTTP-request object sent by the Django framework.
        :param group_id: An group id
        :return: get-request -> Profile renderer, post-request ->
        """
        mode = request.POST["mode"]
        if mode is None:
            return HttpResponseNotAllowed(
                "Post request required field 'mode' not specified!"
            )

        group = get_object_or_404(UserGroup, id=group_id)
        membership = get_object_or_404(GroupMembership, group=group, user=request.user)

        errors = {}
        if mode == "remove_user":
            if membership.level < login.permissions.DELETE_PERM:
                raise PermissionDenied

            user_to_remove: OepUser = OepUser.objects.get(id=request.POST["user_id"])
            target_membership = GroupMembership.objects.get(
                group=group, user=user_to_remove
            )

            if request.user.id == user_to_remove.pk:
                errors["name"] = "Please leave the group to remove your own membership."
                return JsonResponse(errors, status=400)

            elif target_membership.level >= ADMIN_PERM:
                admins = (
                    GroupMembership.objects.filter(group=group, level=ADMIN_PERM)
                    .exclude(user=user_to_remove)
                    .count()
                )
                if admins == 0:
                    errors["name"] = "A group needs at least one admin"
                    return JsonResponse(errors, status=405)
            elif membership.level < target_membership.level:
                errors["name"] = (
                    "You cant remove memberships with higher permission level."
                )
                return JsonResponse(errors, status=400)

            target_membership.delete()
            response = HttpResponse(status=204)
            return response

        elif mode == "alter_user":
            if membership.level < login.permissions.ADMIN_PERM:
                raise PermissionDenied
            user = OepUser.objects.get(id=request.POST["user_id"])
            if user == request.user:
                errors["name"] = "You can not change your own permissions"
                # errors['HX-Trigger'] = 'own-permissions-error'
                return JsonResponse(errors, status=405)
            else:
                membership = GroupMembership.objects.get(group=group, user=user)
                membership.level = request.POST["selected_value"]
                membership.save()

        elif mode == "delete_group":
            if membership.level < login.permissions.ADMIN_PERM:
                raise PermissionDenied
            group.delete()
            response = HttpResponse()
            user_id = request.user.id
            response["profile_user"] = user_id
            response["HX-Redirect"] = (
                f"/user/profile/1/groups?delete_msg=True&profile_user={user_id}"
            )
            return response
        else:
            raise PermissionDenied
        return JsonResponse({"success": True})

    # def __add_user(self, request, group):
    #     user = OepUser.objects.filter(id=request.POST["user_id"]).first()
    #     g = user.groups.add(group)
    #     g.save()
    #     return self.get(request)


# TODO: Post should not return render ... Get might never be used
class PartialGroupEditFormView(View, LoginRequiredMixin):
    @method_decorator(never_cache)
    def get(self, request, group_id):
        """
        Returns a edit form component for a group.

        :param request: A HTTP-request object sent by the Django framework.
        :param group_id: An group id
        :return: Profile renderer
        """
        group = get_object_or_404(UserGroup, pk=group_id)
        is_admin = False
        membership = GroupMembership.objects.filter(
            group=group, user=request.user
        ).first()
        if membership:
            is_admin = membership.level >= ADMIN_PERM
        return render(
            request,
            "login/partials/group_component_form_edit.html",
            {"group": group, "choices": GroupMembership.choices, "is_admin": is_admin},
        )

    def post(self, request, group_id):
        """
        Returns a validated edit form component the current group.

        NOTE: This breaks some htmx usage suggestions but currently
        it seems to be very convenient and helps to make the implementation
        quite efficient.

        :param request: A HTTP-request object sent by the Django framework.
        :param group_id: An group id
        :return: Profile renderer
        """

        group = UserGroup.objects.get(id=group_id) if group_id else None
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            if group_id:
                group = form.save()
                membership = get_object_or_404(
                    GroupMembership, group=group, user=request.user
                )
                if membership.level < WRITE_PERM:
                    raise PermissionDenied
                return render(
                    request,
                    "login/partials/group_component_form_edit.html",
                    {"form": form, "group": group},
                    status=201,
                )


class PartialGroupInviteView(View, LoginRequiredMixin):
    @method_decorator(never_cache)
    def get(self, request, group_id):
        group = get_object_or_404(UserGroup, pk=group_id)
        is_admin = False
        membership = GroupMembership.objects.filter(
            group=group, user=request.user
        ).first()
        if membership:
            is_admin = membership.level >= ADMIN_PERM

        return render(
            request,
            "login/partials/group_component_invite_user.html",
            {
                "is_admin": is_admin,
                "group": group,
                "membership": membership,
            },
        )

    def post(self, request, group_id):
        """
        Performs selected action(save or delete) for a group.
        If a groupname already exists, then a error will be output.
        The selected users become members of this group.

        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An group id
        :return: Profile renderer
        """
        mode = request.POST.get("mode")
        if mode is None:
            return HttpResponseNotAllowed("Mode not specified")

        group = get_object_or_404(UserGroup, id=group_id)
        # group_member_count = group.memberships.all
        membership = get_object_or_404(GroupMembership, group=group, user=request.user)

        context = {}
        if mode == "add_user":
            if membership.level < login.permissions.WRITE_PERM:
                raise PermissionDenied
            try:
                user = OepUser.objects.get(name=request.POST["name"])
                membership, _ = GroupMembership.objects.get_or_create(
                    group=group, user=user
                )
                membership.save()
                context["added_user"] = user.pk
                return JsonResponse(context, status=201)
            except OepUser.DoesNotExist:
                context["error"] = "User does not exist"
                return JsonResponse(context, status=404)
        else:
            raise PermissionDenied
        # return HttpResponse(context, status=201)


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
