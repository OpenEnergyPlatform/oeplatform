import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from oekg.utils import execute_sparql_query
from oeplatform.settings import DOCUMENTATION_LINKS


@login_required
def main_view(request):
    response = render(
        request, "oekg/main.html", context={"oekg_api": DOCUMENTATION_LINKS["oekg_api"]}
    )
    response["Content-Type"] = "text/html; charset=utf-8"
    return response


@require_POST
def sparql_endpoint(request):
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
def sparql_metadata(request):
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
