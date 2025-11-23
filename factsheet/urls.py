"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import path, re_path

from factsheet.views import (
    add_a_fact_view,
    add_entities_view,
    check_ownership_view,
    create_factsheet_view,
    delete_factsheet_by_id_view,
    factsheet_by_id_view,
    factsheets_index_view,
    filter_scenario_bundles_view,
    get_all_factsheets_as_json_ld_view,
    get_all_factsheets_as_turtle_view,
    get_all_factsheets_view,
    get_entities_by_type_view,
    get_oekg_modifications_view,
    get_scenarios_view,
    is_logged_in_view,
    populate_factsheets_elements_view,
    test_query_view,
    update_an_entity_view,
    update_factsheet_view,
)

app_name = "factsheet"

urlpatterns = [
    path(r"", factsheets_index_view, name="index"),
    path(r"main", factsheets_index_view, name="factsheets_index"),
    re_path(r"^id/.*", factsheets_index_view, name="bundle-id-page"),
    re_path(
        r"^compare/.*", factsheets_index_view, name="compare"
    ),  # TODO: how is this different from bundle-id-page
    re_path(r"^oekg_history/.*", factsheets_index_view, name="oekg-history"),
    re_path(
        r"^oekg_modifications/.*", factsheets_index_view, name="oekg-modifications"
    ),
    path(r"add/", create_factsheet_view, name="add"),
    # path(
    #    r"get_oekg_history/",
    #    get_history_view_TODO_MISSING_MODEL,
    #    name="get-oekg-history",
    # ), # REMOVED because model HistoryOfOEKG missing
    path(r"update/", update_factsheet_view, name="update"),
    # path(r"name/", factsheet_by_name_view, name="name"),
    #  REMOVED because model Factsheet missing
    path(r"get/", factsheet_by_id_view, name="get"),
    path(
        r"get_entities_by_type/", get_entities_by_type_view, name="get-entities-by-type"
    ),
    path(r"add_entities/", add_entities_view, name="add-entities"),
    path(r"delete/", delete_factsheet_by_id_view, name="delete"),
    path(r"all/", get_all_factsheets_view, name="all"),
    path(r"all_in_turtle/", get_all_factsheets_as_turtle_view, name="all-in-turtle"),
    path(r"all_in_jsonld/", get_all_factsheets_as_json_ld_view, name="all-in-jsonld"),
    path(r"add_a_fact/", add_a_fact_view, name="add-a-fact"),
    path(
        r"populate_factsheets_elements/",
        populate_factsheets_elements_view,
        name="populate-factsheets-elements",
    ),
    path(r"update_an_entity/", update_an_entity_view, name="update-an-entity"),
    path(r"get_scenarios/", get_scenarios_view, name="get-scenarios"),
    path(r"test_query/", test_query_view, name="test-query"),
    path(
        r"get_oekg_modifications/",
        get_oekg_modifications_view,
        name="get-oekg-modifications",
    ),
    path(r"check-owner/<str:bundle_id>/", check_ownership_view, name="check_ownership"),
    path(
        r"filter-oekg-scenarios/",
        filter_scenario_bundles_view,
        name="filter_bundles_view",
    ),
    path(r"is_logged_in/", is_logged_in_view, name="is-logged-in"),
]
