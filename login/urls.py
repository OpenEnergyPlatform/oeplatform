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
    OrganizationManagementView,
    OrganizationsView,
    PartialOrganizationEditFormView,
    PartialOrganizationInviteView,
    PartialOrganizationMemberManagementView,
    PartialOrganizationsView,
    ReviewsView,
    SettingsView,
    TablesView,
    delete_peer_review_simple_view,
    metadata_review_badge_indicator_icon_file_view,
    organization_leave_view,
    organization_member_count_view,
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
        OrganizationsView.as_view(),
        name="organizations",
    ),
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
        r"^profile/(?P<user_id>[\d]+)/partial_organizations$",
        PartialOrganizationsView.as_view(),
        name="partial-organizations",
    ),
    re_path(
        r"^organizations/new/$",
        OrganizationManagementView.as_view(),
        name="organization-create",
    ),
    re_path(r"^profile/(?P<user_id>[\d]+)/edit$", EditUserView.as_view(), name="edit"),
    re_path(
        r"^profile/organizations/(?P<organization_id>[\w\d_\s]+)/edit$",
        OrganizationManagementView.as_view(),
        name="organization-edit",
    ),
    re_path(
        r"^organizations/(?P<organization_id>[\w\d_\s]+)/members$",
        PartialOrganizationMemberManagementView.as_view(),
        name="partial-organization-membership",
    ),
    re_path(
        r"^organizations/(?P<organization_id>[\w\d_\s]+)/member/invite$",
        PartialOrganizationInviteView.as_view(),
        name="partial-organization-invite",
    ),
    re_path(
        r"^organizations/(?P<organization_id>[\w\d_\s]+)/partial/edit_form$",
        PartialOrganizationEditFormView.as_view(),
        name="organization-partial-edit-form",
    ),
    re_path(
        r"^organizations/(?P<organization_id>[\w\d_\s]+)/members/count$",
        organization_member_count_view,
        name="count-organization-memberships",
    ),
    re_path(
        r"^organizations/(?P<organization_id>[\w\d_\s]+)/leave$",
        organization_leave_view,
        name="organization-leave",
    ),
    re_path(r"^reset/token$", token_reset_view, name="reset-token"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path(
        "delete_peer_review/",
        delete_peer_review_simple_view,
        name="delete_peer_review_simple",
    ),
]
