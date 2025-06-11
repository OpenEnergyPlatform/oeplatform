# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Marco Finkendei <https://github.com/MFinkendei>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import path, re_path

from login import partial_views, views
from login.views import delete_peer_review_simple

app_name = "login"
urlpatterns = [
    re_path(
        "password_reset/",
        PasswordResetView.as_view(
            html_email_template_name="account/password_reset_email.html",
            email_template_name="account/password_reset_email.txt",
            template_name="account/custom_password_reset_form.html",
        ),
        name="password_reset",
    ),
    re_path(
        "password_reset/done/",
        PasswordResetDoneView.as_view(
            template_name="account/custom_password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    re_path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="account/custom_password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    re_path(
        "reset/done/",
        PasswordResetCompleteView.as_view(
            template_name="account/custom_password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)$",
        views.TablesView.as_view(),
        name="profile",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/tables$",
        views.TablesView.as_view(),
        name="tables",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/tables/(?P<table_name>[\w]+)/review-badge$",
        partial_views.metadata_review_badge_indicator_icon_file,
        name="metadata-review-badge-icon",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/review$",
        views.ReviewsView.as_view(),
        name="reviews",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/groups$",
        views.GroupsView.as_view(),
        name="groups",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/settings$",
        views.SettingsView.as_view(),
        name="settings",
    ),
    # TODO: implement tests before we allow user deletion
    # re_path(
    #    r"^profile/(?P<user_id>[\d]+)/delete_acc$",
    #    AccountDeleteView.as_view(),
    #    name="account-delete",
    # ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/partial_groups$",
        views.PartialGroupsView.as_view(),
        name="partial-groups",
    ),
    re_path(
        r"^groups/new/$",
        views.GroupManagement.as_view(),
        name="group-create",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/edit$", views.EditUserView.as_view(), name="edit"
    ),
    re_path(
        r"^profile/groups/(?P<group_id>[\w\d_\s]+)/edit$",
        views.GroupManagement.as_view(),
        name="group-edit",
    ),
    re_path(
        r"^groups/(?P<group_id>[\w\d_\s]+)/members$",
        views.PartialGroupMemberManagement.as_view(),
        name="partial-group-membership",
    ),
    re_path(
        r"^groups/(?P<group_id>[\w\d_\s]+)/member/invite$",
        views.PartialGroupInvite.as_view(),
        name="partial-group-invite",
    ),
    re_path(
        r"^groups/(?P<group_id>[\w\d_\s]+)/partial/edit_form$",
        views.PartialGroupEditForm.as_view(),
        name="group-partial-edit-form",
    ),
    re_path(
        r"^groups/(?P<group_id>[\w\d_\s]+)/members/count$",
        views.group_member_count,
        name="count-group-memberships",
    ),
    re_path(
        r"^groups/(?P<group_id>[\w\d_\s]+)/leave$",
        views.group_leave,
        name="group-leave",
    ),
    # re_path(
    #     r"^groups/(?P<group_id>[\w\d_\s]+)/$",
    #     views.GroupView.as_view(),
    # ),
    re_path(r"^register$", views.CreateUserView.as_view()),
    re_path(r"^detach$", views.DetachView.as_view()),
    re_path(r"^reset/token$", views.token_reset, name="reset-token"),
    path("~redirect/", view=views.user_redirect_view, name="redirect"),
    path(
        "delete_peer_review/",
        delete_peer_review_simple,
        name="delete_peer_review_simple",
    ),
]
