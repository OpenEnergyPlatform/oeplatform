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
    doi = request.GET.get('doi')
    place_of_publication = request.GET.get('place_of_publication')
    link_to_study = request.GET.get('link_to_study')
    scenarios_info = request.GET.get('scenarios_info')

    factsheet_obj = {
        'name': name,
        'acronym': acronym,
        'study_name': study_name,
        'abstract': abstract,
        'institution': json.loads(institution),
        'funding_source': funding_source,
        'authors': authors,
        'contact_person': contact_person,
        'doi': doi,
        'place_of_publication': place_of_publication,
        'link_to_study': link_to_study,
        'scenarios_info': json.loads(scenarios_info),
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
    report_title = request.GET.get('report_title')
    date_of_publication = request.GET.get('date_of_publication')
    doi = request.GET.get('doi')
    place_of_publication = request.GET.get('place_of_publication')
    link_to_study = request.GET.get('link_to_study')
    authors = request.GET.get('authors')
    scenarios_info = request.GET.get('scenarios_info')

    factsheet = Factsheet.objects.get(id=id)
    factsheet.factsheetData['name'] = name
    factsheet.factsheetData['study_name'] = studyName
    factsheet.factsheetData['acronym'] = acronym
    factsheet.factsheetData['abstract'] = abstract
    factsheet.factsheetData['institution'] = json.loads(institution)
    factsheet.factsheetData['funding_source'] = json.loads(funding_source)
    factsheet.factsheetData['contact_person'] = json.loads(contact_person)
    factsheet.factsheetData['report_title'] = report_title
    factsheet.factsheetData['date_of_publication'] = date_of_publication
    factsheet.factsheetData['doi'] = doi
    factsheet.factsheetData['place_of_publication'] = place_of_publication
    factsheet.factsheetData['link_to_study'] = link_to_study
    factsheet.factsheetData['authors'] = authors
    factsheet.factsheetData['scenarios_info'] = json.loads(scenarios_info)

    factsheet.save()

    return JsonResponse('updated', safe=False, status=status.HTTP_201_CREATED)


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
