from django.urls import path

from .views import (
    filter_oekg_by_scenario_bundles_attributes,
    main_view,
    sparql_endpoint,
    sparql_metadata,
)

urlpatterns = [
    path("gui/", main_view, name="main"),
    path("sparql/", sparql_endpoint, name="sparql_endpoint"),
    path("sparql_info/", sparql_metadata, name="sparql_endpoint_info"),
    path(
        "filter-by-criteria/",
        filter_oekg_by_scenario_bundles_attributes,
        name="filter_oekg_by_scenario_bundles_attributes",
    ),
]
