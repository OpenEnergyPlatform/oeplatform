"""
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>
SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Stephan Uller <https://github.com/steull> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import include, path, re_path

from dataedit.views import (
    AdminColumnView,
    AdminConstraintsView,
    MetadataWidgetView,
    StandaloneMetaEditView,
    TableDataView,
    TableGraphView,
    TableMapView,
    TableMetaEditView,
    TablePeerReviewView,
    TablePeerRreviewContributorView,
    TablePermissionView,
    TableRevisionView,
    TableShowRevisionView,
    TablesView,
    TableViewDeleteView,
    TableViewSaveView,
    TableViewSetDefaultView,
    TableWizardView,
    TagEditorView,
    TageTableAddView,
    TagOverviewView,
    TagUpdateView,
    TopicView,
)

pgsql_qualifier = r"[\w\d_]+"
app_name = "dataedit"

urlpatterns_view_schema = [
    re_path(
        r"^(?P<schema>{qual})$".format(qual=pgsql_qualifier),
        TablesView,
        name="input",
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        TableDataView.as_view(),
        name="view",
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/download$".format(qual=pgsql_qualifier),
        TableRevisionView.as_view(),
        name="input",
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/permissions$".format(
            qual=pgsql_qualifier
        ),
        TablePermissionView.as_view(),
        name="input",
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/meta_edit$".format(
            qual=pgsql_qualifier
        ),
        TableMetaEditView.as_view(),
        name="meta_edit",
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/view/save$".format(
            qual=pgsql_qualifier
        ),
        TableViewSaveView,
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/view/set-default".format(
            qual=pgsql_qualifier
        ),
        TableViewSetDefaultView,
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/view/delete".format(
            qual=pgsql_qualifier
        ),
        TableViewDeleteView,
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/(?P<rev_id>\d+)$".format(
            qual=pgsql_qualifier
        ),
        TableShowRevisionView,
        name="input",
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/graph/new".format(qual=pgsql_qualifier),
        TableGraphView.as_view(),
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/map/(?P<maptype>(latlon|geom))/new".format(  # noqa
            qual=pgsql_qualifier
        ),
        TableMapView.as_view(),
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/open_peer_review/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        TablePeerReviewView.as_view(),
        name="peer_review_reviewer",
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/open_peer_review/$".format(
            qual=pgsql_qualifier
        ),
        TablePeerReviewView.as_view(),
        name="peer_review_create",
    ),
    re_path(
        r"^(?P<schema>{qual})/(?P<table>{qual})/opr_contributor/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        TablePeerRreviewContributorView.as_view(),
        name="peer_review_contributor",
    ),
]

urlpatterns_tag = [
    re_path(
        r"^add/$",
        TageTableAddView,
    ),
    re_path(r"^$", TagOverviewView),
    re_path(r"^set/?$", TagUpdateView),
    re_path(r"^new/?$", TagEditorView),
    re_path(r"^edit/(?P<id>[a-z0-9]+)/?$", TagEditorView),
]

urlpatterns = [
    path("view/", include(urlpatterns_view_schema)),
    re_path(r"^view$", TopicView, name="index"),
    re_path(r"^schemas$", TopicView, name="topic-list"),
    path("tags/", include(urlpatterns_tag)),
    re_path(r"^$", TopicView),
    re_path(r"^admin/columns/", AdminColumnView, name="admin-columns"),
    re_path(r"^admin/constraints/", AdminConstraintsView, name="admin-contraints"),
    re_path(
        r"^wizard/(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        TableWizardView.as_view(),
        name="wizard_upload",
    ),
    re_path(
        r"^wizard/$",
        TableWizardView.as_view(),
        name="wizard_create",
    ),
    re_path(
        r"^oemetabuilder/$",
        StandaloneMetaEditView.as_view(),
        name="oemetabuilder",
    ),
    path("metadata-viewer/", MetadataWidgetView, name="metadata-widget"),
]
