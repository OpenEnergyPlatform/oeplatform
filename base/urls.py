from django.conf.urls import url

from base import views

urlpatterns = [
    url(r'^$', views.Welcome.as_view(), name='index'),
]
