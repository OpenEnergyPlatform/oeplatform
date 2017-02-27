from django.conf.urls import url

from login import views

urlpatterns = [
    url(r'^profile/(?P<user_id>[\w\d_\s]+)$', views.ProfileView.as_view(), name='input'),
    url(r'^(?P<user_id>[\w\d_\s]+)/group/$', views.GroupManagement.as_view(), name='input'),
    url(r'^(?P<user_id>[\w\d_\s]+)/group/edit/(?P<group_id>[\w\d_\s]+)$', views.GroupEdit.as_view(), name='input'),
    url(r'^(?P<user_id>[\w\d_\s]+)/group/new/$', views.GroupEdit.as_view(), name='input'),
    url(r'^create$', views.create_user),
]
