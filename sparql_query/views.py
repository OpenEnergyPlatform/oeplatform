import requests
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from oeplatform.settings import OEKG_SPARQL_ENDPOINT_URL
from sparql_query.utils import validate_sparql_query


def main_view(request):
    response = render(request, "sparql_query/main.html")
    response["Content-Type"] = "text/html; charset=utf-8"
    return response


@require_POST
def sparql_endpoint(request):
    sparql_query = request.POST.get("query", "")

    if not sparql_query:
        return HttpResponseBadRequest("Missing 'query' parameter.")

    if not validate_sparql_query(sparql_query):
        raise SuspiciousOperation("Invalid SPARQL query.")

    endpoint_url = OEKG_SPARQL_ENDPOINT_URL

    headers = {"Accept": "application/sparql-results+json"}

    response = requests.post(
        endpoint_url, params={"query": sparql_query}, headers=headers
    )

    return JsonResponse(response.json())
