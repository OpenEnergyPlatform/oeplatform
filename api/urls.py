from django.conf.urls import url

from dataedit import views
from api import actions

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^create', actions.table_create),
    url(r'^insert', actions.data_insert),
    url(r'^drop', actions.table_drop),
    url(r'^delete', actions.data_delete),
    url(r'^search', actions.data_search),
    url(r'^info', actions.data_info),
    url(r'^has_schema', actions.has_schema),
    url(r'^has_table', actions.has_table),
    url(r'^has_sequence', actions.has_sequence),
    url(r'^has_type', actions.has_type),
    url(r'^get_schema_names', actions.get_schema_names),
    url(r'^get_table_names', actions.get_table_names),
    url(r'^get_view_names', actions.get_view_names),
    url(r'^get_view_definition', actions.get_view_definition),
    url(r'^get_columns', actions.get_columns),
    url(r'^get_pk_constraint', actions.get_pk_constraint),
    url(r'^get_foreign_keys', actions.get_foreign_keys),
    url(r'^get_indexes', actions.get_indexes),
    url(r'^get_unique_constraints', actions.get_unique_constraints),
    url(r'^request_dump', actions.get_unique_constraints),
    url(r'^show_revisions', actions.get_unique_constraints),
]
