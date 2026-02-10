"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import path

from oekg.views import (
    filter_oekg_by_scenario_bundles_attributes_view,
    main_view,
    sparql_endpoint_view,
    sparql_metadata_view,
)

app_name = "oekg"
urlpatterns = [
    path("gui/", main_view, name="main"),
    path("sparql/", sparql_endpoint_view, name="sparql_endpoint"),
    path("sparql_info/", sparql_metadata_view, name="sparql_endpoint_info"),
    path(
        "filter-by-criteria/",
        filter_oekg_by_scenario_bundles_attributes_view,
        name="filter_oekg_by_scenario_bundles_attributes",
    ),
]
