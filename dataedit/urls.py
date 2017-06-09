from django.conf.urls import url

from dataedit import views

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^$', views.listschemas, name='index'),
    # url(r'^admin/$', views.admin, name='index'),
    url(r'^admin/columns/', views.admin_columns, name='input'),
    url(r'^admin/constraints/', views.admin_constraints, name='input'),
    url(r'^view/$', views.listschemas, name='index'),
    url(r'^view/(?P<schema_name>{qual})$'.format(qual=pgsql_qualifier), views.listtables, name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})$'.format(qual=pgsql_qualifier), views.DataView.as_view(), name='input'),
    url(r'^tags/add/$'.format(qual=pgsql_qualifier), views.add_table_tags),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/download$'.format(qual=pgsql_qualifier), views.RevisionView.as_view(), name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/comments$'.format(qual=pgsql_qualifier), views.CommentView.as_view(), name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/meta_edit$'.format(qual=pgsql_qualifier), views.MetaView.as_view(), name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/(?P<rev_id>\d+)$'.format(qual=pgsql_qualifier), views.show_revision, name='input'),
    url(r'^search', views.SearchView.as_view()),
    url(r'^tags/?$', views.tag_overview),
    url(r'^tags/set/?$', views.change_tag),
    url(r'^tags/new/?$', views.tag_editor),
    url(r'^tags/(?P<id>[0-9]+)/?$', views.tag_editor),
]
