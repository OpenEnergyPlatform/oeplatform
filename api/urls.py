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

from django.urls import include, path, re_path

from api.views import (
    AdvancedCloseAllAPIView,
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
    AdvancedFetchAPIView,
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
    ColumnAPIView,
    EnergyframeworkFactsheetListAPIView,
    EnergymodelFactsheetListAPIView,
    FieldsAPIView,
    ManageOekgScenarioDatasetsAPIView,
    MetadataAPIView,
    MoveAPIView,
    MovePublishAPIView,
    OekgSparqlAPIView,
    OevkgSearchAPIView,
    RowsAPIView,
    ScenarioDataTablesListAPIView,
    SequenceAPIView,
    TableAPIView,
    TableSizeAPIView,
    groups_api_view,
    oeo_search_api_view,
    users_api_view,
)

app_name = "api"

pgsql_qualifier = r"[\w\d_]+"
equal_qualifier = r"[\w\d\s\'\=]"
structures = r"table|sequence"


urlpatterns_v0_schema_table = [
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/$",
        TableAPIView.as_view(),
        name="api_table",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/meta/$",
        MetadataAPIView.as_view(),
        name="api_table_meta",
    ),
    # TODO: Remove this endpoint later on - MovePublish includes optional
    # embargo time and marks table as published
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/move/(?P<to_schema>[\w\d_\s]+)/",  # noqa
        MoveAPIView.as_view(),
        name="move",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/move_publish/(?P<to_schema>[\w\d_\s]+)/",  # noqa
        MovePublishAPIView.as_view(),
        name="move_publish",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/columns/(?P<column>[\w\d_\s]+)?$",  # noqa
        ColumnAPIView.as_view(),
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/id/(?P<id>[\d]+)/column/(?P<column>[\w\d_\s]+)/$",  # noqa
        FieldsAPIView.as_view(),
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/(?P<row_id>[\d]+)?$",  # noqa
        RowsAPIView.as_view(),
        name="api_rows",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/new?$",
        RowsAPIView.as_view(),
        {"action": "new"},
        name="api_rows_new",
    ),
]

urlpatterns_v0_schema = urlpatterns_v0_schema_table + [
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/sequences/(?P<sequence>[\w\d_\s]+)/$",
        SequenceAPIView.as_view(),
    ),
]


urlpatterns_v0_advanced = [
    re_path(r"^search", AdvancedSearchAPIView, name="advenced-search"),
    re_path(
        r"^insert",
        AdvancedInsertAPIView,
        name="api_insert",
    ),
    re_path(
        r"^delete",
        AdvancedDeleteAPIView,
    ),
    re_path(
        r"^update",
        AdvancedUpdateAPIView,
    ),
    re_path(r"^info", AdvancedInfoAPIView),
    re_path(
        r"^has_schema",
        AdvancedHasSchemaAPIView,
    ),
    re_path(r"^has_table", AdvancedHasTableAPIView),
    re_path(
        r"^has_sequence",
        AdvancedHasSequenceAPIView,
    ),
    re_path(r"^has_type", AdvancedHasTypeAPIView),
    re_path(
        r"^get_schema_names",
        AdvancedGetSchemaNamesAPIView,
    ),
    re_path(
        r"^get_table_names",
        AdvancedGetTableNamesAPIView,
    ),
    re_path(
        r"^get_view_names",
        AdvancedGetViewNamesAPIView,
    ),
    re_path(
        r"^get_view_definition",
        AdvancedGetViewDefinitionAPIView,
    ),
    re_path(
        r"^get_columns",
        AdvancedGetColumnsAPIView,
    ),
    re_path(
        r"^get_pk_constraint",
        AdvancedGetPkConstraintAPIView,
    ),
    re_path(
        r"^get_foreign_keys",
        AdvancedGetForeignKeysAPIView,
    ),
    re_path(
        r"^get_indexes",
        AdvancedGetIndexesAPIView,
    ),
    re_path(
        r"^get_unique_constraints",
        AdvancedGetUniqueConstraintsAPIView,
    ),
    re_path(
        r"^connection/open",
        AdvancedConnectionOpenAPIView,
        name="api_con_open",
    ),
    re_path(
        r"^connection/close$",
        AdvancedConnectionCloseAPIView,
        name="api_con_close",
    ),
    re_path(
        r"^connection/commit",
        AdvancedConnectionCommitAPIView,
        name="api_con_commit",
    ),
    re_path(
        r"^connection/rollback",
        AdvancedConnectionRollbackAPIView,
    ),
    re_path(
        r"^cursor/open",
        AdvancedCursorOpenAPIView,
    ),
    re_path(
        r"^cursor/close",
        AdvancedCursorCloseAPIView,
    ),
    re_path(
        r"^cursor/fetch_one",
        AdvancedCursorFetchOneAPIView,
    ),
    re_path(
        r"^set_isolation_level",
        AdvancedSetIsolationLevelAPIView,
    ),
    re_path(
        r"^get_isolation_level",
        AdvancedGetIsolationLevelAPIView,
    ),
    re_path(
        r"^do_begin_twophase",
        AdvancedDoBeginTwophaseAPIView,
    ),
    re_path(
        r"^do_prepare_twophase",
        AdvancedDoPrepareTwophaseAPIView,
    ),
    re_path(
        r"^do_rollback_twophase",
        AdvancedDoRollbackTwophaseAPIView,
    ),
    re_path(
        r"^do_commit_twophase",
        AdvancedDoCommitTwophaseAPIView,
    ),
    re_path(
        r"^do_recover_twophase",
        AdvancedDoRecoverTwophaseAPIView,
    ),
    re_path(r"^connection/close_all", AdvancedCloseAllAPIView.as_view()),
    re_path(
        r"^cursor/fetch_many",
        AdvancedFetchAPIView.as_view(),
        dict(fetchtype="all"),
    ),
    re_path(
        r"^cursor/fetch_all",
        AdvancedFetchAPIView.as_view(),
        dict(fetchtype="all"),
    ),
]

urlpatterns_v0 = [
    path("schema/", include(urlpatterns_v0_schema)),
    path("advanced/", include(urlpatterns_v0_advanced)),
    re_path(
        r"^oekg/sparql/?$",
        OekgSparqlAPIView.as_view(),
        name="oekg-sparql-http-api",
    ),
    re_path(
        r"^factsheet/frameworks/?$",
        EnergyframeworkFactsheetListAPIView.as_view(),
        name="list-framework-factsheets",
    ),
    re_path(
        r"^factsheet/models/?$",
        EnergymodelFactsheetListAPIView.as_view(),
        name="list-model-factsheets",
    ),
    re_path(
        r"^datasets/list_all/scenario/?$",
        ScenarioDataTablesListAPIView.as_view(),
        name="list-scenario-datasets",
    ),
    re_path(
        r"^scenario-bundle/scenario/manage-datasets/?$",
        ManageOekgScenarioDatasetsAPIView.as_view(),
        name="add-scenario-datasets",
    ),
    path("db/table-sizes/", TableSizeAPIView.as_view(), name="table-sizes"),
]


urlpatterns = [
    path("v0/", include(urlpatterns_v0)),
    path("usrprop/", users_api_view),
    path("grpprop/", groups_api_view),
    path("oeo-search", oeo_search_api_view),
    path("oevkg-query", OevkgSearchAPIView),
]
