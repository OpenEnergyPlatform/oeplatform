import requests
from django.http import JsonResponse
from django.shortcuts import render


def main_view(request):
    response = render(request, "sparql_query/main.html")
    response["Content-Type"] = "text/html; charset=utf-8"
    return response


def sparql_endpoint(request):
    sparql_query = request.GET.get("query", "")
    endpoint_url = (
        "http://localhost:3030/ds/sparql"  # Must be replaced by the url for OEKG
    )

    headers = {"Accept": "application/sparql-results+json"}

    response = requests.get(
        endpoint_url, params={"query": sparql_query}, headers=headers
    )

    return JsonResponse(response.json())
