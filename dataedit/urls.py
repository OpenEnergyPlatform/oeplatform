# SPDX-FileCopyrightText: 2025 Bachibouzouk <pierre-francois.duc@rl-institut.de>
# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Johann Wagner <johann.wagner@st.ovgu.de>
# SPDX-FileCopyrightText: 2025 Johann Wagner <johann@wagnerdevelopment.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@gmail.com>
# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@googlemail.com>
# SPDX-FileCopyrightText: 2025 Tom Heimbrodt <heimbrodt@posteo.de>
# SPDX-FileCopyrightText: 2025 Christian Hofmann <christian.hofmann@rl-institut.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <38939526+Jonas Huber@users.noreply.github.com>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 steull <stephanuller.su@gmail.com>
# SPDX-FileCopyrightText: 2025 wingechr <wingechr@users.noreply.github.com>
#
# SPDX-License-Identifier: MIT

from django.urls import path, re_path
from django.views.generic import RedirectView

from dataedit import views

pgsql_qualifier = r"[\w\d_]+"
app_name = "dataedit"
urlpatterns = [
    re_path(r"^schemas$", views.listschemas, name="topic-list"),
    re_path(r"^$", RedirectView.as_view(url="/dataedit/schemas")),
    # re_path(r'^admin/$', views.admin, name='index'),
    re_path(r"^admin/columns/", views.admin_columns, name="input"),
    re_path(r"^admin/constraints/", views.admin_constraints, name="input"),
    re_path(r"^view/$", views.listschemas, name="index"),
    re_path(
        r"^view/(?P<schema_name>{qual})$".format(qual=pgsql_qualifier),
        views.listtables,
        name="input",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        views.DataView.as_view(),
        name="view",
    ),
    re_path(
        r"^tags/add/$",
        views.redirect_after_table_tags_updated,
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/download$".format(
            qual=pgsql_qualifier
        ),
        views.RevisionView.as_view(),
        name="input",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/permissions$".format(
            qual=pgsql_qualifier
        ),
        views.PermissionView.as_view(),
        name="input",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/meta_edit$".format(
            qual=pgsql_qualifier
        ),
        views.MetaEditView.as_view(),
        name="meta_edit",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/save$".format(
            qual=pgsql_qualifier
        ),
        views.view_save,
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/set-default".format(
            qual=pgsql_qualifier
        ),
        views.view_set_default,
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/delete".format(
            qual=pgsql_qualifier
        ),
        views.view_delete,
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/(?P<rev_id>\d+)$".format(
            qual=pgsql_qualifier
        ),
        views.show_revision,
        name="input",
    ),
    re_path(r"^tags/?$", views.tag_overview),
    re_path(r"^tags/set/?$", views.change_tag),
    re_path(r"^tags/new/?$", views.tag_editor),
    re_path(r"^tags/(?P<id>[0-9]+)/?$", views.tag_editor),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/graph/new".format(
            qual=pgsql_qualifier
        ),
        views.GraphView.as_view(),
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/map/(?P<maptype>(latlon|geom))/new".format(  # noqa
            qual=pgsql_qualifier
        ),
        views.MapView.as_view(),
    ),
    re_path(
        r"^wizard/(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        views.WizardView.as_view(),
        name="wizard_upload",
    ),
    re_path(
        r"^wizard/$",
        views.WizardView.as_view(),
        name="wizard_create",
    ),
    re_path(
        r"^oemetabuilder/$",
        views.StandaloneMetaEditView.as_view(),
        name="oemetabuilder",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/open_peer_review/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        views.PeerReviewView.as_view(),
        name="peer_review_reviewer",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/open_peer_review/$".format(
            qual=pgsql_qualifier
        ),
        views.PeerReviewView.as_view(),
        name="peer_review_create",
    ),
    re_path(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/opr_contributor/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        views.PeerRreviewContributorView.as_view(),
        name="peer_review_contributor",
    ),
    path("metadata-viewer/", views.metadata_widget, name="metadata-widget"),
]
