from django.conf.urls import url
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView

from modelview import views
from oeplatform import settings

urlpatterns = [
  url(r"^$", TemplateView.as_view(template_name="ontology/about.html")),
  url(r"^ontology/oeo-steering-committee$",
      TemplateView.as_view(template_name="ontology/oeo-steering-committee.html"),
      name="oeo-s-c"),
] + [url(r"^{path}$".format(path=path), RedirectView.as_view(url=red)) for path, red in
   [
       ("oeo/oeo-physical.omn",
        "https://raw.githubusercontent.com/OpenEnergyPlatform/ontology/dev/src/ontology/edits/oeo-physical.omn"),
       ("oeo/oeo-model.omn",
        "https://raw.githubusercontent.com/OpenEnergyPlatform/ontology/dev/src/ontology/edits/oeo-model.omn"),
       ("oeo/oeo-social.omn",
        "https://raw.githubusercontent.com/OpenEnergyPlatform/ontology/dev/src/ontology/edits/oeo-social.omn"),
       ("oeo/imports/iao-annotation-module.owl",
        "https://raw.githubusercontent.com/OpenEnergyPlatform/ontology/dev/src/ontology/imports/iao-annotation-module.owl"),
       ("oeo/imports/iao-module.owl",
        "https://raw.githubusercontent.com/OpenEnergyPlatform/ontology/dev/src/ontology/imports/iao-module.owl"),
       ("imports/ro-module.owl",
        "https://raw.githubusercontent.com/OpenEnergyPlatform/ontology/dev/src/ontology/imports/ro-module.owl")
   ]]
