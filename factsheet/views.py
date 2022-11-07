from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework import status
from .models import Factsheet
import json
from django.views.decorators.csrf import csrf_exempt

def factsheets_index(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')

@csrf_exempt
def create_factsheet(request, *args, **kwargs):
    name = request.GET.get('name')
    acronym = request.GET.get('acronym')
    study_name = request.GET.get('study_name')
    abstract = request.GET.get('abstract')
    institution = request.GET.get('institution')
    funding_source = request.GET.get('funding_source')
    authors = request.GET.get('authors')
    contact_person = request.GET.get('contact_person')
    doi = request.GET.get('doi')
    place_of_publication = request.GET.get('place_of_publication')
    link_to_study = request.GET.get('link_to_study')
    scenario_name = request.GET.get('scenario_name')
    scenario_abstract = request.GET.get('scenario_abstract')
    scenario_acronym = request.GET.get('scenario_acronym')
    scenario_region = request.GET.get('scenario_region')
    scenario_interacting_region = request.GET.get('scenario_interacting_region')
    energy_carriers = request.GET.get('energy_carriers')
    energy_transportation = request.GET.get('energy_transportation')

    factsheet_obj = {
        'name': name,
        'acronym': acronym,
        'study_name': study_name,
        'abstract': abstract,
        'institution': institution,
        'funding_source': funding_source,
        'authors': authors,
        'contact_person': contact_person,
        'doi': doi,
        'place_of_publication': place_of_publication,
        'link_to_study': link_to_study,
        'scenario_name': scenario_name,
        'scenario_abstract': scenario_abstract,
        'scenario_acronym': scenario_acronym,
        'scenario_region': scenario_region,
        'scenario_interacting_region': scenario_interacting_region,
        'energy_carriers': energy_carriers,
        'energy_transportation': energy_transportation,
        }

    fs = Factsheet(factsheetData=factsheet_obj)

    fs.save()
    return JsonResponse(factsheet_obj, status=status.HTTP_201_CREATED)

def factsheet_by_id(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')
