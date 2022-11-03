from django.urls import path
from factsheet import views

urlpatterns = [
    path(r"", views.factsheets_index),
    path(r"add/", views.create_factsheet, name='FS')
]
