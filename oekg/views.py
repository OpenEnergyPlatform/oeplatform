import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from oekg.utils import execute_sparql_query


@login_required
def main_view(request):
    response = render(request, "oekg/main.html")
    response["Content-Type"] = "text/html; charset=utf-8"
    return response


# TODO: This endpoint requires a CSRF token, to be usable via a
# https call using CURL or requests (what the user expects when using a web-api)
# this endpoint must also accessible using the API token via the RestFramework.
@require_POST
def sparql_endpoint(request):
    sparql_query = request.POST.get("query", "")
    response_format = request.POST.get("format", "json")  # Default format

    try:
        content, content_type = execute_sparql_query(sparql_query, response_format)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    if content_type == "application/sparql-results+json":
        return JsonResponse(json.loads(content), safe=False)
    else:
        return HttpResponse(content, content_type=content_type)


# def sparql_endpoint(request):
#     sparql_query = request.POST.get("query", "")
#     response_format = request.POST.get("format", "json")  # Default format

#     # Whitelist of supported formats
#     supported_formats = {
#         "json": "application/sparql-results+json",
#         "json-ld": "application/ld+json",
#         "xml": "application/rdf+xml",
#         "turtle": "text/turtle",
#     }

#     if not sparql_query:
#         return HttpResponseBadRequest("Missing 'query' parameter.")

#     if not validate_sparql_query(sparql_query):
#         raise SuspiciousOperation("Invalid SPARQL query.")

#     # Validate and map the requested format
#     if response_format not in supported_formats:
#         return HttpResponseBadRequest(f"Unsupported format: {response_format}")

#     endpoint_url = OEKG_SPARQL_ENDPOINT_URL
#     headers = {"Accept": supported_formats[response_format]}

#     response = requests.post(
#         endpoint_url, data={"query": sparql_query}, headers=headers
#     )

#     # Handle different response types
#     content_type = supported_formats[response_format]
#     if content_type == "application/sparql-results+json":
#         return JsonResponse(response.json(), safe=False)
#     else:
#         return HttpResponse(response.content, content_type=content_type)


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
