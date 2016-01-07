from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.DataView.as_view(), name='index'),
    url(r'^edit', views.DataInputView.as_view(), name='input'),
    url(r'^view', views.DataView.as_view(), name='input'),
    url(r'^upload', views.DataUploadView.as_view(), name='input'),
    url(r'^map', views.DataMapView.as_view(), name='input'),
]
