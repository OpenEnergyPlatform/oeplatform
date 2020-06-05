from django.conf.urls import url
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from os import walk
from ontology import views
from oeplatform import settings

urlpatterns = [
  url(r"^$", TemplateView.as_view(template_name="ontology/about.html")),
  url(r"^ontology/oeo-steering-committee$",
      TemplateView.as_view(template_name="ontology/oeo-steering-committee.html"),
      name="oeo-s-c"),
  url(r"^oeo$",
      views.OntologyOverview.as_view(),
      name="oeo"),
  url(r"^releases\/(?P<ontology>[\w_-]+)(\/(?P<version>[\d\.]+))?\/(?P<file>[\w_-]+)(.(?P<extension>[\w_-]+))?$",
      views.OntologyStatics.as_view()),
]
