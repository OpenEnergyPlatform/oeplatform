from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<model_name>.+)/$', views.ModelView.as_view(), name='index'),
]
