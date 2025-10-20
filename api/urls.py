"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import path, re_path

from api.views import (
    AdvancedConnectionCloseAPIView,
    AdvancedConnectionCommitAPIView,
    AdvancedConnectionOpenAPIView,
    AdvancedConnectionRollbackAPIView,
    AdvancedCursorCloseAPIView,
    AdvancedCursorFetchOneAPIView,
    AdvancedCursorOpenAPIView,
    AdvancedDeleteAPIView,
    AdvancedDoBeginTwophaseAPIView,
    AdvancedDoCommitTwophaseAPIView,
    AdvancedDoPrepareTwophaseAPIView,
    AdvancedDoRecoverTwophaseAPIView,
    AdvancedDoRollbackTwophaseAPIView,
    AdvancedGetColumnsAPIView,
    AdvancedGetForeignKeysAPIView,
    AdvancedGetIndexesAPIView,
    AdvancedGetIsolationLevelAPIView,
    AdvancedGetPkConstraintAPIView,
    AdvancedGetSchemaNamesAPIView,
    AdvancedGetTableNamesAPIView,
    AdvancedGetUniqueConstraintsAPIView,
    AdvancedGetViewDefinitionAPIView,
    AdvancedGetViewNamesAPIView,
    AdvancedHasSchemaAPIView,
    AdvancedHasSequenceAPIView,
    AdvancedHasTableAPIView,
    AdvancedHasTypeAPIView,
    AdvancedInfoAPIView,
    AdvancedInsertAPIView,
    AdvancedSearchAPIView,
    AdvancedSetIsolationLevelAPIView,
    AdvancedUpdateAPIView,
    CloseAllAPIView,
    ColumnAPIView,
    EnergyframeworkFactsheetListAPIView,
    EnergymodelFactsheetListAPIView,
    FetchAPIView,
    FieldsAPIView,
    GroupsAPIView,
    IndexAPIView,
    ManageOekgScenarioDatasetsAPIView,
    MetadataAPIView,
    MoveAPIView,
    MovePublishAPIView,
    OekgSparqlAPIView,
    OeoSsearchAPIView,
    OevkgSearchAPIView,
    RowsAPIView,
    ScenarioDataTablesListAPIView,
    SequenceAPIView,
    TableAPIView,
    TableSizeAPIView,
    UsersAPIView,
)

app_name = "api"

