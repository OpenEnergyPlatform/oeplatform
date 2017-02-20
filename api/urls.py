from django.conf.urls import url

from dataedit import views
from api import actions
from api import views

pgsql_qualifier = r"[\w\d_]+"
structures = r'table|sequence'
urlpatterns = [
    url(r'^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/$', views.Table.as_view()),
    url(r'^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/indexes/(?P<index>[\w\d_\s]+)$', views.Index.as_view()),
]
