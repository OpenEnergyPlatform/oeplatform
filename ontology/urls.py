from django.conf.urls import url
from django.conf.urls.static import static
from django.views.generic import TemplateView

from modelview import views
from oeplatform import settings

owl_qualifier = r"[\w\d_]+"


urlpatterns = [
    url(r"^$", TemplateView.as_view(template_name="ontology/about.html")),
    url(rf"^browse/(?P<id>{owl_qualifier})$", TemplateView.as_view(template_name="ontology/about.html")),
]
