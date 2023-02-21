from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework import status
from .models import Factsheet
import json
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.utils.cache import patch_response_headers

import uuid
import requests
import rdflib
from rdflib import ConjunctiveGraph, Graph, Literal, RDF, URIRef, BNode
from rdflib.plugins.stores import sparqlstore
from rdflib.namespace import XSD, Namespace
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default

def clean_name(name):
  return name.rstrip().lstrip().replace("-","_").replace(" ","_").replace("%","").replace("Ö","Oe").replace("ö","oe").replace("/","_").replace(":","_").replace("(","_").replace(")","_").replace("ü","ue")

def undo_clean_name(name):
  return name.rstrip().lstrip().replace("_"," ")

def factsheets_index(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')

@csrf_exempt
def create_factsheet(request, *args, **kwargs):
    OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
    OBO = Namespace("http://purl.obolibrary.org/obo/")
    DC = Namespace("http://purl.org/dc/terms/")
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    NPG = Namespace("http://ns.nature.com/terms/")
    SCHEMA = Namespace("https://schema.org/")
    OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
    DBO = Namespace("http://dbpedia.org/ontology/")

    #query_endpoint = 'http://localhost:3030/ds/query'
    #update_endpoint = 'http://localhost:3030/ds/update'

    query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
    update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

    store = sparqlstore.SPARQLUpdateStore()
    store.open((query_endpoint, update_endpoint))
    g = Graph(store, identifier=default)

    g.bind("OEO", OEO)
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

    """ factsheet_obj = {
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
        } """

    
    if (None, DC.acronym, Literal(clean_name(acronym)) ) in g:
        response = JsonResponse('Factsheet exists', safe=False, content_type='application/json')
        patch_response_headers(response, cache_timeout=1)
        return response
    else:
        study_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(acronym) )
        g.add(( study_URI, RDF.type, OEO.OEO_00000364 ))
        g.add((study_URI, RDFS.label, Literal(clean_name(acronym))))
        g.add((study_URI, DC.acronym, Literal(clean_name(acronym))))
        g.add((study_URI, OEKG["full_name"], Literal(clean_name(study_name))))
        g.add(( study_URI, DC.abstract, Literal(abstract) ))

        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add(( institution_URI, RDF.type, OEO.OEO_00000238 ))
            g.add(( institution_URI, DC.title, Literal(clean_name(item['name']) )))
            g.add(( study_URI, OEKG["conducted_by"], institution_URI ))

        funding_sources = json.loads(funding_source) if funding_source is not None else []
        for item in funding_sources:
            funding_source_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add(( funding_source_URI, RDF.type, OEO.OEO_00090001 ))
            g.add(( funding_source_URI, DC.title,  Literal(clean_name(item['name']) )))
            g.add(( study_URI, OEO.RO_0002234, funding_source_URI ))

        contact_persons = json.loads(contact_person) if contact_person is not None else []
        for item in contact_persons:
            contact_person_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((contact_person_URI, RDF.type, OEO.OEO_00000107))
            g.add((contact_person_URI, DC.title, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO.OEO_0000050, contact_person_URI))

        _sector_divisions = json.loads(sector_divisions) if sector_divisions is not None else []
        for item in _sector_divisions:
            sector_divisions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((sector_divisions_URI, RDF.type, OEO.OEO_00000368))
            g.add((sector_divisions_URI, DC.name, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO["based_on_sector_division"], contact_person_URI))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            g.add((sector_URI, RDF.type, OEO.OEO_00000367))
            g.add((sector_URI, DC.name, Literal(clean_name(item))))
            g.add((study_URI, OEO["covers_sector"], sector_URI))

        _energy_carriers = json.loads(energy_carriers) if energy_carriers is not None else []
        for item in _energy_carriers:
            energy_carriers_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            g.add((energy_carriers_URI, RDF.type, OEO.OEO_00020039))
            g.add((energy_carriers_URI, DC.name, Literal(clean_name(item))))
            g.add((study_URI, OEO["covers_energy_carrier"], energy_carriers_URI))

        _energy_transformation_processes = json.loads(energy_transformation_processes) if energy_transformation_processes is not None else []
        for item in _energy_transformation_processes:
            energy_transformation_processes_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            g.add((energy_transformation_processes_URI, RDF.type, OEO.OEO_00020003))
            g.add((energy_transformation_processes_URI, DC.name, Literal(clean_name(item))))
            g.add((study_URI, OEO["covers_transformation_processes"], energy_transformation_processes_URI))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            model_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((model_URI, RDF.type, OEO.OEO_00000274))
            g.add((model_URI, DC.name, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO["has_participant"], model_URI))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            framework_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((framework_URI, RDF.type, OEO.OEO_00000172))
            g.add((framework_URI, DC.name, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO["has_participant"], framework_URI))

        _authors = json.loads(authors) if authors is not None else []
        for item in _authors:
            author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((author_URI, RDF.type, OEO.OEO_00000064))
            g.add((author_URI, DC.name, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO.OEO_00000506, author_URI))


        response = JsonResponse('Factsheet saved', safe=False, content_type='application/json')
        patch_response_headers(response, cache_timeout=1)
        return response

