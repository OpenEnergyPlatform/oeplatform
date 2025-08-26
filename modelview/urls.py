# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.  # noqa: E501
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut  # noqa: E501
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg  # noqa: E501
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg  # noqa: E501
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.  # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import path

from modelview import views

app_name = "modelview"

urlpatterns = [
    path("<str:sheettype>s/", views.listsheets, name="modellist"),
    path(
        "<str:sheettype>s/add/",
        views.FSAdd.as_view(),
        {"method": "add"},
        name="modeladd",
    ),
    path(
        "<str:sheettype>s/delete/<int:pk>/",
        views.fs_delete,
        name="delete-factsheet",
    ),
    path("<str:sheettype>s/download/", views.model_to_csv, name="index"),
    path("<str:sheettype>s/<int:model_name>/", views.show, name="show-factsheet"),
    path("<str:sheettype>s/<int:model_name>/edit/", views.editModel, name="index"),
    path(
        "<str:sheettype>s/<int:pk>/update/",
        views.FSAdd.as_view(),
        {"method": "update"},
        name="index",
    ),
]
