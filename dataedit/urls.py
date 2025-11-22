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

from django.http import HttpResponseRedirect
from django.urls import include, path, re_path, reverse
from django.views.generic import RedirectView

from dataedit.views import (
    StandaloneMetaEditView,
    TableDataView,
    TableGraphView,
    TableMapView,
    TableMetaEditView,
    TablePeerReviewView,
    TablePeerRreviewContributorView,
    TablePermissionView,
    TableWizardView,
    admin_column_view,
    admin_constraints_view,
    metadata_widget_view,
    table_show_revision_view,
    table_view_delete_view,
    table_view_save_view,
    table_view_set_default_view,
    tables_view,
    tag_editor_view,
    tag_overview_view,
    tag_table_add_view,
    tag_update_view,
    topic_view,
)

app_name = "dataedit"
pgsql_qualifier = r"[\w\d_]+"


urlpatterns_view_schema = [
    re_path(
        r"^(?P<table>{qual})$".format(qual=pgsql_qualifier),
        TableDataView.as_view(),
        name="view",
    ),
    re_path(
        r"^(?P<table>{qual})/permissions$".format(qual=pgsql_qualifier),
        TablePermissionView.as_view(),
        name="table-permission",
    ),
    re_path(
        r"^(?P<table>{qual})/meta_edit$".format(qual=pgsql_qualifier),
        TableMetaEditView.as_view(),
        name="meta_edit",
    ),
    re_path(
        r"^(?P<table>{qual})/view/save$".format(qual=pgsql_qualifier),
        table_view_save_view,
        name="table-view-save",
    ),
    re_path(
        r"^(?P<table>{qual})/view/set-default".format(qual=pgsql_qualifier),
        table_view_set_default_view,
        name="table-view-set-default",  # TODO: should be POST, but is GET?
    ),
    re_path(
        r"^(?P<table>{qual})/view/delete".format(qual=pgsql_qualifier),
        table_view_delete_view,
        name="table-view-delete-default",  # TODO: should be POST, but is GET?
    ),
    re_path(
        r"^(?P<table>{qual})/(?P<rev_id>\d+)$".format(qual=pgsql_qualifier),
        table_show_revision_view,
        name="table-revision",
        # TODO: do we need it??, also: rev_id (int) in args, but view wants a date?
    ),
    re_path(
        r"^(?P<table>{qual})/graph/new".format(qual=pgsql_qualifier),
        TableGraphView.as_view(),
        name="table-graph",
    ),
    re_path(
        r"^(?P<table>{qual})/map/(?P<maptype>(latlon|geom))/new".format(  # noqa
            qual=pgsql_qualifier
        ),
        TableMapView.as_view(),
        name="table-map",
    ),
    re_path(
        r"^(?P<table>{qual})/open_peer_review/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        TablePeerReviewView.as_view(),
        name="peer_review_reviewer",
    ),
    re_path(
        r"^(?P<table>{qual})/open_peer_review/$".format(qual=pgsql_qualifier),
        TablePeerReviewView.as_view(),
        name="peer_review_create",
    ),
    re_path(
        r"^(?P<table>{qual})/opr_contributor/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        TablePeerRreviewContributorView.as_view(),
        name="peer_review_contributor",
    ),
]

urlpatterns_tag = [
    re_path(r"^$", tag_overview_view, name="tags"),
    re_path(r"^new/?$", tag_editor_view, name="tags-new"),
    re_path(r"^edit/(?P<tag_pk>[a-z0-9_]+)/?$", tag_editor_view, name="tags-edit"),
    re_path(r"^add/?$", tag_table_add_view, name="tags-add"),
    re_path(r"^set/?$", tag_update_view, name="tags-set"),
]


def get_legacy_redirect(name: str, *keys: str):
    def legacy_redirect(request, **kwargs):
        return HttpResponseRedirect(reverse(name, kwargs={k: kwargs[k] for k in keys}))

    return legacy_redirect


urlpatterns = [
    re_path(
        # redirecting old /dataedit/view/SCHEMA/TABLE
        r"^view/{qual}/(?P<path>.*)".format(qual=pgsql_qualifier),
        # NOTE: redirect url must be absolute (including "/database/")
        RedirectView.as_view(url="/database/table/%(path)s"),
    ),
    re_path(r"^table/", include(urlpatterns_view_schema)),
    re_path(
        r"^view/(?P<topic>{qual})$".format(qual=pgsql_qualifier),
        tables_view,
        name="tables",
    ),
    re_path(r"^$", topic_view, name="topic-list"),
    re_path(
        r"^view$", RedirectView.as_view(pattern_name="dataedit:topic-list")
    ),  # legacy
    re_path(
        r"^schemas$", RedirectView.as_view(pattern_name="dataedit:topic-list")
    ),  # legacy
    path("tags/", include(urlpatterns_tag)),
    re_path(
        r"^admin/columns/",
        admin_column_view,
        name="admin-columns",  # TODO: do we need this
    ),
    re_path(
        r"^admin/constraints/",
        admin_constraints_view,
        name="admin-contraints",  # TODO: do we need this
    ),
    re_path(
        r"^wizard/(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        get_legacy_redirect("dataedit:wizard_upload", "table"),
    ),
    re_path(
        r"^wizard/(?P<table>{qual})$".format(qual=pgsql_qualifier),
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
    path("metadata-viewer/", metadata_widget_view, name="metadata-widget"),
]
