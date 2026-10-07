"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import path, register_converter

from modelview.helper import SHEET_TYPES
from modelview.views import (
    FSAddView,
    edit_model_view,
    fs_delete_view,
    list_payload_view,
    list_sheets_view,
    model_to_csv_view,
    show_view,
)

app_name = "modelview"


class SheetTypeConverter:
    """One of `SHEET_TYPES`. Any other type does not resolve, so every route
    below answers 404 for it, the list included -- which used to render an
    empty list for any word ending in `s`."""

    regex = "|".join(SHEET_TYPES)

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(SheetTypeConverter, "sheettype")

urlpatterns = [
    path("<sheettype:sheettype>s/", list_sheets_view, name="modellist"),
    path(
        "<sheettype:sheettype>s/add/",
        FSAddView.as_view(),
        {"method": "add"},
        name="modeladd",
    ),
    path(
        "<sheettype:sheettype>s/delete/<int:pk>/",
        fs_delete_view,
        name="delete-factsheet",
    ),
    path("<sheettype:sheettype>s/download/", model_to_csv_view, name="download"),
    path("<sheettype:sheettype>s/payload/", list_payload_view, name="list-payload"),
    path("<sheettype:sheettype>s/<int:pk>/", show_view, name="show-factsheet"),
    path("<sheettype:sheettype>s/<int:pk>/edit/", edit_model_view, name="edit"),
    path(
        "<sheettype:sheettype>s/<int:pk>/update/",
        FSAddView.as_view(),
        {"method": "update"},
        name="update",
    ),
]