pgsql_qualifier = r"[\w\d_]+"
equal_qualifier = r"[\w\d\s\'\=]"
structures = r"table|sequence"
urlpatterns = [
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/$",
        TableAPIView.as_view(),
        name="api_table",
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/sequences/(?P<sequence>[\w\d_\s]+)/$",  # noqa
        SequenceAPIView.as_view(),
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/meta/$",  # noqa
        MetadataAPIView.as_view(),
        name="api_table_meta",
    ),
    # TODO: Remove this endpoint later on - MovePublish includes optional
    # embargo time and marks table as published
    path(
        "v0/schema/<str:schema>/tables/<str:table>/move/<str:to_schema>/",
        MoveAPIView.as_view(),
        name="move",
    ),
    path(
        "v0/schema/<str:schema>/tables/<str:table>/move_publish/<str:to_schema>/",  # noqa
        MovePublishAPIView.as_view(),
        name="move_publish",
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/columns/(?P<column>[\w\d_\s]+)?$",  # noqa
        ColumnAPIView.as_view(),
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/id/(?P<id>[\d]+)/column/(?P<column>[\w\d_\s]+)/$",  # noqa
        FieldsAPIView.as_view(),
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/indexes/(?P<index>[\w\d_\s]+)$",  # noqa
        IndexAPIView.as_view(),
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/(?P<row_id>[\d]+)?$",  # noqa
        RowsAPIView.as_view(),
        name="api_rows",
    ),
    re_path(
        r"^v0/schema/(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/new?$",  # noqa
        RowsAPIView.as_view(),
        {"action": "new"},
        name="api_rows_new",
    ),
    re_path(
        r"^v0/advanced/search",
        AdvancedSearchAPIView,
    ),
    re_path(
        r"^v0/advanced/insert",
        AdvancedInsertAPIView,
        name="api_insert",
    ),
    re_path(
        r"^v0/advanced/delete",
        AdvancedDeleteAPIView,
    ),
    re_path(
        r"^v0/advanced/update",
        AdvancedUpdateAPIView,
    ),
    re_path(r"^v0/advanced/info", AdvancedInfoAPIView),
    re_path(
        r"^v0/advanced/has_schema",
        AdvancedHasSchemaAPIView,
    ),
    re_path(r"^v0/advanced/has_table", AdvancedHasTableAPIView),
    re_path(
        r"^v0/advanced/has_sequence",
        AdvancedHasSequenceAPIView,
    ),
    re_path(r"^v0/advanced/has_type", AdvancedHasTypeAPIView),
    re_path(
        r"^v0/advanced/get_schema_names",
        AdvancedGetSchemaNamesAPIView,
    ),
    re_path(
        r"^v0/advanced/get_table_names",
        AdvancedGetTableNamesAPIView,
    ),
    re_path(
        r"^v0/advanced/get_view_names",
        AdvancedGetViewNamesAPIView,
    ),
    re_path(
        r"^v0/advanced/get_view_definition",
        AdvancedGetViewDefinitionAPIView,
    ),
    re_path(
        r"^v0/advanced/get_columns",
        AdvancedGetColumnsAPIView,
    ),
    re_path(
        r"^v0/advanced/get_pk_constraint",
        AdvancedGetPkConstraintAPIView,
    ),
    re_path(
        r"^v0/advanced/get_foreign_keys",
        AdvancedGetForeignKeysAPIView,
    ),
    re_path(
        r"^v0/advanced/get_indexes",
        AdvancedGetIndexesAPIView,
    ),
    re_path(
        r"^v0/advanced/get_unique_constraints",
        AdvancedGetUniqueConstraintsAPIView,
    ),
    re_path(
        r"^v0/advanced/connection/open",
        AdvancedConnectionOpenAPIView,
        name="api_con_open",
    ),
    re_path(
        r"^v0/advanced/connection/close$",
        AdvancedConnectionCloseAPIView,
        name="api_con_close",
    ),
    re_path(
        r"^v0/advanced/connection/commit",
        AdvancedConnectionCommitAPIView,
        name="api_con_commit",
    ),
    re_path(
        r"^v0/advanced/connection/rollback",
        AdvancedConnectionRollbackAPIView,
    ),
    re_path(
        r"^v0/advanced/cursor/open",
        AdvancedCursorOpenAPIView,
    ),
    re_path(
        r"^v0/advanced/cursor/close",
        AdvancedCursorCloseAPIView,
    ),
    re_path(
        r"^v0/advanced/cursor/fetch_one",
        AdvancedCursorFetchOneAPIView,
    ),
    re_path(
        r"^v0/advanced/set_isolation_level",
        AdvancedSetIsolationLevelAPIView,
    ),
    re_path(
        r"^v0/advanced/get_isolation_level",
        AdvancedGetIsolationLevelAPIView,
    ),
    re_path(
        r"^v0/advanced/do_begin_twophase",
        AdvancedDoBeginTwophaseAPIView,
    ),
    re_path(
        r"^v0/advanced/do_prepare_twophase",
        AdvancedDoPrepareTwophaseAPIView,
    ),
    re_path(
        r"^v0/advanced/do_rollback_twophase",
        AdvancedDoRollbackTwophaseAPIView,
    ),
    re_path(
        r"^v0/advanced/do_commit_twophase",
        AdvancedDoCommitTwophaseAPIView,
    ),
    re_path(
        r"^v0/advanced/do_recover_twophase",
        AdvancedDoRecoverTwophaseAPIView,
    ),
    re_path(r"^v0/advanced/connection/close_all", CloseAllAPIView.as_view()),
    re_path(
        r"^v0/advanced/cursor/fetch_many",
        FetchAPIView.as_view(),
        dict(fetchtype="all"),
    ),
    re_path(
        r"^v0/advanced/cursor/fetch_all",
        FetchAPIView.as_view(),
        dict(fetchtype="all"),
    ),
    path("usrprop/", UsersAPIView),
    path("grpprop/", GroupsAPIView),
    path("oeo-search", OeoSsearchAPIView),
    path("oevkg-query", OevkgSearchAPIView),
    re_path(
        r"^v0/oekg/sparql/?$",
        OekgSparqlAPIView.as_view(),
        name="oekg-sparql-http-api",
    ),
    re_path(
        r"^v0/factsheet/frameworks/?$",
        EnergyframeworkFactsheetListAPIView.as_view(),
        name="list-framework-factsheets",
    ),
    re_path(
        r"^v0/factsheet/models/?$",
        EnergymodelFactsheetListAPIView.as_view(),
        name="list-model-factsheets",
    ),
    re_path(
        r"^v0/datasets/list_all/scenario/?$",
        ScenarioDataTablesListAPIView.as_view(),
        name="list-scenario-datasets",
    ),
    re_path(
        r"^v0/scenario-bundle/scenario/manage-datasets/?$",
        ManageOekgScenarioDatasetsAPIView.as_view(),
        name="add-scenario-datasets",
    ),
    path("v0/db/table-sizes/", TableSizeAPIView.as_view(), name="table-sizes"),
]
