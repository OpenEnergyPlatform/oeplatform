# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

from django.urls import path

from .views import main_view, sparql_endpoint, sparql_metadata

urlpatterns = [
    path("gui/", main_view, name="main"),
    path("sparql/", sparql_endpoint, name="sparql_endpoint"),
    path("sparql_info/", sparql_metadata, name="sparql_endpoint_info"),
]
