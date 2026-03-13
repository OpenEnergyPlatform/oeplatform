"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Marco Finkendei <https://github.com/MFinkendei>
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import path, re_path

from base.views import handler404
from login.views import (
    EditUserView,
    GroupFormView,
    GroupListView,
    GroupManagementView,
    GroupMembersView,
    GroupsView,
    GroupTablesView,
    ReviewsView,
    SettingsView,
    TablesView,
    delete_peer_review_simple_view,
    group_delete_view,
    group_leave_view,
    metadata_review_badge_indicator_icon_file_view,
    token_reset_view,
    user_redirect_view,
)

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
    re_path(r"^profile/(?P<user_id>[\d]+)/edit$", EditUserView.as_view(), name="edit"),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/settings$",
        SettingsView.as_view(),
        name="settings",
    ),
    # TODO: implement tests before we allow user deletion
    re_path(
        r"^profile/(?P<user_id>[\d]+)/delete_acc$",
        # AccountDeleteView.as_view(),
        handler404,
        name="account-delete",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)$",
        TablesView.as_view(),
        name="profile",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/tables$",
        TablesView.as_view(),
        name="tables",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/tables/(?P<table_name>[\w]+)/review-badge$",
        metadata_review_badge_indicator_icon_file_view,
        name="metadata-review-badge-icon",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/review$",
        ReviewsView.as_view(),
        name="reviews",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/organizations$",
        GroupsView.as_view(group_type="organization"),
        name="organizations",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/projects$",
        GroupsView.as_view(group_type="project"),
        name="projects",
    ),
    re_path(
        r"^(?P<group_type>organization|project)/list/$",
        GroupListView.as_view(),
        name="group-list",
    ),
    re_path(
        r"^(?P<group_type>organization|project)/new/$",
        GroupFormView.as_view(),
        name="group-create",
    ),
    re_path(
        r"^(?P<group_type>organization|project)/(?P<group_id>[\w\d_\s]+)/manage$",
        GroupManagementView.as_view(),
        name="group-management",
    ),
    re_path(
        r"^(?P<group_type>organization|project)/(?P<group_id>[\w\d_\s]+)/edit$",
        GroupFormView.as_view(),
        name="group-edit",
    ),
    re_path(
        r"^(?P<group_type>organization|project)/(?P<group_id>[\w\d_\s]+)/tables$",
        GroupTablesView.as_view(),
        name="group-tables",
    ),
    re_path(
        r"^(?P<group_type>organization|project)/(?P<group_id>[\w\d_\s]+)/members$",
        GroupMembersView.as_view(),
        name="group-membership",
    ),
    re_path(
        r"^group/(?P<group_id>[\w\d_\s]+)/leave$",
        group_leave_view,
        name="group-leave",
    ),
    re_path(
        r"^group/(?P<group_id>[\w\d_\s]+)/delete$",
        group_delete_view,
        name="group-delete",
    ),
    re_path(r"^reset/token$", token_reset_view, name="reset-token"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path(
        "delete_peer_review/",
        delete_peer_review_simple_view,
        name="delete_peer_review_simple",
    ),
]
