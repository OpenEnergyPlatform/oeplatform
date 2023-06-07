from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, View
from django.views.generic.edit import DeleteView, UpdateView

from itertools import groupby

import login.models as models
from dataedit.models import Table, PeerReviewManager

from .forms import ChangeEmailForm, CreateUserForm, DetachForm, EditUserForm, GroupForm
from .models import ADMIN_PERM, GroupMembership, UserGroup
from .models import myuser as OepUser


class TablesView(View):
    def get(self, request, user_id):
        """
        Load the user identified by user_id and is OAuth-token.
            If latter does not exist yet, create one.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """
        user = get_object_or_404(OepUser, pk=user_id)

        # get all tables and optimize query
        tables = Table.objects.all().select_related()
        # get all tables the user got write perm on
        user_tables = [
            table
            for table in tables
            if user.get_table_permission_level(table) >= models.WRITE_PERM
        ]  # WRITE_PERM = 4
        # prepare data for template
        tables = [{"name": table.name, "schema": table.schema} for table in user_tables]

        # get name of schema form FK object
        for table in tables:
            table["schema"] = table["schema"].name

        return render(
            request, "login/user_tables.html", {"tables": tables, "profile_user": user}
        )


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
        peer_review_reviews = PeerReviewManager.filter_opr_by_reviewer(
            reviewer_user=user
        )
        latest_review = peer_review_reviews.last()
        print(latest_review)
        if latest_review is not None:
            review_history = peer_review_reviews.exclude(pk=latest_review.pk)
            current_manager = PeerReviewManager.load(latest_review)
            # Update days open value stored in peerReviewManager table
            current_manager.update_open_since(opr=latest_review)
            latest_review_status = current_manager.status
            latest_review_days_open = current_manager.is_open_since
            current_reviewer = current_manager.current_reviewer
            reviewed_context = {
                "latest": latest_review,
                "latest_status": latest_review_status,
                "current_reviewer": current_reviewer,
                "latest_days_open": latest_review_days_open, 
                "history": review_history,
            }
        else:
            reviewed_context = None

        # Sort the reviews by table name
        sorted_reviews = sorted(peer_review_reviews, key=lambda x: x.table)
        # Group the reviews by table name
        grouped_reviews = {
            k: list(v) for k, v in groupby(sorted_reviews, key=lambda x: x.table)
        }

        ##################################################################
        # get contributor pov reviews
        ##################################################################
        peer_review_contributions = PeerReviewManager.filter_opr_by_contributor(
            contributor_user=user
        )
        latest_reviewed_contribution = peer_review_contributions.last()
        if latest_reviewed_contribution is not None:
            reviewed_contribution_history = peer_review_contributions.exclude(
                pk=latest_reviewed_contribution.pk
            )
            current_manager = PeerReviewManager.load(latest_reviewed_contribution)
            # Update days open value stored in peerReviewManager table
            current_manager.update_open_since(opr=latest_reviewed_contribution)
            latest_reviewed_contribution_status = current_manager.status
            latest_reviewed_contribution_days_open = current_manager.is_open_since
            reviewed_contributions_context = {
                "latest": latest_reviewed_contribution,
                "latest_status": latest_reviewed_contribution_status,
                "latest_days_open": latest_reviewed_contribution_days_open,
                "history": reviewed_contribution_history,
            }
        else:
            reviewed_contributions_context = None

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
        if request.user.is_authenticated:
            token = Token.objects.get(user=request.user)
        return render(
            request, "login/user_settings.html", {"profile_user": user, "token": token}
        )


class GroupManagement(View, LoginRequiredMixin):
    def get(self, request):
        """
        Load and list the available groups by groupadmin.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :return: Profile renderer
        """

        membership = request.user.memberships
        return render(
            request, "login/list_memberships.html", {"membership": membership}
        )


