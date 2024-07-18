from django.urls import path

from .views import main_view, sparql_endpoint

urlpatterns = [
    path("gui/", main_view, name="main"),
    path("sparql/", sparql_endpoint, name="sparql_endpoint"),
]
