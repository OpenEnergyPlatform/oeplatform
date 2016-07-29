from django.conf.urls import url

from dataedit import views
from api import actions

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^dataconnection_create', actions.table_create),
    url(r'^dataconnection_insert', actions.data_insert),
    url(r'^dataconnection_drop', actions.table_drop),
    url(r'^dataconnection_delete', actions.data_delete),
    url(r'^dataconnection_search', actions.data_search),
    url(r'^dataconnection_info', actions.data_info),
    url(r'^dataconnection_has_schema', actions.has_schema),
    url(r'^dataconnection_has_table', actions.has_table),
    url(r'^dataconnection_has_sequence', actions.has_sequence),
    url(r'^dataconnection_has_type', actions.has_type),
    url(r'^dataconnection_get_schema_names', actions.get_schema_names),
    url(r'^dataconnection_get_table_names', actions.get_table_names),
    url(r'^dataconnection_get_view_names', actions.get_view_names),
    url(r'^dataconnection_get_view_definition', actions.get_view_definition),
    url(r'^dataconnection_get_columns', actions.get_columns),
    url(r'^dataconnection_get_pk_constraint', actions.get_pk_constraint),
    url(r'^dataconnection_get_foreign_keys', actions.get_foreign_keys),
    url(r'^dataconnection_get_indexes', actions.get_indexes),
    url(r'^dataconnection_get_unique_constraints', actions.get_unique_constraints),
    url(r'^dataconnection_request_dump', actions.get_unique_constraints),
    url(r'^show_revisions', actions.get_unique_constraints),
]
