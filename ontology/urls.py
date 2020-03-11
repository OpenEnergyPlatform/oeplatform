from django.conf.urls import url
from django.conf.urls.static import static
from django.views.generic import TemplateView

from modelview import views
from oeplatform import settings

urlpatterns = [
    url(r"^$", TemplateView.as_view(template_name="ontology/about.html")),
]
