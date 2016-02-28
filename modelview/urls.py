from django.conf.urls import url

from modelview import views
from oeplatform import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^models/$', views.listsheets, {'sheettype':'model'}, name='modellist'),
    url(r'^models/add/$', views.ModelAdd.as_view(), name='modellist'),
    url(r'^models/(?P<model_name>[\w\d_]+)/$', views.show, {'sheettype':'model'},  name='index'),
    url(r'^models/(?P<model_name>[\w\d_]+)/edit/$', views.editModel, name='index'),
    url(r'^models/(?P<model_name>[\w\d_]+)/update/$', views.updateModel, name='index'),
    
    url(r'^frameworks/$', views.listsheets, {'sheettype':'framework'}, name='modellist'),
    url(r'^frameworks/add/$', views.FrameworkAdd.as_view(), name='modellist'),
    url(r'^frameworks/(?P<model_name>[\w\d_]+)/$',  views.show, {'sheettype':'framework'}, name='index'),
    url(r'^frameworks/(?P<model_name>[\w\d_]+)/edit/$', views.editModel, name='index'),
    url(r'^frameworks/(?P<model_name>[\w\d_]+)/update/$', views.updateModel, name='index'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
