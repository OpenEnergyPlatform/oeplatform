from django.conf.urls import url
from django.views.generic import RedirectView

from dataedit import views

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r"^schemas$", views.listschemas, name="index"),
    url(r"^$", RedirectView.as_view(url="/dataedit/schemas")),
    # url(r'^admin/$', views.admin, name='index'),
    url(r"^admin/columns/", views.admin_columns, name="input"),
    url(r"^admin/constraints/", views.admin_constraints, name="input"),
    url(r"^view/$", views.listschemas, name="index"),
    url(
        r"^view/(?P<schema_name>{qual})$".format(qual=pgsql_qualifier),
        views.listtables,
        name="input",
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        views.DataView.as_view(),
        name="view",
    ),
    url(
        r"^tags/add/$",
        views.redirect_after_table_tags_updated,
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/download$".format(
            qual=pgsql_qualifier
        ),
        views.RevisionView.as_view(),
        name="input",
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/permissions$".format(
            qual=pgsql_qualifier
        ),
        views.PermissionView.as_view(),
        name="input",
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/meta_edit$".format(
            qual=pgsql_qualifier
        ),
        views.MetaEditView.as_view(),
        name="meta_edit",
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/save$".format(
            qual=pgsql_qualifier
        ),
        views.view_save,
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/set-default".format(
            qual=pgsql_qualifier
        ),
        views.view_set_default,
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/view/delete".format(
            qual=pgsql_qualifier
        ),
        views.view_delete,
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/(?P<rev_id>\d+)$".format(
            qual=pgsql_qualifier
        ),
        views.show_revision,
        name="input",
    ),
    url(r"^tags/?$", views.tag_overview),
    url(r"^tags/set/?$", views.change_tag),
    url(r"^tags/new/?$", views.tag_editor),
    url(r"^tags/(?P<id>[0-9]+)/?$", views.tag_editor),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/graph/new".format(
            qual=pgsql_qualifier
        ),
        views.GraphView.as_view(),
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/map/(?P<maptype>(latlon|geom))/new".format(  # noqa
            qual=pgsql_qualifier
        ),
        views.MapView.as_view(),
    ),
    url(
        r"^wizard/(?P<schema>{qual})/(?P<table>{qual})$".format(qual=pgsql_qualifier),
        views.WizardView.as_view(),
        name="wizard_upload",
    ),
    url(
        r"^wizard/$",
        views.WizardView.as_view(),
        name="wizard_create",
    ),
    url(
        r"^oemetabuilder/$",
        views.StandaloneMetaEditView.as_view(),
        name="oemetabuilder",
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/open_peer_review/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        views.PeerReviewView.as_view(),
        name="peer_review_reviewer",
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/open_peer_review/$".format(
            qual=pgsql_qualifier
        ),
        views.PeerReviewView.as_view(),
        name="peer_review_create",
    ),
    url(
        r"^view/(?P<schema>{qual})/(?P<table>{qual})/opr_contributor/(?P<review_id>\d*)/$".format(  # noqa
            qual=pgsql_qualifier
        ),
        views.PeerRreviewContributorView.as_view(),
        name="peer_review_contributor",
    ),
]
