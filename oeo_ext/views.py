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
#oeo_ext.base_iri = "http://openenergy-platform.org/ontology/oeo/oeo_ext/oeo_ext.owl#"

# Static parts, object properties:
has_linear_unit_numerator = oeo.search_one(label="has unit numerator")
has_squared_unit_numerator = onto.search_one(label='has squared unit numerator')
has_cubed_unit_numerator = onto.search_one(label='has cubed unit numerator')
has_linear_unit_denominator = oeo.search_one(label="has linear unit denominator")
has_squared_unit_denominator = oeo.search_one(label="has squared unit denominator")
has_cubed_unit_denominator = onto.search_one(label='has cubed unit denominator')

unit = oeo.search_one(label="unit")



# Suggested views maybe you will use other ones @adel
class OeoExtPluginView(View, LoginRequiredMixin):
    """
    Some text Some textSome textSome textSome textSome textSome textSome
    """
    
    def take_user_input():
        units_used = []
        D = { 'linear_unit_numerators': [], 
        'squared_unit_numerators' : [],
        'cubed_unit_numerators' : [],
        'linear_unit_denominators' : [],
        'squared_unit_denominators' : [],
        'cubed_unit_denominators' : [] }
        label = str(input("Enter new units name : "))
        n = int(input("Enter number of existing units needed : "))
        for i in range(0, n):
            this_unit = str(input("Enter " + str(i+1) + ". unit: "))
            n_or_d = str(input("Is " + this_unit + " used as a numerator or denominator? [n/d]"))
            while not(n_or_d == "n" or n_or_d == "d"):
                print("Faulty Input! Please input 'n' for numerator or 'd' for denominator!")
                n_or_d = str(input("Is " + this_unit + " used as a numerator or denominator? [n/d]"))
            l_or_s = str(input("Is " + this_unit + " used linear, squared or cubed? [l/s/c]"))
            while not(l_or_s == "l" or l_or_s == "s" or l_or_s == "c"):
                print("Faulty Input! Please input 'l' for linear, 's' for squared or 'c' for cubed!")
                l_or_s = str(input("Is " + u + " used linear, squared or cubed? [l/s/c]"))
            if (n_or_d == "n"):
                if (l_or_s == "l"):
                    D['linear_unit_numerators'].append(this_unit)
                elif (l_or_s == "s"):
                    D['squared_unit_numerators'].append(this_unit)
                elif (l_or_s == "c"):
                    D['cubed_unit_numerators'].append(this_unit)
            elif (n_or_d == "d"):
                if (l_or_s == "l"):
                    D['linear_unit_denominators'].append(this_unit)
                elif (l_or_s == "s"):
                    D['squared_unit_denominators'].append(this_unit)
                elif (l_or_s == "c"):
                    D['cubed_unit_denominators'].append(this_unit)
        return label, D
    
    def get_new_iri():
        for annot_prop in ontox.metadata:
            for i in range(len(annot_prop[ontox.metadata])):
                if ("0000Counter = " in annot_prop[ontox.metadata][i]):
                    newNr = annot_prop[ontox.metadata][i][len("0000Counter = "):]
                    counter = int(newNr) +1
                    annot_prop[ontox.metadata][i] = "0000Counter = " + str(counter)
            ontox.save()
        new_class_iri = "http://purl.obolibrary.org/obo/ext/OEO_0000" + f"{str(counter):0>4}"
        return new_class_iri

    def get(self, request):
        print(request)
        new_class_iri = get_new_iri()
        label_of_unit, classesUsed = get_class_data()
        lists = list(classesUsed.keys())
        class_definition = "( "
        for i in range(0, len(lists)):
            for units_used in classesUsed[lists[i]]:
                locals()[units_used] = onto.search_one(label=units_used)
                class_definition += "has_" + str(lists[i])[:-1] + ".some(" + units_used + ") &"
        class_definition = class_definition[:-1]
        class_definition += " )"
        import types
        with ontox:
            NewClass = types.new_class(new_class_iri, (unit,))
            NewClass.label=str(label_of_unit)
            NewClass.equivalent_to = [
              eval(class_definition)
            ]
        oeo_ext.save(file= OEO_EXT_PATH, format="rdfxml")

        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")

    def post(self, request):
        print("post")
        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html")
