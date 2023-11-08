from django.conf.urls import url
from django.urls import path

from modelview import views

# urlpatterns = [
#     path(r"^(?P<sheettype>[\w\d_]+)s/$", views.listsheets, {}, name="modellist"),
#     url(
#         r"^(?P<sheettype>[\w\d_]+)s/add/$",
#         views.FSAdd.as_view(),
#         {"method": "add"},
#         name="modeladd",
#     ),
#     url(
#         r"delete/<str:sheettype>/<int:pk>/",
#         views.FSDelete.as_view(),
#         name="delete_model",
#     ),
#     url(r"^(?P<sheettype>[\w\d_]+)s/download/$", views.model_to_csv, {}, name="index"),
#     url(
#         r"^(?P<sheettype>[\w\d_]+)s/(?P<model_name>[\d]+)/$",
#         views.show,
#         {},
#         name="index",
#     ),
#     url(
#         r"^(?P<sheettype>[\w\d_]+)s/(?P<model_name>[\d]+)/edit/$",
#         views.editModel,
#         {},
#         name="index",
#     ),
#     url(
#         r"^(?P<sheettype>[\w\d_]+)s/(?P<pk>[\d]+)/update/$",
#         views.FSAdd.as_view(),
#         {"method": "update"},
#         name="index",
#     ),
# ]

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
        name="delete_factsheet",
    ),
    path("<str:sheettype>s/download/", views.model_to_csv, name="index"),
    path("<str:sheettype>s/<int:model_name>/", views.show, name="index"),
    path("<str:sheettype>s/<int:model_name>/edit/", views.editModel, name="index"),
    path(
        "<str:sheettype>s/<int:pk>/update/",
        views.FSAdd.as_view(),
        {"method": "update"},
        name="index",
    ),
]
