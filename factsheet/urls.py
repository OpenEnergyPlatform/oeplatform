from django.urls import path, re_path
from factsheet import views


urlpatterns = [
    path(r'', views.factsheets_index),
    re_path(r'^fs/*', views.factsheets_index),
    path(r"add/", views.create_factsheet),
    path(r"update/", views.update_factsheet),
    path(r"name/", views.factsheet_by_name),
    path(r"get/", views.factsheet_by_id),
    path(r"delete/", views.delete_factsheet_by_id),
    path(r"all/", views.get_all_factsheets),
    path(r"all_in_turtle/", views.get_all_factsheets_as_turtle),
    path(r"all_in_jsonld/", views.get_all_factsheets_as_json_ld),
    
]
