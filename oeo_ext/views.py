from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render  # noqa:F401
from django.views.generic import View
from pathlib import Path
from oeplatform.settings import ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME
from ontology.utility import get_ontology_version
from owlready2 import *
import uuid
import types

OEO_BASE_PATH = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)
OEO_VERSION = get_ontology_version(OEO_BASE_PATH)
OEO_PATH = str(OEO_BASE_PATH) + "/" + str(OEO_VERSION) + "/oeo-full.owl"

oeo = get_ontology(OEO_PATH)
oeo.load()

oeo_ext = get_ontology("http://openenergy-platform.org/ontology/oeox/")

# Static parts, object properties:
has_linear_unit_numerator = oeo.search_one(label='has unit numerator')
has_linear_unit_denominator = oeo.search_one(label='has linear unit denominator')
has_squared_unit_denominator = oeo.search_one(label='has squared unit denominator')


# Dynamic parts, retrieve oeo classes based on user inputs:
unit = oeo.search_one(label="unit")
watt_hour = oeo.search_one(label="watt-hour")
mega = oeo.search_one(label="mega")
meter = oeo.search_one(label="meter")
year = oeo.search_one(label="year")


new_class_iri = 'http://purl.obolibrary.org/obo/ext/' + str(uuid.uuid4())

with oeo_ext:
    NewClass = types.new_class(new_class_iri, (unit,))
    NewClass.label="Megawatt−hour per square meter and year"
    NewClass.equivalent_to = [
      ( has_linear_unit_numerator.some(watt_hour)
        & has_squared_unit_denominator.some(meter)
        & has_linear_unit_denominator.some(year)
        )
    ]

oeo_ext.save(file="oeo_ext.owl", format="rdfxml")

# Suggested views maybe you will use other ones @adel
class OeoExtPluginView(View, LoginRequiredMixin):
    """
    Some text Some textSome textSome textSome textSome textSome textSome
    """

    def get(self, request):
        print('get')
        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")

    def post(self, request):
        print('post')
        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")
