from django.conf.urls import url

from modelview import views
from oeplatform import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^(?P<sheettype>[\w\d_]+)s/$', views.listsheets, {}, name='modellist'),
    url(r'^(?P<sheettype>[\w\d_]+)s/add/$', views.FSAdd.as_view(), {'method':'add'}, name='modellist'),
    url(r'^(?P<sheettype>[\w\d_]+)s/(?P<model_name>[\w\d_]+)/$', views.show, {},  name='index'),
    url(r'^(?P<sheettype>[\w\d_]+)s/(?P<model_name>[\w\d_]+)/edit/$', views.editModel, {}, name='index'),
    url(r'^(?P<sheettype>[\w\d_]+)s/(?P<pk>[\w\d_]+)/update/$', views.FSAdd.as_view(), {'method':'update'}, name='index'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
