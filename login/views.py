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
from django.core.paginator import Paginator
from django.db.models import F
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
from django.views.generic import RedirectView, TemplateView, View
from django.views.generic.edit import DeleteView
from rest_framework.authtoken.models import Token

import login.permissions
from dataedit.models import PeerReview, PeerReviewManager, Table, Topic
from login.forms import EditUserForm, OrganizationForm
from login.models import Organization, OrganizationMembership
from login.models import myuser as OepUser
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM
from login.utils import get_tables_for_organization

# Pagination
ITEMS_PER_PAGE = 8


# NO_PERM = 0/None WRITE_PERM = 4 DELETE_PERM = 8 ADMIN_PERM = 12

###########################################################################
#            User Tables related views & partial views for htmx           #
###########################################################################


class TablesView(View):
    @method_decorator(never_cache)
    def get(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        tables_set = user.get_tables_queryset(min_permission_level=WRITE_PERM)
        draft_tables = tables_set.filter(is_publish=False).order_by(
            F("date_updated").desc(nulls_last=True), "human_readable_name"
        )
        published_tables = tables_set.filter(is_publish=True).order_by(
            F("date_updated").desc(nulls_last=True), "human_readable_name"
        )

        # Paginate tables
        published_paginator = Paginator(published_tables, ITEMS_PER_PAGE)
        draft_paginator = Paginator(draft_tables, ITEMS_PER_PAGE)

        # Check if the request contains a page
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
        }

        # TODO: Fix this is_ajax as it is outdated according to django documentation ...
        # provide better api endpoint for http requests via HTMX
        if "HX-Request" in request.headers:
            return render(request, "login/partials/user_partial_tables.html", context)
        else:
            return render(request, "login/user_tables.html", context)


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
    Удаление Peer Review по review_id (упрощённый вариант),
    считывая review_id из тела запроса (JSON).
    """
    data = json.loads(request.body)
    review_id = data.get("review_id")  # берем из POST

    if not review_id:
        return JsonResponse({"error": "No review_id in request."}, status=400)

    peer_review = PeerReview.objects.filter(id=review_id).first()
    if peer_review:
        peer_review.delete()
        return JsonResponse({"message": "PeerReview successfully deleted."})
    else:
        return JsonResponse({"error": "PeerReview not found."}, status=404)


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
    membership = get_object_or_404(
        OrganizationMembership, organization=organization, user=request.user
    )

    members = (
        OrganizationMembership.objects.filter(organization=organization)
        .exclude(user=user.pk)
        .count()
    )
    if members == 0:
        return HttpResponse(
            "Please delete the organization instead (you are the only member)."
        )

    if membership.level >= ADMIN_PERM:
        admins = (
            OrganizationMembership.objects.filter(
                organization=organization, level=ADMIN_PERM
            )
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
    membership = get_object_or_404(
        OrganizationMembership, organization=organization, user=request.user
    )
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


class PartialOrganizationsView(View):
    @method_decorator(never_cache)
    def get(self, request, user_id: int):
        """
        TBD
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """
        user = get_object_or_404(OepUser, pk=user_id)
        user_organizations = None
        if request.user.is_authenticated:
            user_organizations = request.user.memberships

        return render(
            request,
            "login/partials/organizations.html",
            {"profile_user": user, "organizations": user_organizations},
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
                OrganizationMembership, organization=organization, user=request.user
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
                "choices": OrganizationMembership.choices,
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
                    OrganizationMembership, organization=organization, user=request.user
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
                membership = OrganizationMembership.objects.create(
                    user=request.user, organization=organization, level=ADMIN_PERM
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


class PartialOrganizationMemberManagementView(TemplateView, LoginRequiredMixin):
    template_name = "login/partials/organization_component_membership.html"

    def get_context_data(self, **kwargs):
        """Render context."""
        context = super(PartialOrganizationMemberManagementView, self).get_context_data(
            **kwargs
        )

        organization = get_object_or_404(
            Organization, pk=self.kwargs["organization_id"]
        )
        is_admin = False
        membership = OrganizationMembership.objects.filter(
            organization=organization, user=self.request.user
        ).first()
        if membership:
            is_admin = membership.level >= ADMIN_PERM

        context["organization"] = organization
        context["choices"] = OrganizationMembership.choices
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
            OrganizationMembership, organization=organization, user=request.user
        )

        error_message = None
        if mode == "add_user":
            if membership.level < login.permissions.WRITE_PERM:
                raise PermissionDenied
            try:
                user = OepUser.objects.get(name=request.POST["name"])
                membership, _ = OrganizationMembership.objects.get_or_create(
                    organization=organization, user=user
                )
                membership.save()
            except OepUser.DoesNotExist:
                error_message = "User does not exist"

        elif mode == "remove_user":
            if membership.level < login.permissions.DELETE_PERM:
                raise PermissionDenied

            user_to_remove: OepUser = OepUser.objects.get(id=request.POST["user_id"])
            target_membership = OrganizationMembership.objects.get(
                organization=organization, user=user_to_remove
            )

            if request.user.id == user_to_remove.pk:
                error_message = (
                    "Please leave the organization to remove your own membership."
                )

            elif target_membership.level >= ADMIN_PERM:
                admins = (
                    OrganizationMembership.objects.filter(
                        organization=organization, level=ADMIN_PERM
                    )
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
                membership = OrganizationMembership.objects.get(
                    organization=organization, user=user
                )
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
        context=context,  # type:ignore (we have Literals in type signature)
    )
