from django.conf.urls import url

from login import views

urlpatterns = [
    url(r'^profile/(?P<user_id>[\d]+)$',
            views.ProfileView.as_view(), name='input'),
    url(r'^profile/(?P<user_id>[\d]+)/passwd$',
        views.OEPPasswordChangeView.as_view(), name='input'),
    url(r'^profile/(?P<user_id>[\d]+)/edit$', views.EditUserView.as_view(), name='input'),
    url(r'^groups/$', views.GroupManagement.as_view(), name='input'),
    url(r'^groups/(?P<group_id>[\w\d_\s]+)/edit', views.GroupCreate.as_view(), name='input'),
    url(r'^groups/(?P<group_id>[\w\d_\s]+)/members$', views.GroupEdit.as_view(), name='input'),
    url(r'^groups/new/$', views.GroupCreate.as_view(), name='input'),
    url(r'^register$', views.CreateUserView.as_view()),
    url(r'^detach$', views.DetachView.as_view()),
]
