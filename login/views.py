from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import RedirectView, View
from django.views.generic.edit import DeleteView, UpdateView
from rest_framework.authtoken.models import Token

import login.models as models
from dataedit.models import PeerReviewManager
from dataedit.views import schema_whitelist
from login.utils import (
    get_badge_icon_path,
    get_review_badge_from_table_metadata,
    get_tables_if_group_assigned,
    get_user_tables,
    validate_open_data_license,
)
from oeplatform.settings import UNVERSIONED_SCHEMAS

from .forms import (
    CreateUserForm,
    DetachForm,
    EditUserForm,
    GroupForm,
    OEPPasswordChangeForm,
)

# NO_PERM = 0/None WRITE_PERM = 4 DELETE_PERM = 8 ADMIN_PERM = 12
from .models import ADMIN_PERM, DELETE_PERM, WRITE_PERM, GroupMembership, UserGroup
from .models import myuser as OepUser

###########################################################################
#            User Tables related views & partial views for htmx           #
###########################################################################


class TablesView(View):
    def get(self, request, user_id):
        user = get_object_or_404(OepUser, pk=user_id)
        tables = get_user_tables(user_id)
        draft_tables = []
        published_tables = []

        for table in tables:
            permission_level = user.get_table_permission_level(table)
            license_status = validate_open_data_license(django_table_obj=table)

            review_badge = None
            badge_icon = None
            badge_msg = None
            # oemetadata is None by default
            if table.oemetadata:
                review_badge = get_review_badge_from_table_metadata(table)

            if review_badge and review_badge[0]:
                badge_icon = get_badge_icon_path(review_badge[1])

            if review_badge and review_badge[0]:
                badge_msg = review_badge[1]

            # Use attributes in the templates
            table_data = {
                "name": table.name,
                "schema": table.schema.name,
                "table_label": table.human_readable_name,
                "is_publish": table.is_publish,
                "is_reviewed": table.is_reviewed,
                "review_badge_context": {
                    "error_msg": badge_msg,
                    "badge": review_badge,
                    "icon": badge_icon,
                },
                "icon_path": badge_icon,
                "license_status": {
                    "status": license_status[0],
                    "error": license_status[1],
                },
            }

            if permission_level >= models.WRITE_PERM:
                if table.is_publish and table.schema.name not in UNVERSIONED_SCHEMAS:
                    published_tables.append(table_data)
                else:
                    draft_tables.append(table_data)

        # Pagination
        ITEMS_PER_PAGE = 8

        # Paginate tables
        published_paginator = Paginator(published_tables, ITEMS_PER_PAGE)
        draft_paginator = Paginator(draft_tables, ITEMS_PER_PAGE)

        # Check if the request contains a page
        if request.GET.get("published_page"):
            page_number = request.GET.get("published_page")
            published_page_obj = published_paginator.get_page(page_number)
        # Always return page 1 if not requested otherwise
        else:
            published_page_obj = published_paginator.get_page(1)

        if request.GET.get("draft_page"):
            page_number = request.GET.get("draft_page")
            draft_page_obj = draft_paginator.get_page(page_number)
        else:
            draft_page_obj = draft_paginator.get_page(1)

        context = {
            "profile_user": user,
            "draft_tables_page": draft_page_obj,
            "published_tables_page": published_page_obj,
            "schema_whitelist": schema_whitelist,
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

        return render(
            request,
            "login/user_review.html",
            {
                "profile_user": user,
                "reviewer_reviewed": reviewed_context,
                "reviewer_reviewed_grouped": grouped_reviews,
                "contributor_reviewed": reviewed_contributions_context,
                "contributor_reviewed_grouped": grouped_contributions,
            },
        )


class SettingsView(View):
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


def group_member_count(request, group_id: int):
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


@login_required
def group_leave(request, group_id: int):
    """ """
    user: OepUser = request.user
    user_id: int = request.user.id
    group = get_object_or_404(UserGroup, id=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)

    errors: dict = {}
    members = GroupMembership.objects.filter(group=group).exclude(user=user.id).count()
    if members == 0:
        errors[
            "err_leave"
        ] = "Please delete the group instead (you are the only member)."
        return JsonResponse(errors, status=400)

    if membership.level >= ADMIN_PERM:
        admins = (
            GroupMembership.objects.filter(group=group, level=ADMIN_PERM)
            .exclude(user=user.id)
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


class GroupManagement(View, LoginRequiredMixin):
    form_is_valid = False

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
            return redirect("groups", user_id=request.user.id)

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
                response[
                    "HX-Redirect"
                ] = f"/user/profile/1/groups?create_msg=True&profile_user={user}"
                return response


class PartialGroupMemberManagement(View, LoginRequiredMixin):
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
            if membership.level < models.DELETE_PERM:
                raise PermissionDenied

            user_to_remove: OepUser = OepUser.objects.get(id=request.POST["user_id"])
            target_membership = GroupMembership.objects.get(
                group=group, user=user_to_remove
            )

            if request.user.id == user_to_remove.id:
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
                errors[
                    "name"
                ] = "You cant remove memberships with higher permission level."
                return JsonResponse(errors, status=400)

            target_membership.delete()
            response = HttpResponse(status=204)
            return response

        elif mode == "alter_user":
            if membership.level < models.ADMIN_PERM:
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
            if membership.level < models.ADMIN_PERM:
                raise PermissionDenied
            group.delete()
            response = HttpResponse()
            user_id = request.user.id
            response["profile_user"] = user_id
            response[
                "HX-Redirect"
            ] = f"/user/profile/1/groups?delete_msg=True&profile_user={user_id}"
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
class PartialGroupEditForm(View, LoginRequiredMixin):
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


class PartialGroupInvite(View, LoginRequiredMixin):
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
            if membership.level < models.WRITE_PERM:
                raise PermissionDenied
            try:
                user = OepUser.objects.get(name=request.POST["name"])
                membership, _ = GroupMembership.objects.get_or_create(
                    group=group, user=user
                )
                membership.save()
                context["added_user"] = user.id
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


class ProfileUpdateView(UpdateView, LoginRequiredMixin):
    """
    Autogenerate a update form for users.
    """

    model = OepUser
    fields = ["name", "affiliation", "email"]
    template_name_suffix = "_update_form"


class EditUserView(View):
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
            return redirect("/user/profile/{id}".format(id=request.user.id))
        else:
            return render(request, "login/oepuser_edit_form.html", {"form": form})


class CreateUserView(View):
    def get(self, request):
        form = CreateUserForm()
        return render(request, "login/oepuser_create_form.html", {"form": form})

    def post(self, request):
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("activate")
        else:
            return render(request, "login/oepuser_create_form.html", {"form": form})


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("login:settings", kwargs={"user_id": self.request.user.id})


user_redirect_view = UserRedirectView.as_view()


class DetachView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_native:
            raise PermissionDenied
        form = DetachForm(request.user)
        return render(request, "login/detach.html", {"form": form})

    def post(self, request):
        if request.user.is_native:
            raise PermissionDenied
        form = DetachForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")
        else:
            print(form.errors)
            return render(request, "login/detach.html", {"form": form})


class OEPPasswordChangeView(PasswordChangeView):
    template_name = "login/generic_form.html"
    success_url = "/"
    form_class = OEPPasswordChangeForm


class AccountDeleteView(LoginRequiredMixin, DeleteView):
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


def token_reset(request):
    if request.user.is_authenticated:
        user_token = get_object_or_404(
            Token, user=request.user.id
        )  # Get the current user's token
        user_token.delete()  # Delete the existing token

        new_token = Token.objects.create(user=request.user)

        return HttpResponse(new_token)
    else:
        return HttpResponseForbidden("You are not authorized to reset the token.")
