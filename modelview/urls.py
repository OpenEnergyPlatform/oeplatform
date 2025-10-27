"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import path

from modelview.views import (
    FSAddView,
    edit_model_view,
    fs_delete_view,
    list_sheets_view,
    model_to_csv_view,
    show_view,
)

app_name = "modelview"

urlpatterns = [
    path("<str:sheettype>s/", list_sheets_view, name="modellist"),
    path(
        "<str:sheettype>s/add/",
        FSAddView.as_view(),
        {"method": "add"},
        name="modeladd",
    ),
    path(
        "<str:sheettype>s/delete/<int:pk>/",
        fs_delete_view,
        name="delete-factsheet",
    ),
    path("<str:sheettype>s/download/", model_to_csv_view, name="download"),
    path("<str:sheettype>s/<int:pk>/", show_view, name="show-factsheet"),
    path("<str:sheettype>s/<int:pk>/edit/", edit_model_view, name="edit"),
    path(
        "<str:sheettype>s/<int:pk>/update/",
        FSAddView.as_view(),
        {"method": "update"},
        name="update",
    ),
]
