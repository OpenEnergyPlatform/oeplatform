from django.conf.urls import url

from login import views

urlpatterns = [
    url(r'^profile/(?P<user_id>[\w\d_\s]+)$', views.ProfileView.as_view(), name='input'),
    url(r'^create$', views.create_user),
]
