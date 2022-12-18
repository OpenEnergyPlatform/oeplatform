from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework import status
from .models import Factsheet
import json
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers


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
    sector_divisions = request.GET.get('sector_divisions')
    sectors = request.GET.get('sectors')
    scenario_energy_carriers = request.GET.get('scenario_energy_carriers')
    scenario_energy_transportation_process = request.GET.get('scenario_energy_transportation_process')
    contact_person = request.GET.get('contact_person')
    doi = request.GET.get('doi')
    place_of_publication = request.GET.get('place_of_publication')
    link_to_study = request.GET.get('link_to_study')
    scenarios_name = request.GET.get('scenarios_name')
    scenarios_acronym = request.GET.get('scenarios_acronym')
    scenarios_abstract = request.GET.get('scenarios_abstract')
    scenarios_region = request.GET.get('scenarios_region')
    scenarios_interacting_region = request.GET.get('scenarios_interacting_region')
    scenarios_years = request.GET.get('scenarios_years')
    scenarios_keywords = request.GET.get('scenarios_keywords')
    scenarios_input_datasets = request.GET.get('scenarios_input_datasets')
    scenarios_output_datasets = request.GET.get('scenarios_output_datasets')

    factsheet_obj = {
        'name': name,
        'acronym': acronym,
        'study_name': study_name,
        'abstract': abstract,
        'institution': json.loads(institution),
        'funding_source': funding_source,
        'authors': authors,
        'contact_person': contact_person,
        'sector_divisions': sector_divisions,
        'scenario_energy_transportation_process': scenario_energy_transportation_process,
        'scenario_energy_carriers': scenario_energy_carriers,
        'sectors': sectors,
        'doi': doi,
        'place_of_publication': place_of_publication,
        'link_to_study': link_to_study,
        'scenarios_name': json.loads(scenarios_name),
        'scenarios_acronym': json.loads(scenarios_acronym),
        'scenarios_abstract': json.loads(scenarios_abstract),
        'scenarios_region': json.loads(scenarios_region),
        'scenarios_interacting_region': json.loads(scenarios_interacting_region),
        'scenarios_years': json.loads(scenarios_years),
        'scenarios_keywords': json.loads(scenarios_keywords),
        'scenarios_keywords': json.loads(scenarios_keywords),
        'scenarios_input_datasets': json.loads(scenarios_input_datasets),
        'scenarios_output_datasets': json.loads(scenarios_output_datasets),
        }

    fs = Factsheet(factsheetData=factsheet_obj)
    fs.save()
    return JsonResponse(factsheet_obj, status=status.HTTP_201_CREATED)

@csrf_exempt
def update_factsheet(request, *args, **kwargs):
    id = request.GET.get('id')
    name = request.GET.get('name')
    studyName = request.GET.get('study_name')
    acronym = request.GET.get('acronym')
    abstract = request.GET.get('abstract')
    institution = request.GET.get('institution')
    funding_source = request.GET.get('funding_source')
    contact_person = request.GET.get('contact_person')
    sector_divisions = request.GET.get('sector_divisions')
    sectors = request.GET.get('sectors')
    scenario_energy_carriers = request.GET.get('scenario_energy_carriers')
    scenario_energy_transportation_process = request.GET.get('scenario_energy_transportation_process')
    report_title = request.GET.get('report_title')
    date_of_publication = request.GET.get('date_of_publication')
    doi = request.GET.get('doi')
    place_of_publication = request.GET.get('place_of_publication')
    link_to_study = request.GET.get('link_to_study')
    authors = request.GET.get('authors')
    scenarios_name = request.GET.get('scenarios_name')
    scenarios_acronym = request.GET.get('scenarios_acronym')
    scenarios_abstract = request.GET.get('scenarios_abstract')
    scenarios_region = request.GET.get('scenarios_region')
    scenarios_interacting_region = request.GET.get('scenarios_interacting_region')
    scenarios_years = request.GET.get('scenarios_years')
    scenarios_keywords = request.GET.get('scenarios_keywords')
    scenarios_input_datasets = request.GET.get('scenarios_input_datasets')
    scenarios_output_datasets = request.GET.get('scenarios_output_datasets')

    factsheet = Factsheet.objects.get(id=id)
    factsheet.factsheetData['name'] = name
    factsheet.factsheetData['study_name'] = studyName
    factsheet.factsheetData['acronym'] = acronym
    factsheet.factsheetData['abstract'] = abstract
    factsheet.factsheetData['institution'] = json.loads(institution)
    factsheet.factsheetData['funding_source'] = json.loads(funding_source)
    factsheet.factsheetData['contact_person'] = json.loads(contact_person)
    factsheet.factsheetData['sector_divisions'] = json.loads(sector_divisions)
    factsheet.factsheetData['sectors'] = json.loads(sectors)
    factsheet.factsheetData['scenario_energy_carriers'] = json.loads(scenario_energy_carriers)
    factsheet.factsheetData['scenario_energy_transportation_process'] = json.loads(scenario_energy_transportation_process)
    factsheet.factsheetData['report_title'] = report_title
    factsheet.factsheetData['date_of_publication'] = date_of_publication
    factsheet.factsheetData['doi'] = doi
    factsheet.factsheetData['place_of_publication'] = place_of_publication
    factsheet.factsheetData['link_to_study'] = link_to_study
    factsheet.factsheetData['authors'] = authors
    factsheet.factsheetData['scenarios_name'] = json.loads(scenarios_name)
    factsheet.factsheetData['scenarios_acronym'] = json.loads(scenarios_acronym)
    factsheet.factsheetData['scenarios_abstract'] = json.loads(scenarios_abstract)
    factsheet.factsheetData['scenarios_region'] = json.loads(scenarios_region)
    factsheet.factsheetData['scenarios_interacting_region'] = json.loads(scenarios_interacting_region)
    factsheet.factsheetData['scenarios_years'] = json.loads(scenarios_years)
    factsheet.factsheetData['scenarios_keywords'] = json.loads(scenarios_keywords)
    factsheet.factsheetData['scenarios_input_datasets'] = json.loads(scenarios_input_datasets)
    factsheet.factsheetData['scenarios_output_datasets'] = json.loads(scenarios_output_datasets)

    factsheet.save()
    return JsonResponse('factsheet updated!', safe=False, status=status.HTTP_201_CREATED)

@csrf_exempt
def factsheet_by_name(request, *args, **kwargs):
    name = request.GET.get('name')
    factsheet = Factsheet.objects.get(name=name)
    return JsonResponse(factsheet, safe=False, content_type='application/json')

@csrf_exempt
def factsheet_by_id(request, *args, **kwargs):
    id = request.GET.get('id')
    factsheet = Factsheet.objects.filter(id=id)
    factsheet_json = serializers.serialize('json', factsheet)
    return JsonResponse(factsheet_json, safe=False, content_type='application/json')

@csrf_exempt
def delete_factsheet_by_id(request, *args, **kwargs):
    id = request.GET.get('id')
    factsheet = Factsheet.objects.filter(id=id)
    print(id)
    factsheet.delete()
    return JsonResponse('deleted!', safe=False, content_type='application/json')

@csrf_exempt
def get_all_factsheets(request, *args, **kwargs):
    factsheets = Factsheet.objects.all()
    factsheets_json = serializers.serialize('json', factsheets)
    return JsonResponse(factsheets_json, safe=False, content_type='application/json')
