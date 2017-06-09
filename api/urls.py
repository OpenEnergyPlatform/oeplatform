from django.conf.urls import url

from api import actions
from api import views


pgsql_qualifier = r"[\w\d_]+"
equal_qualifier = r"[\w\d\s\'\=]"
structures = r'table|sequence'
urlpatterns = [
    url(r'^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/$', views.Table.as_view()),
    url(r'^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/indexes/(?P<index>[\w\d_\s]+)$', views.Index.as_view()),
    url(r'^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/$', views.Rows.as_view()),


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

    url(r'^legacy/open_raw_connection', views.create_ajax_handler(actions.open_raw_connection)),
    url(r'^legacy/close_raw_connection', views.create_ajax_handler(actions.close_raw_connection)),
    url(r'^legacy/open_cursor', views.create_ajax_handler(actions.open_cursor)),
    url(r'^legacy/close_cursor', views.create_ajax_handler(actions.close_cursor)),
    url(r'^legacy/fetch_one', views.create_ajax_handler(actions.fetchone)),
    url(r'^legacy/fetch_many', views.create_ajax_handler(actions.fetchmany)),
    url(r'^legacy/fetch_all', views.create_ajax_handler(actions.fetchall)),

    url(r'^legacy/set_isolation_level', views.create_ajax_handler(actions.set_isolation_level)),
    url(r'^legacy/get_isolation_level', views.create_ajax_handler(actions.get_isolation_level)),
    url(r'^legacy/do_begin_twophase', views.create_ajax_handler(actions.do_begin_twophase)),
    url(r'^legacy/do_prepare_twophase', views.create_ajax_handler(actions.do_prepare_twophase)),
    url(r'^legacy/do_rollback_twophase', views.create_ajax_handler(actions.do_rollback_twophase)),
    url(r'^legacy/do_commit_twophase', views.create_ajax_handler(actions.do_commit_twophase)),
    url(r'^legacy/do_recover_twophase', views.create_ajax_handler(actions.do_recover_twophase)),



    url(r'^legacy/show_revisions', views.create_ajax_handler(actions.get_unique_constraints)),
]
