# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Darynarli <“Daryna.Barabanova@rl-institut.de”>
# SPDX-FileCopyrightText: 2025 Jonas Huber <38939526+jh-RLI@users.noreply.github.com>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 MFinkendei <anubis-mf@web.de>
# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@gmail.com>
# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@googlemail.com>
# SPDX-FileCopyrightText: 2025 daryna <Daryna.Martymianova@rl-institut.de>
#
# SPDX-License-Identifier: MIT

from django.conf.urls import include
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import re_path, path

from login import partial_views, views
from login.views import delete_peer_review_simple

# from login.views import AccountDeleteView

urlpatterns = [
    re_path(
        "password_reset/",
        PasswordResetView.as_view(
            html_email_template_name="registration/password_reset_email.html",
            email_template_name="registration/password_reset_email.txt",
            template_name="registration/custom_password_reset_form.html",
        ),
        name="password_reset",
    ),
    re_path(
        "password_reset/done/",
        PasswordResetDoneView.as_view(
            template_name="registration/custom_password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    re_path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="registration/custom_password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    re_path(
        "reset/done/",
        PasswordResetCompleteView.as_view(
            template_name="registration/custom_password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    re_path("^", include("django.contrib.auth.urls")),
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
    re_path(
        r"^profile/(?P<user_id>[\d]+)/password_change$",
        views.OEPPasswordChangeView.as_view(),
        name="input",
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
    re_path(r"^activate/(?P<token>[\w\d\-\s]+)$", views.activate),
    re_path(r"^activate/$", views.ActivationNoteView.as_view(), name="activate"),
    re_path(r"^reset/token$", views.token_reset, name="reset-token"),
    path(
        'delete_peer_review/',
        delete_peer_review_simple,
        name='delete_peer_review_simple'
    ),
]
