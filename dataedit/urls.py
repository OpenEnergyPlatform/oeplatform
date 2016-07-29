from django.conf.urls import url

from dataedit import views

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^$', views.listschemas, name='index'),
    url(r'^edit', views.DataInputView.as_view(), name='input'),
    url(r'^delete', views.delete, name='input'),
    url(r'^drop', views.dropSessionData, name='input'),
    url(r'^view/$', views.listschemas, name='index'),
    url(r'^view/(?P<schema>{qual})$'.format(qual=pgsql_qualifier), views.listtables, name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})$'.format(qual=pgsql_qualifier), views.DataView.as_view(), name='input'),
    url(r'^view/(?P<schema>{qual})/(?P<table>{qual})/(?P<rev_id>\d)$'.format(qual=pgsql_qualifier), views.show_revision, name='input'),
    url(r'^upload', views.DataUploadView.as_view(), name='input'),
    url(r'^map', views.DataMapView.as_view(), name='input'),
    url(r'^confirm', views.confirm, name='input'),
    url(r'^commit', views.commit, name='input'),
]
