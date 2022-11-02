from django.conf.urls import url

from api import actions, views

pgsql_qualifier = r"[\w\d_]+"
equal_qualifier = r"[\w\d\s\'\=]"
structures = r"table|sequence"
urlpatterns = [
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/$",
        views.Table.as_view(),
        name="api_table",
    ),
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/sequences/(?P<sequence>[\w\d_\s]+)/$",
        views.Sequence.as_view(),
    ),
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/meta/$",
        views.Metadata.as_view(),
        name="api_table_meta",
    ),
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/move/(?P<to_schema>[\w\d_\s]+)/$",  # noqa
        views.Move.as_view(),
        name="move",
    ),
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/columns/(?P<column>[\w\d_\s]+)?$",  # noqa
        views.Column.as_view(),
    ),
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/id/(?P<id>[\d]+)/column/(?P<column>[\w\d_\s]+)/$",  # noqa
        views.Fields.as_view(),
    ),
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/indexes/(?P<index>[\w\d_\s]+)$",  # noqa
        views.Index.as_view(),
    ),
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/(?P<row_id>[\d]+)?$",  # noqa
        views.Rows.as_view(),
        name="api_rows",
    ),
    url(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/new?$",
        views.Rows.as_view(),
        {"action": "new"},
        name="api_rows_new",
    ),
    url(
        r"^v0/advanced/search",
        views.create_ajax_handler(
            actions.data_search, allow_cors=True, requires_cursor=True
        ),
    ),
    url(
        r"^v0/advanced/insert",
        views.create_ajax_handler(actions.data_insert, requires_cursor=True),
        name="api_insert",
    ),
    url(
        r"^v0/advanced/delete",
        views.create_ajax_handler(actions.data_delete, requires_cursor=True),
    ),
    url(
        r"^v0/advanced/update",
        views.create_ajax_handler(actions.data_update, requires_cursor=True),
    ),
    url(r"^v0/advanced/info", views.create_ajax_handler(actions.data_info)),
    url(r"^v0/advanced/has_schema", views.create_ajax_handler(actions.has_schema)),
    url(r"^v0/advanced/has_table", views.create_ajax_handler(actions.has_table)),
    url(r"^v0/advanced/has_sequence", views.create_ajax_handler(actions.has_sequence)),
    url(r"^v0/advanced/has_type", views.create_ajax_handler(actions.has_type)),
    url(
        r"^v0/advanced/get_schema_names",
        views.create_ajax_handler(actions.get_schema_names),
    ),
    url(
        r"^v0/advanced/get_table_names",
        views.create_ajax_handler(actions.get_table_names),
    ),
    url(
        r"^v0/advanced/get_view_names",
        views.create_ajax_handler(actions.get_view_names),
    ),
    url(
        r"^v0/advanced/get_view_definition",
        views.create_ajax_handler(actions.get_view_definition),
    ),
    url(r"^v0/advanced/get_columns", views.create_ajax_handler(actions.get_columns)),
    url(
        r"^v0/advanced/get_pk_constraint",
        views.create_ajax_handler(actions.get_pk_constraint),
    ),
    url(
        r"^v0/advanced/get_foreign_keys",
        views.create_ajax_handler(actions.get_foreign_keys),
    ),
    url(r"^v0/advanced/get_indexes", views.create_ajax_handler(actions.get_indexes)),
    url(
        r"^v0/advanced/get_unique_constraints",
        views.create_ajax_handler(actions.get_unique_constraints),
    ),
    url(
        r"^v0/advanced/connection/open",
        views.create_ajax_handler(actions.open_raw_connection),
        name="api_con_open",
    ),
    url(
        r"^v0/advanced/connection/close$",
        views.create_ajax_handler(actions.close_raw_connection),
        name="api_con_close",
    ),
    url(
        r"^v0/advanced/connection/commit",
        views.create_ajax_handler(actions.commit_raw_connection),
        name="api_con_commit",
    ),
    url(
        r"^v0/advanced/connection/rollback",
        views.create_ajax_handler(actions.rollback_raw_connection),
    ),
    url(r"^v0/advanced/connection/close_all", views.CloseAll.as_view()),
    url(r"^v0/advanced/cursor/open", views.create_ajax_handler(actions.open_cursor)),
    url(r"^v0/advanced/cursor/close", views.create_ajax_handler(actions.close_cursor)),
    url(r"^v0/advanced/cursor/fetch_one", views.create_ajax_handler(actions.fetchone)),
    url(
        r"^v0/advanced/cursor/fetch_many",
        views.FetchView.as_view(),
        dict(fetchtype="all"),
    ),
    url(
        r"^v0/advanced/cursor/fetch_all",
        views.FetchView.as_view(),
        dict(fetchtype="all"),
    ),
    url(
        r"^v0/advanced/set_isolation_level",
        views.create_ajax_handler(actions.set_isolation_level),
    ),
    url(
        r"^v0/advanced/get_isolation_level",
        views.create_ajax_handler(actions.get_isolation_level),
    ),
    url(
        r"^v0/advanced/do_begin_twophase",
        views.create_ajax_handler(actions.do_begin_twophase),
    ),
    url(
        r"^v0/advanced/do_prepare_twophase",
        views.create_ajax_handler(actions.do_prepare_twophase),
    ),
    url(
        r"^v0/advanced/do_rollback_twophase",
        views.create_ajax_handler(actions.do_rollback_twophase),
    ),
    url(
        r"^v0/advanced/do_commit_twophase",
        views.create_ajax_handler(actions.do_commit_twophase),
    ),
    url(
        r"^v0/advanced/do_recover_twophase",
        views.create_ajax_handler(actions.do_recover_twophase),
    ),
    url(r"^v0/image/upload", views.ImageUpload.as_view()),
    url(r"usrprop/", views.get_users),
    url(r"grpprop/", views.get_groups),
    url("oeo-search", views.oeo_search),
]
