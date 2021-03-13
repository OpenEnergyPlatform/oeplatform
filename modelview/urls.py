from django.conf.urls import url
from django.conf.urls.static import static

from modelview import views
from oeplatform import settings

urlpatterns = [
    url(r"study/(?P<identifier>[\w\d_]*)/$", views.StudyRDFView.as_view()),
    url(r"study/(?P<identifier>[\w\d_]*)/edit", views.StudyRDFFormView.as_view()),
    url(r"^(?P<sheettype>[\w\d_]+)s/$", views.listsheets, {}, name="modellist"),
    url(r"^overview/$", views.overview, {}),
    url(
        r"^(?P<sheettype>[\w\d_]+)s/add/$",
        views.FSAdd.as_view(),
        {"method": "add"},
        name="modellist",
    ),

    url(r"^(?P<sheettype>[\w\d_]+)s/download/$", views.model_to_csv, {}, name="index"),
    url(
        r"^(?P<sheettype>[\w\d_]+)s/(?P<model_name>[\d]+)/$",
        views.show,
        {},
        name="index",
    ),
    url(
        r"^(?P<sheettype>[\w\d_]+)s/(?P<model_name>[\d]+)/edit/$",
        views.editModel,
        {},
        name="index",
    ),
    url(
        r"^(?P<sheettype>[\w\d_]+)s/(?P<pk>[\d]+)/update/$",
        views.FSAdd.as_view(),
        {"method": "update"},
        name="index",
    ),
]
