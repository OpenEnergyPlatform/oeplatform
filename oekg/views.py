"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from oekg.registry.loader import load_registry
from oekg.utils import execute_filter_sparql_query, execute_sparql_query
from oeplatform.settings import DOCUMENTATION_LINKS


@login_required
def main_view(request):
    response = render(
        request, "oekg/main.html", context={"oekg_api": DOCUMENTATION_LINKS["oekg_api"]}
    )
    response["Content-Type"] = "text/html; charset=utf-8"
    return response


@require_GET
def dimension_registry_view(request):
    """Serve the Dimension Property Registry contract (registry.json).

    The single shared vocabulary consumed by the comparison frontend (to build
    dynamic SPARQL + filter UI) and by the mapping generator (passed as a dict).
    Source of truth: oekg/registry/dimension_property_registry.yaml.
    """
    return JsonResponse(load_registry(), safe=False)


@require_POST
def sparql_endpoint_view(request):
    """
    Internal SPARQL endpoint. Must only allow read queries. Intended to be use
    with a djago app frontend as it requires an CSRF token.

    Note: The http based oekg sparql endpoint is implemented in api/views.py
    OekgSparqlAPIView. It is usable by providing a valid API key in the request
    """
    sparql_query = request.POST.get("query", "")
    response_format = request.POST.get("format", "json")  # Default format

    try:
        content, content_type = execute_sparql_query(sparql_query, response_format)
    except ValueError as e:
        return HttpResponseBadRequest(
            f"{str(e)}. Please provide a valid SPARQL query."
            "This does not include update/delete queries."
        )

    if content_type == "application/sparql-results+json":
        return JsonResponse(json.loads(content), safe=False)
    else:
        return HttpResponse(content, content_type=content_type)


@require_GET
def sparql_metadata_view(request):
    supported_formats = {
        "json": "application/sparql-results+json",
        "json-ld": "application/ld+json",
        "xml": "application/rdf+xml",
        "turtle": "text/turtle",
    }
    return JsonResponse(
        {
            "description": "This API accepts SPARQL queries and returns"
            "the results in various formats.",
            "supported_formats": supported_formats,
        }
    )


# @login_required
@require_POST
def filter_oekg_by_scenario_bundles_attributes_view(request):
    """
    This function takes filter objects provided by the user and utilises
    them to construct a SPARQL query.

    Args:
        request (HttpRequest): The incoming HTTP GET request.
        criteria (str): An object that contains institutions, authors,
        funding sources, start date of the publications, end date of publications
        study descriptors, and a range for scenario years. All of these fields
        are utilised to construct a SPARQL query for execution on the OEKG.

    """
    request_body = json.loads(request.body)

    criteria = request_body.get("criteria", {})
    results = execute_filter_sparql_query(criteria)

    response = JsonResponse(
        results.get("results", [])["bindings"],
        safe=False,
        content_type="application/json",
    )
    return response
