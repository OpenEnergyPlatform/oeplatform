from django.conf.urls import url

from login import views

urlpatterns = [
    url(r'^profile/(?P<user_id>[\w\d_\s]+)$', views.ProfileView.as_view(), name='input'),
    url(r'^groups/$', views.GroupManagement.as_view(), name='input'),
    url(r'^groups/(?P<group_id>[\w\d_\s]+)/edit', views.GroupCreate.as_view(), name='input'),
    url(r'^groups/(?P<group_id>[\w\d_\s]+)/members$', views.GroupEdit.as_view(), name='input'),
    url(r'^groups/new/$', views.GroupCreate.as_view(), name='input'),
    url(r'^create$', views.create_user),
]
