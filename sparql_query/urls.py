from django.urls import path

from .views import main_view, sparql_endpoint

urlpatterns = [
    path("main/", main_view, name="main"),
    path("sparql/", sparql_endpoint, name="sparql_endpoint"),
]
