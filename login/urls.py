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

from django.urls import path, re_path

from login.views import (
    DatasetsView,
    EditUserView,
    OrganizationListView,
    OrganizationManagementView,
    OrganizationMembersView,
    OrganizationsView,
    ReviewsView,
    SettingsView,
    TableAccessView,
    TableActionCheckView,
    TableActionView,
    TableNamesView,
    TablesView,
    account_delete_view,
    delete_peer_review_simple_view,
    metadata_review_badge_indicator_icon_file_view,
    organization_delete_view,
    organization_leave_view,
    token_reset_view,
    user_redirect_view,
)

app_name = "login"
urlpatterns = [
    re_path(
        # dataset-first dashboard: the profile opens on the datasets view
        r"^profile/(?P<user_id>[\d]+)$",
        DatasetsView.as_view(),
        name="profile",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/datasets$",
        DatasetsView.as_view(),
        name="datasets",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/tables$",
        TablesView.as_view(),
        name="tables",
    ),
    # Whatever is not one Table sits beside tables/, never under it: a Table
    # may be named "actions" or "names", and tables/<table_name>/access must
    # reach its drawer (#2611).
    re_path(
        r"^profile/(?P<user_id>[\d]+)/table-actions/(?P<action>[a-z_]+)$",
        TableActionView.as_view(),
        name="table-action",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/table-actions/(?P<action>[a-z_]+)/check$",
        TableActionCheckView.as_view(),
        name="table-action-check",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/table-names$",
        TableNamesView.as_view(),
        name="table-names",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/tables/(?P<table_name>[\w]+)/access$",
        TableAccessView.as_view(),
        name="table-access",
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
        account_delete_view,
        name="account-delete",
    ),
    re_path(
        r"^profile/(?P<user_id>[\d]+)/partial_organizations$",
        OrganizationListView.as_view(),
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
        OrganizationMembersView.as_view(),
        name="partial-organization-membership",
    ),
    re_path(
        r"^organizations/(?P<organization_id>[\w\d_\s]+)/leave$",
        organization_leave_view,
        name="organization-leave",
    ),
    re_path(
        r"^organizations/(?P<organization_id>[\w\d_\s]+)/delete$",
        organization_delete_view,
        name="organization-delete",
    ),
    re_path(r"^reset/token$", token_reset_view, name="reset-token"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path(
        "delete_peer_review/",
        delete_peer_review_simple_view,
        name="delete_peer_review_simple",
    ),
]
