import types
import uuid
from pathlib import Path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render  # noqa:F401
from django.views.generic import View
from owlready2 import *

from oeplatform.settings import ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME
from ontology.utility import get_ontology_version

OEO_BASE_PATH = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)
OEO_VERSION = get_ontology_version(OEO_BASE_PATH)
OEO_PATH = str(OEO_BASE_PATH) + "/" + str(OEO_VERSION) + "/oeo-full.owl"
OEO_EXT_PATH = str(Path(ONTOLOGY_ROOT)) + "/oeo_ext/oeo_ext.owl"

oeo = get_ontology(OEO_PATH)
oeo.load()

oeo_ext = get_ontology(OEO_EXT_PATH)
oeo_ext.load()
# oeo_ext.base_iri = "http://openenergy-platform.org/ontology/oeo/oeo_ext/oeo_ext.owl#"

# Static parts, object properties:
has_linear_unit_numerator = oeo.search_one(label="has unit numerator")
has_linear_unit_denominator = oeo.search_one(label="has linear unit denominator")
has_squared_unit_denominator = oeo.search_one(label="has squared unit denominator")

# Dynamic parts, retrieve oeo classes based on user inputs:
unit = oeo.search_one(label="unit")
watt_hour = oeo.search_one(label="watt-hour")
mega = oeo.search_one(label="mega")
meter = oeo.search_one(label="meter")
year = oeo.search_one(label="year")


# Suggested views maybe you will use other ones @adel
class OeoExtPluginView(View, LoginRequiredMixin):
    """
    Some text Some textSome textSome textSome textSome textSome textSome
    """

    def get(self, request):
        print(request)
        new_class_iri = "http://purl.obolibrary.org/obo/ext/" + "4"

        with oeo_ext:
            NewClass = types.new_class(new_class_iri, (unit,))
            NewClass.label = "Megawatt−hour per square meter and year"
            NewClass.equivalent_to = [
                (
                    has_linear_unit_numerator.some(watt_hour)
                    & has_squared_unit_denominator.some(meter)
                    & has_squared_unit_denominator.some(year)
                )
            ]

        oeo_ext.save(file=OEO_EXT_PATH, format="rdfxml")

        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")

    def post(self, request):
        print("post")
        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")