class GroupCreate(View, LoginRequiredMixin):
    def get(self, request, group_id=None):
        """
        Load the chosen action(create or edit) for a group.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer
        """

        if group_id:
            group = UserGroup.objects.get(id=group_id)
            form = GroupForm(instance=group)
            membership = get_object_or_404(
                GroupMembership, group=group, user=request.user
            )
            if membership.level < ADMIN_PERM:
                raise PermissionDenied
        else:
            form = GroupForm()
        return render(request, "login/group_create.html", {"form": form})

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
        group = UserGroup.objects.get(id=group_id) if group_id else None
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            if group_id:
                group = form.save()
                membership = get_object_or_404(
                    GroupMembership, group=group, user=request.user
                )
                if membership.level < ADMIN_PERM:
                    raise PermissionDenied
            else:
                group = form.save()
                membership = GroupMembership.objects.create(
                    user=request.user, group=group, level=ADMIN_PERM
                )
                membership.save()
            return redirect("/user/groups/{id}".format(id=group.id), {"group": group})
        else:
            return render(request, "login/group_create.html", {"form": form})


class GroupView(View, LoginRequiredMixin):
    def get(self, request, group_id):
        """
        Load the chosen action(create or edit) for a group.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer
        """
        group = get_object_or_404(UserGroup, pk=group_id)
        return render(
            request,
            "login/group.html",
            {"group": group},
        )


class GroupEdit(View, LoginRequiredMixin):
    def get(self, request, group_id):
        """
        Load the chosen action(create or edit) for a group.
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
            "login/change_form.html",
            {"group": group, "choices": GroupMembership.choices, "is_admin": is_admin},
        )

    def post(self, request, group_id):
        """
        Performs selected action(save or delete) for a group.
        If a groupname already exists, then a error will be output.
        The selected users become members of this group. The groupadmin is already set.
        :param request: A HTTP-request object sent by the Django framework.
        :param user_id: An user id
        :param user_id: An group id
        :return: Profile renderer
        """
        mode = request.POST["mode"]
        group = get_object_or_404(UserGroup, id=group_id)
        membership = get_object_or_404(GroupMembership, group=group, user=request.user)

        errors = {}
        if mode == "add_user":
            if membership.level < models.WRITE_PERM:
                raise PermissionDenied
            try:
                user = OepUser.objects.get(name=request.POST["name"])
                membership, _ = GroupMembership.objects.get_or_create(
                    group=group, user=user
                )
                membership.save()
            except OepUser.DoesNotExist:
                errors["name"] = "User does not exist"
        elif mode == "remove_user":
            if membership.level < models.DELETE_PERM:
                raise PermissionDenied
            user = OepUser.objects.get(id=request.POST["user_id"])
            membership = GroupMembership.objects.get(group=group, user=user)
            if membership.level >= ADMIN_PERM:
                admins = GroupMembership.objects.filter(group=group).exclude(user=user)
                if not admins:
                    errors["name"] = "A group needs at least one admin"
                else:
                    membership.delete()
            else:
                membership.delete()
        elif mode == "alter_user":
            if membership.level < models.ADMIN_PERM:
                raise PermissionDenied
            user = OepUser.objects.get(id=request.POST["user_id"])
            if user == request.user:
                errors["name"] = "You can not change your own permissions"
            else:
                membership = GroupMembership.objects.get(group=group, user=user)
                membership.level = request.POST["level"]
                membership.save()
        elif mode == "delete_group":
            if membership.level < models.ADMIN_PERM:
                raise PermissionDenied
            group.delete()
            return redirect("/user/groups")
        else:
            raise PermissionDenied
        return render(
            request,
            "login/change_form.html",
            {
                "group": group,
                "choices": GroupMembership.choices,
                "errors": errors,
                "is_admin": True,
            },
        )

    def __add_user(self, request, group):
        user = OepUser.objects.filter(id=request.POST["user_id"]).first()
        g = user.groups.add(group)
        g.save()
        return self.get(request)


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


class ActivationNoteView(FormView):
    template_name = "login/activate.html"
    form_class = ChangeEmailForm
    success_url = "user/activate"

    def form_valid(self, form):
        if self.request.user.is_anonymous or self.request.user.is_mail_verified:
            raise PermissionDenied
        form.save(self.request.user)
        return super(ActivationNoteView, self).form_valid(form)


def activate(request, token):
    token_obj = models.ActivationToken.objects.filter(value=token).first()
    if not token_obj:
        form = ChangeEmailForm()
        form._errors = {
            forms.forms.NON_FIELD_ERRORS: form.error_class(
                ["Your token was invalid or expired"]
            )
        }
        return render(request, "login/activate.html", {"form": form})
    else:
        token_obj.user.is_mail_verified = True
        token_obj.user.save()
        token_obj.delete()
    return redirect("/user/profile/{id}".format(id=token_obj.user.id))
