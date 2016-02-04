from django.conf.urls import url

from . import views
from oeplatform import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^(?P<model_name>[\w\d_]+)/$', views.show, name='index'),
    url(r'^(?P<model_name>[\w\d_]+)/edit/$', views.editModel, name='index'),
    url(r'^(?P<model_name>[\w\d_]+)/update/$', views.updateModel, name='index'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
