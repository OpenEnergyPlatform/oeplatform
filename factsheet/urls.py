from django.urls import path, re_path

from factsheet import views

app_name = "factsheet"
urlpatterns = [
    path(r"", views.factsheets_index),
    path(r"main", views.factsheets_index),
    re_path(r"^id/*", views.factsheets_index, name="bundle-id-page"),
    re_path(r"^compare/*", views.factsheets_index),
    re_path(r"^oekg_history/*", views.factsheets_index),
    re_path(r"^oekg_modifications/*", views.factsheets_index),
    path(r"add/", views.create_factsheet),
    path(r"get_oekg_history/", views.get_history),
    path(r"update/", views.update_factsheet),
    path(r"name/", views.factsheet_by_name),
    path(r"get/", views.factsheet_by_id),
    path(r"get_entities_by_type/", views.get_entities_by_type),
    path(r"add_entities/", views.add_entities),
    # path(r"delete_entities/", views.delete_entities),
    path(r"delete/", views.delete_factsheet_by_id),
    path(r"all/", views.get_all_factsheets),
    path(r"all_in_turtle/", views.get_all_factsheets_as_turtle),
    path(r"all_in_jsonld/", views.get_all_factsheets_as_json_ld),
    path(r"add_a_fact/", views.add_a_fact),
    path(r"populate_factsheets_elements/", views.populate_factsheets_elements),
    path(r"update_an_entity/", views.update_an_entity),
    path(r"query/", views.query_oekg),
    path(r"get_scenarios/", views.get_scenarios),
    path(r"test_query/", views.test_query),
    path(r"get_oekg_modifications/", views.get_oekg_modifications),
    path(r"get_oekg_modifications_filtered/", views.filter_oekg_modifications),
    path(
        r"check-owner/<str:bundle_id>/", views.check_ownership, name="check_ownership"
    ),
    path(
        r"filter-oekg-scenarios/",
        views.filter_scenario_bundles_view,
        name="filter_bundles_view",
    ),
    path(r"is_logged_in/", views.is_logged_in),
]
