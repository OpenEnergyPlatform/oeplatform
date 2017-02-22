from django.conf.urls import url

from . import views

pgsql_qualifier = r"[\w\d_]+"

urlpatterns = [
    url(r'^$', views.listdbs, name='index'),
    url(r'^profie/', views.ProfileView.as_view(), name='input'),
    url(r'^group/', views.GroupManagement.as_view(), name='input'),
    url(r'^group/edit/', views.GroupEdit.as_view(), name='input'),
]
