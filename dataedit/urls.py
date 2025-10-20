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

from django.urls import path, re_path
from django.views.generic import RedirectView

from dataedit.views import (
    AdminColumnView,
    AdminConstraintsView,
    ChangeTagView,
    DataView,
    GraphView,
    MapView,
    MetadataWidgetView,
    MetaEditView,
    PeerReviewView,
    PeerRreviewContributorView,
    PermissionView,
    RedirectAfterTableTagsUpdatedView,
    RevisionView,
    ShowRevisionView,
    StandaloneMetaEditView,
    TablesView,
    TagEditorView,
    TagOverviewView,
    TopicView,
    ViewDeleteView,
    ViewSaveView,
    ViewSetDefaultView,
    WizardView,
)

pgsql_qualifier = r"[\w\d_]+"
app_name = "dataedit"
urlpatterns = [
    re_path(r"^schemas$", TopicView, name="topic-list"),
    re_path(r"^$", RedirectView.as_view(url="/dataedit/schemas")),
    re_path(r"^admin/columns/", AdminColumnView, name="input"),
    re_path(r"^admin/constraints/", AdminConstraintsView, name="input"),
    re_path(r"^view/$", TopicView, name="index"),
    re_path(
        r"^view/(?P<schema_name>{qual})$".format(qual=pgsql_qualifier),
        TablesView,
        name="input",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        DataView.as_view(),
        name="view",
    ),
    re_path(
        r"^tags/add/$",
        RedirectAfterTableTagsUpdatedView,
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/download$".format(
            qual=pgsql_qualifier
        ),
        RevisionView.as_view(),
        name="input",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/permissions$".format(
            qual=pgsql_qualifier
        ),
        PermissionView.as_view(),
        name="input",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/meta_edit$".format(
            qual=pgsql_qualifier
        ),
        MetaEditView.as_view(),
        name="meta_edit",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/save$".format(
            qual=pgsql_qualifier
        ),
        ViewSaveView,
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/set-default".format(
            qual=pgsql_qualifier
        ),
        ViewSetDefaultView,
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/delete".format(
            qual=pgsql_qualifier
        ),
        ViewDeleteView,
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/(?P<rev_id>\d+)$".format(
            qual=pgsql_qualifier
        ),
        ShowRevisionView,
        name="input",
    ),
    re_path(r"^tags/?$", TagOverviewView),
    re_path(r"^tags/set/?$", ChangeTagView),
    re_path(r"^tags/new/?$", TagEditorView),
    re_path(r"^tags/(?P<id>[a-z0-9]+)/?$", TagEditorView),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/graph/new".format(
            qual=pgsql_qualifier
        ),
        GraphView.as_view(),
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/map/(?P<maptype>(latlon|geom))/new".format(  # noqa
            qual=pgsql_qualifier
        ),
        MapView.as_view(),
    ),
    re_path(
        r"^wizard/(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        WizardView.as_view(),
        name="wizard_upload",
    ),
    re_path(
        r"^wizard/$",
        WizardView.as_view(),
        name="wizard_create",
    ),
    re_path(
        r"^oemetabuilder/$",
        StandaloneMetaEditView.as_view(),
        name="oemetabuilder",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/open_peer_review/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        PeerReviewView.as_view(),
        name="peer_review_reviewer",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/open_peer_review/$".format(
            qual=pgsql_qualifier
        ),
        PeerReviewView.as_view(),
        name="peer_review_create",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/opr_contributor/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        PeerRreviewContributorView.as_view(),
        name="peer_review_contributor",
    ),
    path("metadata-viewer/", MetadataWidgetView, name="metadata-widget"),
]
