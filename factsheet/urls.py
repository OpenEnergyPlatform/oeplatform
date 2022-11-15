from django.urls import path
from factsheet import views

urlpatterns = [
    path(r"", views.factsheets_index),
    path(r"add/", views.create_factsheet),
    path(r"update/", views.update_factsheet),
    path(r"name/", views.factsheet_by_name),
    path(r"get/", views.factsheet_by_id),
    path(r"all/", views.get_all_factsheet)
]
