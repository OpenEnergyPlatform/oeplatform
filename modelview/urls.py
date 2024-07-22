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
