from django.conf.urls import url

from dataedit import views

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^$', views.listschemas, name='index'),
    url(r'^view/$', views.listschemas, name='index'),
    url(r'^view/(?P<schema_name>{qual})$'.format(qual=pgsql_qualifier), views.listtables, name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})$'.format(qual=pgsql_qualifier), views.DataView.as_view(), name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/tags/add/$'.format(qual=pgsql_qualifier), views.add_table_tags),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/tags/add/(?P<tag_id>\d+)$'.format(qual=pgsql_qualifier), views.add_table_tag, name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/(?P<rev_id>\d+)$'.format(qual=pgsql_qualifier), views.show_revision, name='input'),
    url(r'^tag/create', views.TagCreate.as_view(),name='tag'),
    url(r'^search', views.SearchView.as_view()),
]
