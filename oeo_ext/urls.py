"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import re_path

from oeo_ext.views import OeoExtPluginView, add_unit_element_view

app_name = "oeo_ext"

urlpatterns = [
    re_path(
        r"oeo-ext-plugin-ui/create",
        OeoExtPluginView.as_view(),
        name="oeo-ext-plugin-ui-create",
    ),
    re_path("add-unit-element/", add_unit_element_view, name="add_unit_element"),
]
