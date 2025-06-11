# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Hannah Spinde <hannah.spinde@st.ovgu.de> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render  # noqa:F401
from django.views.generic import View

from oeo_ext.forms import ComposedUnitFormWrapper, UnitEntryForm
from oeo_ext.utils import create_new_unit
from oeplatform.settings import EXTERNAL_URLS


# Suggested views maybe you will use other ones @adel
class OeoExtPluginView(View, LoginRequiredMixin):
    """
    Some text Some textSome textSome textSome textSome textSome textSome
    """

    def get(self, request):
        form = ComposedUnitFormWrapper()
        context = {
            "form": form,
            "nominator_forms": [],
            "denominator_forms": [],
            "oeox_github_link": EXTERNAL_URLS["oeo_extended_github"],
        }
        return render(request, "oeo_ext/partials/oeo-ext-plugin-ui.html", context)

    def post(self, request):
        try:
            data = json.loads(request.POST.get("data", None))
            form = ComposedUnitFormWrapper(data)

            nominator_data = data.get("nominator", [])
            denominator_data = data.get("denominator", [])

            nominator_forms = [UnitEntryForm(item) for item in nominator_data]
            denominator_forms = [UnitEntryForm(item) for item in denominator_data]

            all_forms_valid = (
                form.is_valid()
                and all(f.is_valid() for f in nominator_forms)
                and all(f.is_valid() for f in denominator_forms)
            )

            if all_forms_valid:
                data = {
                    "success": True,
                    "message": "Form data is valid",
                    "data": {
                        "definition": form.cleaned_data.get("definition"),
                        "unitLabel": form.cleaned_data.get("unitLabel"),
                        "nominator": [f.cleaned_data for f in nominator_forms],
                        "denominator": [f.cleaned_data for f in denominator_forms],
                    },
                    "newComposedUnitURI": None,
                }
                n = data.get("data", {})["nominator"]
                d = data.get("data", {})["denominator"]
                # new_unit_uir is either URIRef type or None
                # error is either dict with key:value or None
                new_unit, error = create_new_unit(numerator=n, denominator=d)
                if error:
                    # response_data = error
                    response_data = {
                        "success": False,
                        "message": "Form data is not valid!",
                        "errors": error,
                    }
                else:
                    data["newComposedUnitURI"] = new_unit
                    response_data = data
                return render(
                    request,
                    "oeo_ext/partials/success.html",
                    {"response_data": response_data},
                )
                # return JsonResponse(response_data, status=200)
            else:
                errors = {
                    "form_errors": form.errors,
                    "nominator_errors": [f.errors for f in nominator_forms],
                    "denominator_errors": [f.errors for f in denominator_forms],
                }
                response_data = {"success": False, "errors": errors}
                return JsonResponse(response_data, status=400)
        except json.JSONDecodeError as e:
            response_data = {"success": False, "errors": {"json_error": str(e)}}
            return JsonResponse(response_data, status=400)


def add_unit_element(request):
    unit_id = None
    unit_id = request.session.get("unit_id_counter", 0)
    # Increment the counter
    unit_id += 1
    # Save the new counter value back to the session
    request.session["unit_id_counter"] = unit_id

    return render(
        request, "oeo_ext/partials/unit_element.html", context={"unit_id": str(unit_id)}
    )


# def search_units(request):
# can only be implemented if there is a way to get all classes form the oeo
# that are a unit
#     query = request.GET.get("query", "")
#     results = []
#     if query:
#         results = ["search_ontology(query)"]

#     return JsonResponse({"data": results})
