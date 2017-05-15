from django.conf.urls import url

from dataedit import views
from api import actions
from api import views

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^create', views.create_ajax_handler(actions.table_create)),
    url(r'^insert', views.create_ajax_handler(actions.data_insert)),
    url(r'^drop', views.create_ajax_handler(actions.table_drop)),
    url(r'^delete', views.create_ajax_handler(actions.data_delete)),
    url(r'^search', views.create_ajax_handler(actions.data_search)),
    url(r'^info', views.create_ajax_handler(actions.data_info)),
    url(r'^update', views.create_ajax_handler(actions.data_update)),
    url(r'^has_schema', views.create_ajax_handler(actions.has_schema)),
    url(r'^has_table', views.create_ajax_handler(actions.has_table)),
    url(r'^has_sequence', views.create_ajax_handler(actions.has_sequence)),
    url(r'^has_type', views.create_ajax_handler(actions.has_type)),
    url(r'^get_schema_names', views.create_ajax_handler(actions.get_schema_names)),
    url(r'^get_table_names', views.create_ajax_handler(actions.get_table_names)),
    url(r'^get_view_names', views.create_ajax_handler(actions.get_view_names)),
    url(r'^get_view_definition', views.create_ajax_handler(actions.get_view_definition)),
    url(r'^get_columns', views.create_ajax_handler(actions.get_columns)),
    url(r'^get_pk_constraint', views.create_ajax_handler(actions.get_pk_constraint)),
    url(r'^get_foreign_keys', views.create_ajax_handler(actions.get_foreign_keys)),
    url(r'^get_indexes', views.create_ajax_handler(actions.get_indexes)),
    url(r'^get_unique_constraints', views.create_ajax_handler(actions.get_unique_constraints)),
    url(r'^request_dump', views.create_ajax_handler(actions.get_unique_constraints)),

    url(r'^set_isolation_level', views.create_ajax_handler(actions.set_isolation_level)),
    url(r'^get_isolation_level', views.create_ajax_handler(actions.get_isolation_level)),
    url(r'^do_begin_twophase', views.create_ajax_handler(actions.do_begin_twophase)),
    url(r'^do_prepare_twophase', views.create_ajax_handler(actions.do_prepare_twophase)),
    url(r'^do_rollback_twophase', views.create_ajax_handler(actions.do_rollback_twophase)),
    url(r'^do_commit_twophase', views.create_ajax_handler(actions.do_commit_twophase)),

    url(r'^show_revisions', views.create_ajax_handler(actions.get_unique_constraints)),
]
