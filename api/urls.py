from django.conf.urls import url

from dataedit import views
from api import actions
from api import views

pgsql_qualifier = r"[\w\d_]+"
structures = r'table|sequence'
urlpatterns = [
    url(r'^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/$', views.Table.as_view()),
    url(r'^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/indexes/(?P<index>[\w\d_\s]+)$', views.Index.as_view()),

    url(r'^legacy/create', views.create_ajax_handler(actions.table_create)),
    url(r'^legacy/insert', views.create_ajax_handler(actions.data_insert)),
    url(r'^legacy/drop', views.create_ajax_handler(actions.table_drop)),
    url(r'^legacy/delete', views.create_ajax_handler(actions.data_delete)),
    url(r'^legacy/search', views.create_ajax_handler(actions.data_search)),
    url(r'^legacy/info', views.create_ajax_handler(actions.data_info)),
    url(r'^legacy/update', views.create_ajax_handler(actions.data_update)),
    url(r'^legacy/has_schema', views.create_ajax_handler(actions.has_schema)),
    url(r'^legacy/has_table', views.create_ajax_handler(actions.has_table)),
    url(r'^legacy/has_sequence', views.create_ajax_handler(actions.has_sequence)),
    url(r'^legacy/has_type', views.create_ajax_handler(actions.has_type)),
    url(r'^legacy/get_schema_names', views.create_ajax_handler(actions.get_schema_names)),
    url(r'^legacy/get_table_names', views.create_ajax_handler(actions.get_table_names)),
    url(r'^legacy/get_view_names', views.create_ajax_handler(actions.get_view_names)),
    url(r'^legacy/get_view_definition', views.create_ajax_handler(actions.get_view_definition)),
    url(r'^legacy/get_columns', views.create_ajax_handler(actions.get_columns)),
    url(r'^legacy/get_pk_constraint', views.create_ajax_handler(actions.get_pk_constraint)),
    url(r'^legacy/get_foreign_keys', views.create_ajax_handler(actions.get_foreign_keys)),
    url(r'^legacy/get_indexes', views.create_ajax_handler(actions.get_indexes)),
    url(r'^legacy/get_unique_constraints', views.create_ajax_handler(actions.get_unique_constraints)),
    url(r'^legacy/request_dump', views.create_ajax_handler(actions.get_unique_constraints)),
    url(r'^legacy/show_revisions', views.create_ajax_handler(actions.get_unique_constraints)),
]
