from django.conf.urls import url

from tutorial import views



pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^$', views.tutorial_home,),
    url(r'^database_conform_data/$', views.database_conform_data,),
]
