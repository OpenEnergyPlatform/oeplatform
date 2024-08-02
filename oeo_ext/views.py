import types

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render  # noqa:F401
from django.views.generic import View
from owlready2 import get_ontology
from rdflib import Graph

from oeo_ext.oekb.connection import oeo_owl
from oeo_ext.utils import get_class_data, get_new_iri
from oeplatform.settings import ONTOLOGY_ROOT

OEO_EXT_PATH = ONTOLOGY_ROOT / "oeo_ext/oeo_ext.owl"

# load oeo via common interface
oeo = oeo_owl

oeo_ext = Graph()
oeo_ext.parse(OEO_EXT_PATH.as_uri())
oeo_ext_owl = get_ontology(OEO_EXT_PATH.as_posix()).load()

# oeo_ext.base_iri = "http://openenergy-platform.org/ontology/oeo/oeo_ext/oeo_ext.owl#"

# Static parts, object properties:
has_linear_unit_numerator = oeo.search_one(label="has unit numerator")
has_squared_unit_numerator = oeo.search_one(label="has squared unit numerator")
has_cubed_unit_numerator = oeo.search_one(label="has cubed unit numerator")
has_linear_unit_denominator = oeo.search_one(label="has linear unit denominator")
has_squared_unit_denominator = oeo.search_one(label="has squared unit denominator")
has_cubed_unit_denominator = oeo.search_one(label="has cubed unit denominator")
unit = oeo.search_one(label="unit")

UNITS = oeo.search(label="unit")


# Suggested views maybe you will use other ones @adel
class OeoExtPluginView(View, LoginRequiredMixin):
    """
    Some text Some textSome textSome textSome textSome textSome textSome
    """

    def get(self, request):
        print(request)

        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")

    def post(self, request):
        print("post")

        new_class_iri = get_new_iri(ontox=oeo_ext_owl)
        label_of_unit, classesUsed = get_class_data()
        lists = list(classesUsed.keys())
        class_definition = "( "
        for i in range(0, len(lists)):
            for units_used in classesUsed[lists[i]]:
                locals()[units_used] = oeo.search_one(label=units_used)
                class_definition += (
                    "has_" + str(lists[i])[:-1] + ".some(" + units_used + ") &"
                )
        class_definition = class_definition[:-1]
        class_definition += " )"

        with oeo_ext_owl:
            NewClass = types.new_class(new_class_iri, (UNITS,))
            NewClass.label = str(label_of_unit)
            NewClass.equivalent_to = [eval(class_definition)]
        oeo_ext_owl.save(file=OEO_EXT_PATH, format="rdfxml")

        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")


def add_unit_element(request):
    return render(request, "oeo_ext/partials/unit_element.html")


# def search_units(request):
#     query = request.GET.get("query", "")
#     results = []
#     if query:
#         results = ["search_ontology(query)"]

#     return JsonResponse({"data": results})
