# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

from django.urls import re_path  # noqa:F401

from oeo_ext import views

app_name = "oeo_ext"

urlpatterns = [
    re_path(
        r"oeo-ext-plugin-ui/create",
        views.OeoExtPluginView.as_view(),
        name="oeo-ext-plugin-ui-create",
    ),
    re_path("add-unit-element/", views.add_unit_element, name="add_unit_element"),
    # re_path("search-oeo-units/", views.search_units, name="search_oeo_unit"),
]
