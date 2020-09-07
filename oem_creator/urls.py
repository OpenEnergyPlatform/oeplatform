from django.urls import path
from django.conf.urls import url
from oem_creator import views
from django.views.generic.base import TemplateView
from django.views.generic import RedirectView
from django.urls import path, include
app_name = 'oem_creator'


urlpatterns = [
    #url(r"^$", TemplateView.as_view(template_name='meta_creator/bla.html')),
    #url(r"^$", TemplateView.as_view(template_name='meta_creator/creator.html')),
    #url(r"^$", TemplateView.as_view(name='creator')),
    #url(r"^3$", RedirectView.as_view(pattern_name='oem_creator:form')), #leitet nur weiter
    url(r"^$", views.CreatorView.as_view(), name='form'),
    #url(r"^1/$", views.CreatorView_some.as_view(), name='some'),
    #path('', views.CreatorView_some(), name='some'),
    #path('', views.CreatorView_some("test"))
]

