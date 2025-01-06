from django.urls import path, re_path

from api import actions, views

pgsql_qualifier = r"[\w\d_]+"
equal_qualifier = r"[\w\d\s\'\=]"
structures = r"table|sequence"
urlpatterns = [
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/$",
        views.Table.as_view(),
        name="api_table",
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/sequences/(?P<sequence>[\w\d_\s]+)/$",  # noqa
        views.Sequence.as_view(),
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/meta/$",  # noqa
        views.Metadata.as_view(),
        name="api_table_meta",
    ),
    # TODO: Remove this endpoint later on - MovePublish includes optional
    # embargo time and marks table as published
    path(
        "v0/schema/<str:schema>/tables/<str:table>/move/<str:to_schema>/",
        views.Move.as_view(),
        name="move",
    ),
    path(
        "v0/schema/<str:schema>/tables/<str:table>/move_publish/<str:to_schema>/",  # noqa
        views.MovePublish.as_view(),
        name="move_publish",
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/columns/(?P<column>[\w\d_\s]+)?$",  # noqa
        views.Column.as_view(),
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/id/(?P<id>[\d]+)/column/(?P<column>[\w\d_\s]+)/$",  # noqa
        views.Fields.as_view(),
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/indexes/(?P<index>[\w\d_\s]+)$",  # noqa
        views.Index.as_view(),
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/(?P<row_id>[\d]+)?$",  # noqa
        views.Rows.as_view(),
        name="api_rows",
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/new?$",  # noqa
        views.Rows.as_view(),
        {"action": "new"},
        name="api_rows_new",
    ),
    re_path(
        r"^v0/advanced/search",
        views.create_ajax_handler(
            actions.data_search, allow_cors=True, requires_cursor=True
        ),
    ),
    re_path(
        r"^v0/advanced/insert",
        views.create_ajax_handler(actions.data_insert, requires_cursor=True),
        name="api_insert",
    ),
    re_path(
        r"^v0/advanced/delete",
        views.create_ajax_handler(actions.data_delete, requires_cursor=True),
    ),
    re_path(
        r"^v0/advanced/update",
        views.create_ajax_handler(actions.data_update, requires_cursor=True),
    ),
    re_path(r"^v0/advanced/info", views.create_ajax_handler(actions.data_info)),
    re_path(
        r"^v0/advanced/has_schema", views.create_ajax_handler(actions.has_schema)
    ),  # noqa
    re_path(r"^v0/advanced/has_table", views.create_ajax_handler(actions.has_table)),
    re_path(
        r"^v0/advanced/has_sequence", views.create_ajax_handler(actions.has_sequence)
    ),  # noqa
    re_path(r"^v0/advanced/has_type", views.create_ajax_handler(actions.has_type)),
    re_path(
        r"^v0/advanced/get_schema_names",
        views.create_ajax_handler(actions.get_schema_names),
    ),
    re_path(
        r"^v0/advanced/get_table_names",
        views.create_ajax_handler(actions.get_table_names),
    ),
    re_path(
        r"^v0/advanced/get_view_names",
        views.create_ajax_handler(actions.get_view_names),
    ),
    re_path(
        r"^v0/advanced/get_view_definition",
        views.create_ajax_handler(actions.get_view_definition),
    ),
    re_path(
        r"^v0/advanced/get_columns", views.create_ajax_handler(actions.get_columns)
    ),  # noqa
    re_path(
        r"^v0/advanced/get_pk_constraint",
        views.create_ajax_handler(actions.get_pk_constraint),
    ),
    re_path(
        r"^v0/advanced/get_foreign_keys",
        views.create_ajax_handler(actions.get_foreign_keys),
    ),
    re_path(
        r"^v0/advanced/get_indexes", views.create_ajax_handler(actions.get_indexes)
    ),  # noqa
    re_path(
        r"^v0/advanced/get_unique_constraints",
        views.create_ajax_handler(actions.get_unique_constraints),
    ),
    re_path(
        r"^v0/advanced/connection/open",
        views.create_ajax_handler(actions.open_raw_connection),
        name="api_con_open",
    ),
    re_path(
        r"^v0/advanced/connection/close$",
        views.create_ajax_handler(actions.close_raw_connection),
        name="api_con_close",
    ),
    re_path(
        r"^v0/advanced/connection/commit",
        views.create_ajax_handler(actions.commit_raw_connection),
        name="api_con_commit",
    ),
    re_path(
        r"^v0/advanced/connection/rollback",
        views.create_ajax_handler(actions.rollback_raw_connection),
    ),
    re_path(r"^v0/advanced/connection/close_all", views.CloseAll.as_view()),
    re_path(
        r"^v0/advanced/cursor/open", views.create_ajax_handler(actions.open_cursor)
    ),  # noqa
    re_path(
        r"^v0/advanced/cursor/close", views.create_ajax_handler(actions.close_cursor)
    ),  # noqa
    re_path(
        r"^v0/advanced/cursor/fetch_one", views.create_ajax_handler(actions.fetchone)
    ),  # noqa
    re_path(
        r"^v0/advanced/cursor/fetch_many",
        views.FetchView.as_view(),
        dict(fetchtype="all"),
    ),
    re_path(
        r"^v0/advanced/cursor/fetch_all",
        views.FetchView.as_view(),
        dict(fetchtype="all"),
    ),
    re_path(
        r"^v0/advanced/set_isolation_level",
        views.create_ajax_handler(actions.set_isolation_level),
    ),
    re_path(
        r"^v0/advanced/get_isolation_level",
        views.create_ajax_handler(actions.get_isolation_level),
    ),
    re_path(
        r"^v0/advanced/do_begin_twophase",
        views.create_ajax_handler(actions.do_begin_twophase),
    ),
    re_path(
        r"^v0/advanced/do_prepare_twophase",
        views.create_ajax_handler(actions.do_prepare_twophase),
    ),
    re_path(
        r"^v0/advanced/do_rollback_twophase",
        views.create_ajax_handler(actions.do_rollback_twophase),
    ),
    re_path(
        r"^v0/advanced/do_commit_twophase",
        views.create_ajax_handler(actions.do_commit_twophase),
    ),
    re_path(
        r"^v0/advanced/do_recover_twophase",
        views.create_ajax_handler(actions.do_recover_twophase),
    ),
    path("usrprop/", views.get_users),
    path("grpprop/", views.get_groups),
    path("oeo-search", views.oeo_search),
    path("oevkg-query", views.oevkg_search),
    re_path(
        r"^v0/oekg/sparql/?$",
        views.SparqlAPIView.as_view(),
        name="oekg-sparql-http-api",
    ),
    re_path(
        r"^v0/factsheet/frameworks/?$",
        views.EnergyframeworkFactsheetListAPIView.as_view(),
        name="list-framework-factsheets",
    ),
    re_path(
        r"^v0/factsheet/models/?$",
        views.EnergymodelFactsheetListAPIView.as_view(),
        name="list-model-factsheets",
    ),
    re_path(
        r"^v0/datasets/list_all/scenario/?$",
        views.ScenarioDataTablesListAPIView.as_view(),
        name="list-scenario-datasets",
    ),
]
