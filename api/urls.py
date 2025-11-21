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
    AllTableSizesAPIView,
    EnergyframeworkFactsheetListAPIView,
    EnergymodelFactsheetListAPIView,
    ManageOekgScenarioDatasetsAPIView,
    OekgSparqlAPIView,
    ScenarioDataTablesListAPIView,
    TableAPIView,
    TableColumnAPIView,
    TableFieldsAPIView,
    TableMetadataAPIView,
    TableMoveAPIView,
    TableMovePublishAPIView,
    TableRowsAPIView,
    TableUnpublishAPIView,
    grpprop_api_view,
    oeo_search_api_view,
    oevkg_query_api_view,
    table_approx_row_count_view,
    usrprop_api_view,
)

app_name = "api"

pgsql_qualifier = r"[\w\d_]+"
equal_qualifier = r"[\w\d\s\'\=]"
structures = r"table|sequence"

# all endpoints referring to table
urlpatterns_v0_schema_table = [
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/$",
        TableAPIView.as_view(),
        name="api_table",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/meta/$",
        TableMetadataAPIView.as_view(),
        name="api_table_meta",
    ),
    # TODO: Remove this endpoint later on - MovePublish includes optional
    # embargo time and marks table as published
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/move/(?P<to_schema>[\w\d_\s]+)/",  # noqa
        TableMoveAPIView.as_view(),
        name="move",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/move_publish/(?P<to_schema>[\w\d_\s]+)/",  # noqa
        TableMovePublishAPIView.as_view(),
        name="move_publish",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/unpublish$",
        TableUnpublishAPIView.as_view(),
        name="table-unpublish",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/columns/(?P<column>[\w\d_\s]+)?$",  # noqa
        TableColumnAPIView.as_view(),
        name="table-columns",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/id/(?P<column_id>[\d]+)/column/(?P<column>[\w\d_\s]+)/$",  # noqa
        TableFieldsAPIView.as_view(),
        name="table-fields",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/(?P<row_id>[\d]+)?$",  # noqa
        TableRowsAPIView.as_view(),
        name="api_rows",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rows/new?$",
        TableRowsAPIView.as_view(),
        {"action": "new"},
        name="api_rows_new",
    ),
    re_path(
        r"^(?P<schema>[\w\d_\s]+)/tables/(?P<table>[\w\d_\s]+)/rowcount$",
        table_approx_row_count_view,
        name="approx-row-count",
    ),
]


