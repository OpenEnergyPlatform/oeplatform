from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework import status
from .models import Factsheet
import json
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.utils.cache import patch_response_headers


import requests
import rdflib
from rdflib import ConjunctiveGraph, Graph, Literal, RDF, URIRef, BNode
from rdflib.plugins.stores import sparqlstore
from rdflib.namespace import XSD, Namespace
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default

def clean_name(name):
  return name.rstrip().lstrip().replace("-","_").replace(" ","_").replace("%","").replace("Ö","Oe").replace("ö","oe").replace("/","_").replace(":","_").replace("(","_").replace(")","_").replace("ü","ue")

def factsheets_index(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')

@csrf_exempt
def create_factsheet(request, *args, **kwargs):
    OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
    OEO_KG = Namespace("http://openenergy-platform.org/oekg/")
    OBO = Namespace("http://purl.obolibrary.org/obo/")
    DC = Namespace("http://purl.org/dc/terms/")
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    NPG = Namespace("http://ns.nature.com/terms/")
    SCHEMA = Namespace("https://schema.org/")
    OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
    DBO = Namespace("http://dbpedia.org/ontology/")

    query_endpoint = 'http://localhost:3030/ds/query'
    update_endpoint = 'http://localhost:3030/ds/update'
    store = sparqlstore.SPARQLUpdateStore()
    store.open((query_endpoint, update_endpoint))
    g = Graph(store, identifier=default)

    g.bind("OEO", OEO)
    g.bind("OEO_KG", OEO_KG)
    g.bind("OBO", OBO)
    g.bind("DC", DC)
    g.bind("RDFS", RDFS)
    g.bind("NPG", NPG)
    g.bind("SCHEMA", SCHEMA)
    g.bind("OEKG", OEKG)
    g.bind("DBO", DBO)


    request_body = json.loads(request.body)

    name = request_body['name']
    acronym = request_body['acronym']
    study_name = request_body['study_name']
    abstract = request_body['abstract']
    institution = request_body['institution']
    funding_source = request_body['funding_source']
    authors = request_body['authors']
    contact_person = request_body['contact_person']
    sector_divisions = request_body['sector_divisions']
    sectors = request_body['sectors']
    expanded_sectors = request_body['expanded_sectors']
    energy_carriers = request_body['energy_carriers']
    expanded_energy_carriers = request_body['expanded_energy_carriers']
    energy_transformation_processes = request_body['energy_transformation_processes']
    expanded_energy_transformation_processes = request_body['expanded_energy_transformation_processes']
    study_keywords = request_body['study_keywords']
    doi = request_body['doi']
    place_of_publication = request_body['place_of_publication']
    link_to_study = request_body['link_to_study']
    scenarios = request_body['scenarios']
    models = request_body['models']
    frameworks = request_body['frameworks']
    date_of_publication = request_body['date_of_publication']
    report_title = request_body['report_title']

    factsheet_obj = {
        'name': name,
        'acronym': acronym,
        'study_name': study_name,
        'abstract': abstract,
        'institution': json.loads(institution) if institution is not None else [],
        'funding_source': json.loads(funding_source) if funding_source  is not None else [],
        'authors': json.loads(authors) if authors is not None else [],
        'contact_person': json.loads(contact_person) if contact_person is not None else [],
        'sectors': json.loads(sectors) if sectors is not None else [],
        'expanded_sectors': json.loads(expanded_sectors) if expanded_sectors is not None else [],
        'sector_divisions': json.loads(sector_divisions) if sector_divisions is not None else [],
        'energy_transformation_processes': json.loads(energy_transformation_processes) if energy_transformation_processes is not None else [],
        'expanded_energy_transformation_processes': json.loads(expanded_energy_transformation_processes) if expanded_energy_transformation_processes is not None else [],
        'energy_carriers': json.loads(energy_carriers) if energy_carriers is not None else [],
        'expanded_energy_carriers': json.loads(expanded_energy_carriers) if expanded_energy_carriers is not None else [],
        'study_keywords': json.loads(study_keywords) if study_keywords is not None else [],
        'doi': doi,
        'place_of_publication': place_of_publication,
        'link_to_study': link_to_study,
        'scenarios': json.loads(scenarios) if scenarios is not None else [],
        'models': json.loads(models) if models is not None else [],
        'frameworks': json.loads(frameworks) if frameworks is not None else [],
        'date_of_publication': date_of_publication,
        'report_title': report_title,
        }

    fs = Factsheet(factsheetData=factsheet_obj)
    fs.save()

    response = JsonResponse(factsheet_obj, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    study_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(acronym) )
    g.add(( study_URI, RDF.type, OEO.OEO_00000364 ))
    g.add(( study_URI, DC.abstract, Literal(abstract) ))

    institutions = json.loads(institution) if institution is not None else []
    for item in institutions:
        institution_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add(( institution_URI, RDF.type, OEO.OEO_00000238 ))
        g.add(( institution_URI, DC.title, institution_URI ))
        g.add(( study_URI, OEO.OEO_00000510, institution_URI ))

    funding_sources = json.loads(funding_source) if funding_source is not None else []
    for item in funding_sources:
        funding_source_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add(( funding_source_URI, RDF.type, OEO.OEO_00090001 ))
        g.add(( funding_source_URI, DC.title, funding_source_URI ))
        g.add(( study_URI, OEO.RO_0002234, funding_source_URI ))

    return response

@csrf_exempt
def update_factsheet(request, *args, **kwargs):
    OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
    OEO_KG = Namespace("http://openenergy-platform.org/oekg/")
    OBO = Namespace("http://purl.obolibrary.org/obo/")
    DC = Namespace("http://purl.org/dc/terms/")
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    NPG = Namespace("http://ns.nature.com/terms/")
    SCHEMA = Namespace("https://schema.org/")
    OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
    DBO = Namespace("http://dbpedia.org/ontology/")

    query_endpoint = 'http://localhost:3030/ds/query'
    update_endpoint = 'http://localhost:3030/ds/update'
    store = sparqlstore.SPARQLUpdateStore()
    store.open((query_endpoint, update_endpoint))
    g = Graph(store, identifier=default)

    g.bind("OEO", OEO)
    g.bind("OEO_KG", OEO_KG)
    g.bind("OBO", OBO)
    g.bind("DC", DC)
    g.bind("RDFS", RDFS)
    g.bind("NPG", NPG)
    g.bind("SCHEMA", SCHEMA)
    g.bind("OEKG", OEKG)
    g.bind("DBO", DBO)

    request_body = json.loads(request.body)


    fsData = request_body['fsData']
    id = request_body['id']
    name = request_body['name']
    studyName = request_body['study_name']
    acronym = request_body['acronym']
    abstract = request_body['abstract']
    institution = request_body['institution']
    funding_source = request_body['funding_source']
    contact_person = request_body['contact_person']
    sector_divisions = request_body['sector_divisions']
    sectors = request_body['sectors']
    expanded_sectors = request_body['expanded_sectors']
    energy_carriers = request_body['energy_carriers']
    expanded_energy_carriers = request_body['expanded_energy_carriers']
    energy_transformation_processes = request_body['energy_transformation_processes']
    expanded_energy_transformation_processes = request_body['expanded_energy_transformation_processes']
    study_keywords = request_body['study_keywords']
    report_title = request_body['report_title']
    date_of_publication = request_body['date_of_publication']
    doi = request_body['doi']
    place_of_publication = request_body['place_of_publication']
    link_to_study = request_body['link_to_study']
    authors = request_body['authors']
    scenarios = request_body['scenarios']
    models = request_body['models']
    frameworks = request_body['frameworks']


    factsheet = Factsheet.objects.get(id=id)
    factsheet.factsheetData['name'] = name
    factsheet.factsheetData['study_name'] = studyName
    factsheet.factsheetData['acronym'] = acronym
    factsheet.factsheetData['abstract'] = abstract
    factsheet.factsheetData['institution'] = json.loads(institution) if institution is not None else []
    factsheet.factsheetData['funding_source'] = json.loads(funding_source) if funding_source is not None else []
    factsheet.factsheetData['contact_person'] = json.loads(contact_person) if contact_person is not None else []
    factsheet.factsheetData['sector_divisions'] = json.loads(sector_divisions) if sector_divisions is not None else []
    factsheet.factsheetData['sectors'] = json.loads(sectors) if sectors is not None else []
    factsheet.factsheetData['expanded_sectors'] = json.loads(expanded_sectors) if expanded_sectors is not None else []
    factsheet.factsheetData['energy_carriers'] = json.loads(energy_carriers) if energy_carriers is not None else []
    factsheet.factsheetData['expanded_energy_carriers'] = json.loads(expanded_energy_carriers) if expanded_energy_carriers is not None else []
    factsheet.factsheetData['energy_transformation_processes'] = json.loads(energy_transformation_processes) if energy_transformation_processes is not None else []
    factsheet.factsheetData['expanded_energy_transformation_processes'] = json.loads(expanded_energy_transformation_processes) if expanded_energy_transformation_processes is not None else []
    factsheet.factsheetData['study_keywords'] = json.loads(study_keywords) if study_keywords is not None else []
    factsheet.factsheetData['report_title'] = report_title
    factsheet.factsheetData['date_of_publication'] = date_of_publication
    factsheet.factsheetData['doi'] = doi
    factsheet.factsheetData['place_of_publication'] = place_of_publication
    factsheet.factsheetData['link_to_study'] = link_to_study
    factsheet.factsheetData['authors'] = json.loads(authors) if authors is not None else []
    factsheet.factsheetData['scenarios'] = json.loads(scenarios) if scenarios is not None else []
    factsheet.factsheetData['models'] = json.loads(models) if models is not None else []
    factsheet.factsheetData['frameworks'] = json.loads(frameworks) if frameworks is not None else []

    factsheet.save()

    print(fsData)
    response = JsonResponse('factsheet updated!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    old_Study_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(fsData["acronym"]) )
    print(old_Study_URI)
    study_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(acronym) )

    for s, p, o in g.triples((old_Study_URI, RDF.type, OEO.OEO_00000364)):
        g.remove((s, p, o))
    g.add(( study_URI, RDF.type, OEO.OEO_00000364 ))


    for s, p, o in g.triples((old_Study_URI, OEO.OEO_00000510, None)):
        g.remove((s, p, o))

    institutions = json.loads(institution) if institution is not None else []
    for item in institutions:
        institution_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add(( institution_URI, RDF.type, OEO.OEO_00000238 ))
        g.add(( institution_URI, DC.title, institution_URI ))
        g.add(( study_URI, OEO.OEO_00000510, institution_URI ))

    for s, p, o in g.triples((old_Study_URI, OEO.RO_0002234, None)):
        g.remove((s, OEO.RO_0002234, o))

    funding_sources = json.loads(funding_source) if funding_source is not None else []
    for item in funding_sources:
        funding_source_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add(( funding_source_URI, RDF.type, OEO.OEO_00090001 ))
        g.add(( funding_source_URI, DC.title, funding_source_URI ))
        g.add(( study_URI, OEO.RO_0002234, funding_source_URI ))

    abstract_URI =  URIRef("http://purl.org/dc/terms/abstract")
    for s, p, o in g.triples((old_Study_URI, abstract_URI, None)):
        g.remove((s, abstract_URI, o))

    g.add(( study_URI, DC.abstract, Literal(abstract) ))


    return response

@csrf_exempt
def factsheet_by_name(request, *args, **kwargs):
    name = request.GET.get('name')
    factsheet = Factsheet.objects.get(name=name)
    factsheet_json = serializers.serialize('json', factsheet)
    response = JsonResponse(factsheet_json, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def factsheet_by_id(request, *args, **kwargs):
    id = request.GET.get('id')
    factsheet = Factsheet.objects.filter(id=id)
    factsheet_json = serializers.serialize('json', factsheet)
    response = JsonResponse(factsheet_json, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def delete_factsheet_by_id(request, *args, **kwargs):
    id = request.GET.get('id')
    factsheet = Factsheet.objects.filter(id=id)
    factsheet.delete()
    response = JsonResponse('factsheet deleted!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response


@csrf_exempt
def get_all_factsheets(request, *args, **kwargs):
    factsheets = Factsheet.objects.all()
    factsheets_json = serializers.serialize('json', factsheets)
    response = JsonResponse(factsheets_json, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response