@csrf_exempt
def update_factsheet(request, *args, **kwargs):
    OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
    OBO = Namespace("http://purl.obolibrary.org/obo/")
    DC = Namespace("http://purl.org/dc/terms/")
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    NPG = Namespace("http://ns.nature.com/terms/")
    SCHEMA = Namespace("https://schema.org/")
    OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
    DBO = Namespace("http://dbpedia.org/ontology/")

    #query_endpoint = 'http://localhost:3030/ds/query'
    #update_endpoint = 'http://localhost:3030/ds/update'

    query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
    update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

    store = sparqlstore.SPARQLUpdateStore()
    store.open((query_endpoint, update_endpoint))
    g = Graph(store, identifier=default)

    g.bind("OEO", OEO)
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

    """  
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

    factsheet.save() """

    response = JsonResponse('factsheet updated!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    old_Study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(fsData["acronym"]))
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(acronym))

    for s, p, o in g.triples(( old_Study_URI, None, None )):
        g.remove((s, p, o))
        g.add((study_URI, p, o))

    g.remove((study_URI, RDFS.label, None))
    g.add((study_URI, RDFS.label, Literal(clean_name(acronym))))

    for s, p, o in g.triples((old_Study_URI, OEO.OEO_00000510, None)):
        g.remove((s, p, o))

    for s, p, o in g.triples((old_Study_URI, OEKG["full_name"], None)):
        g.remove((s, p, o))
    g.add((study_URI, OEKG["full_name"], Literal(clean_name(studyName))))

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
        g.remove((s, p, o))
    g.add(( study_URI, DC.abstract, Literal(abstract) ))

    for s, p, o in g.triples((old_Study_URI, OEO.OEO_0000050, None)):
        g.remove((s, p, o))

    contact_persons = json.loads(contact_person) if contact_person is not None else []
    for item in contact_persons:
        contact_person_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((contact_person_URI, RDF.type, OEO.OEO_00000107))
        g.add((contact_person_URI, DC.title, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO.OEO_0000050, contact_person_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["based_on_sector_division"], None)):
        g.remove((s, p, o))

    _sector_divisions = json.loads(sector_divisions) if sector_divisions is not None else []
    for item in _sector_divisions:
        sector_divisions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((sector_divisions_URI, RDF.type, OEO.OEO_00000368))
        g.add((sector_divisions_URI, DC.name, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO["based_on_sector_division"], contact_person_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["covers_sector"], None)):
        g.remove((s, p, o))

    _sectors = json.loads(sectors) if sectors is not None else []
    for item in _sectors:
        sector_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
        g.add((sector_URI, RDF.type, OEO.OEO_00000367))
        g.add((sector_URI, DC.name, Literal(clean_name(item))))
        g.add((study_URI, OEO["covers_sector"], sector_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["covers_energy_carrier"], None)):
        g.remove((s, p, o))

    _energy_carriers = json.loads(energy_carriers) if energy_carriers is not None else []
    for item in _energy_carriers:
        energy_carriers_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
        g.add((energy_carriers_URI, RDF.type, OEO.OEO_00020039))
        g.add((energy_carriers_URI, DC.name, Literal(clean_name(item))))
        g.add((study_URI, OEO["covers_energy_carrier"], energy_carriers_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["covers_transformation_processes"], None)):
        g.remove((s, p, o))

    _energy_transformation_processes = json.loads(
        energy_transformation_processes) if energy_transformation_processes is not None else []
    for item in _energy_transformation_processes:
        energy_transformation_processes_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
        g.add((energy_transformation_processes_URI, RDF.type, OEO.OEO_00020003))
        g.add((energy_transformation_processes_URI, DC.name, Literal(clean_name(item))))
        g.add((study_URI, OEO["covers_transformation_processes"], energy_transformation_processes_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["has_participant"], None)):
        g.remove((s, p, o))

    _models = json.loads(models) if models is not None else []
    for item in _models:
        model_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((model_URI, RDF.type, OEO.OEO_00000274))
        g.add((model_URI, DC.name, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO["has_participant"], model_URI))

    _frameworks = json.loads(frameworks) if frameworks is not None else []
    for item in _frameworks:
        framework_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((framework_URI, RDF.type, OEO.OEO_00000172))
        g.add((framework_URI, DC.name, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO["has_participant"], framework_URI))

    for s, p, o in g.triples((old_Study_URI, OEO.OEO_00000506, None)):
        g.remove((s, p, o))

    _authors = json.loads(authors) if authors is not None else []
    for item in _authors:
        author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((author_URI, RDF.type, OEO.OEO_00000064))
        g.add((author_URI, DC.name, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO.OEO_00000506, author_URI))

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
    """ id = request.GET.get('id')
    factsheet = Factsheet.objects.filter(id=id)
    factsheet_json = serializers.serialize('json', factsheet)
    response = JsonResponse(factsheet_json, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response """

    query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
    update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

    store = sparqlstore.SPARQLUpdateStore()
    store.open((query_endpoint, update_endpoint))
    g = Graph(store, identifier=default)

    id = request.GET.get('id')
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(id))

    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
    DC = Namespace("http://purl.org/dc/terms/")
    OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")

    factsheet = {}
    for s, p, o in g.triples(( study_URI, RDFS.label, None )):
        factsheet['acronym'] = o

    for s, p, o in g.triples(( study_URI, OEKG.full_name, None )):
        factsheet['study_name'] = o

    for s, p, o in g.triples(( study_URI, DC.abstract, None )):
        factsheet['abstract'] = o

    factsheet['funding_sources'] = []
    for s, p, o in g.triples(( study_URI, OEO.RO_0002234, None )):
        v = undo_clean_name(o.split('/')[-1])
        factsheet['funding_sources'].append({ 'id': v, 'name': v })
        
    factsheet['institution'] = []
    for s, p, o in g.triples(( study_URI, OEO.OEO_00000510, None )):
        v = undo_clean_name(o.split('/')[-1])
        factsheet['institution'].append({ 'id': v, 'name': v })

    response = JsonResponse(factsheet, safe=False, content_type='application/json')
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
    """  factsheets = Factsheet.objects.all()
    factsheets_json = serializers.serialize('json', factsheets)
    response = JsonResponse(factsheets_json, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response """

    query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
    update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

    store = sparqlstore.SPARQLUpdateStore()
    store.open((query_endpoint, update_endpoint))
    g = Graph(store, identifier=default)

    OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
    OBO = Namespace("http://purl.obolibrary.org/obo/")
    DC = Namespace("http://purl.org/dc/terms/")
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    NPG = Namespace("http://ns.nature.com/terms/")
    SCHEMA = Namespace("https://schema.org/")
    OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
    DBO = Namespace("http://dbpedia.org/ontology/")

    g.bind("OEO", OEO)
    g.bind("OBO", OBO)
    g.bind("DC", DC)
    g.bind("RDFS", RDFS)
    g.bind("NPG", NPG)
    g.bind("SCHEMA", SCHEMA)
    g.bind("OEKG", OEKG)
    g.bind("DBO", DBO)
 
    all_factsheets = []
    for s1, p1, o1 in g.triples(( None, RDF.type, OEO.OEO_00000364 )):
        element = {}
        element['acronym'] =  s1.split('/')[-1]
        for s2, p2, o2 in g.triples(( s1, OEKG.full_name, None )):
            element['study_name'] = o2
        for s3, p4, o3 in g.triples(( s1, DC.abstract, None )):
            element['abstract'] = o3
        all_factsheets.append(element)

    response = JsonResponse(all_factsheets, safe=False, content_type='application/json') 
    patch_response_headers(response, cache_timeout=1)

    return response

@csrf_exempt
def get_all_factsheets_as_turtle(request, *args, **kwargs):
    query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
    update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

    store = sparqlstore.SPARQLUpdateStore()
    store.open((query_endpoint, update_endpoint))
    g = Graph(store, identifier=default)

    all_factsheets_as_turtle = g.serialize(format="ttl")
    response = JsonResponse(all_factsheets_as_turtle, safe=False, content_type='application/json')

    
    patch_response_headers(response, cache_timeout=1)

    return response

@csrf_exempt
def get_all_factsheets_as_json_ld(request, *args, **kwargs):
    query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
    update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

    store = sparqlstore.SPARQLUpdateStore()
    store.open((query_endpoint, update_endpoint))
    g = Graph(store, identifier=default)

    all_factsheets_as_turtle = g.serialize(format="json-ld")
    response = JsonResponse(all_factsheets_as_turtle, safe=False, content_type='application/json')

    
    patch_response_headers(response, cache_timeout=1)

    return response

    