urlpatterns_v0_advanced = [
    re_path(r"^search", AdvancedSearchAPIView, name="advanced-search"),
    re_path(
        r"^insert",
        AdvancedInsertAPIView,
        name="advanced-insert",
    ),
    re_path(r"^delete", AdvancedDeleteAPIView, name="advanced-delete"),
    re_path(r"^update", AdvancedUpdateAPIView, name="advanced-update"),
    re_path(r"^info", AdvancedInfoAPIView, name="advanced-info"),
    re_path(r"^has_schema", AdvancedHasSchemaAPIView, name="advanced-has-schema"),
    re_path(r"^has_table", AdvancedHasTableAPIView, name="advanced-has-table"),
    re_path(r"^has_sequence", AdvancedHasSequenceAPIView, name="advanced-has-sequence"),
    re_path(r"^has_type", AdvancedHasTypeAPIView, name="advanced-has-type"),
    re_path(
        r"^get_schema_names",
        AdvancedGetSchemaNamesAPIView,
        name="advanced-schema-names",
    ),
    re_path(
        r"^get_table_names", AdvancedGetTableNamesAPIView, name="advanced-table-names"
    ),
    re_path(
        r"^get_view_names", AdvancedGetViewNamesAPIView, name="advanced-view-names"
    ),
    re_path(
        r"^get_view_definition",
        AdvancedGetViewDefinitionAPIView,
        name="advanced-view-definitions",
    ),
    re_path(
        r"^get_columns",
        AdvancedGetColumnsAPIView,
        name="advanced-columns",
    ),
    re_path(
        r"^get_pk_constraint",
        AdvancedGetPkConstraintAPIView,
        name="advanced-pk-constraint",
    ),
    re_path(
        r"^get_foreign_keys",
        AdvancedGetForeignKeysAPIView,
        name="advanced-foreign-keys",
    ),
    re_path(
        r"^get_indexes",
        AdvancedGetIndexesAPIView,
        name="advanced-indexes",
    ),
    re_path(
        r"^get_unique_constraints",
        AdvancedGetUniqueConstraintsAPIView,
        name="advanced-unique-constraints",
    ),
    re_path(
        r"^connection/open",
        AdvancedConnectionOpenAPIView,
        name="advanced-connection-open",
    ),
    re_path(
        r"^connection/close$",
        AdvancedConnectionCloseAPIView,
        name="advanced-connection-close",
    ),
    re_path(
        r"^connection/commit",
        AdvancedConnectionCommitAPIView,
        name="advanced-connection-commit",
    ),
    re_path(
        r"^connection/rollback",
        AdvancedConnectionRollbackAPIView,
        name="advanced-connection-rollback",
    ),
    re_path(r"^cursor/open", AdvancedCursorOpenAPIView, name="advanced-cursor-open"),
    re_path(r"^cursor/close", AdvancedCursorCloseAPIView, name="advanced-cursor-close"),
    re_path(
        r"^cursor/fetch_one",
        AdvancedCursorFetchOneAPIView,
        name="advanced-cursor-fetch-one",
    ),
    re_path(
        r"^set_isolation_level",
        AdvancedSetIsolationLevelAPIView,
        name="advanced-set-isolation-level",
    ),
    re_path(
        r"^get_isolation_level",
        AdvancedGetIsolationLevelAPIView,
        name="advanced-get-isolation-level",
    ),
    re_path(
        r"^do_begin_twophase",
        AdvancedDoBeginTwophaseAPIView,
        name="advanced-do-begin-twophase",
    ),
    re_path(
        r"^do_prepare_twophase",
        AdvancedDoPrepareTwophaseAPIView,
        name="advanced-doprepare-twophase",
    ),
    re_path(
        r"^do_rollback_twophase",
        AdvancedDoRollbackTwophaseAPIView,
        name="advanced-do-rollback-twophase",
    ),
    re_path(
        r"^do_commit_twophase",
        AdvancedDoCommitTwophaseAPIView,
        name="advanced-do-commit-twophase",
    ),
    re_path(
        r"^do_recover_twophase",
        AdvancedDoRecoverTwophaseAPIView,
        name="advanced-do-recover-twophase",
    ),
    re_path(
        r"^connection/close_all",
        AdvancedCloseAllAPIView.as_view(),
        name="advanced-connection-close-all",
    ),
    re_path(
        r"^cursor/fetch_many",
        AdvancedFetchAPIView.as_view(),
        dict(fetchtype="all"),  # TODO: shouldn't this be "many"?
        name="advanced-cursor-fetch-many",
    ),
    re_path(
        r"^cursor/fetch_all",
        AdvancedFetchAPIView.as_view(),
        dict(fetchtype="all"),
        name="advanced-cursor-fetch-all",
    ),
]

urlpatterns_v0 = [
    path("schema/", include(urlpatterns_v0_schema_table)),
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
    path("db/table-sizes/", AllTableSizesAPIView.as_view(), name="table-sizes"),
]


urlpatterns = [
    path("v0/", include(urlpatterns_v0)),
    path("usrprop/", usrprop_api_view, name="usrprop"),
    path("grpprop/", grpprop_api_view, name="grpprop"),
    path("oeo-search", oeo_search_api_view, name="oeo-search"),
    path("oevkg-query", oevkg_query_api_view, name="oevkg-query"),
]
