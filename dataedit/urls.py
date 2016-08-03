from django.conf.urls import url

from dataedit import views

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^$', views.listschemas, name='index'),
    url(r'^view/$', views.listschemas, name='index'),
    url(r'^view/(?P<schema>{qual})$'.format(qual=pgsql_qualifier), views.listtables, name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})$'.format(qual=pgsql_qualifier), views.DataView.as_view(), name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/(?P<rev_id>\d)$'.format(qual=pgsql_qualifier), views.show_revision, name='input'),
    url(r'^upload', views.DataUploadView.as_view(), name='input'),
]
