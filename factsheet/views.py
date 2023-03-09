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

import os
from oeplatform.settings import ONTOLOGY_FOLDER
from datetime import date


versions = os.listdir(f"{ONTOLOGY_FOLDER}/{'oeo'}")
version = max((d for d in versions), key=lambda d: [int(x) for x in d.split(".")])
path = f"{ONTOLOGY_FOLDER}/{'oeo'}/{version}"
file = "oeo-full.owl"
Ontology_URI = os.path.join(path, file)
oeo = Graph()
oeo.parse(Ontology_URI)


#query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
#update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

query_endpoint = 'http://localhost:3030/ds/query'
update_endpoint = 'http://localhost:3030/ds/update'

store = sparqlstore.SPARQLUpdateStore()
store.open((query_endpoint, update_endpoint))
oekg = Graph(store, identifier=default)

OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DC = Namespace("http://purl.org/dc/terms/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
NPG = Namespace("http://ns.nature.com/terms/")
SCHEMA = Namespace("https://schema.org/")
OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
DBO = Namespace("http://dbpedia.org/ontology/")

oekg.bind("OEO", OEO)
oekg.bind("OBO", OBO)
oekg.bind("DC", DC)
oekg.bind("RDFS", RDFS)
oekg.bind("NPG", NPG)
oekg.bind("SCHEMA", SCHEMA)
oekg.bind("OEKG", OEKG)
oekg.bind("DBO", DBO)


def clean_name(name):
  return name.rstrip().lstrip().replace("-","_").replace(" ","_").replace("%","").replace("Ö","Oe").replace("ö","oe").replace("/","_").replace(":","_").replace("(","_").replace(")","_").replace("ü","ue")

def undo_clean_name(name):
  return name.rstrip().lstrip().replace("_"," ")

def factsheets_index(request, *args, **kwargs):
    return render(request, 'factsheet/index.html')

@csrf_exempt
def create_factsheet(request, *args, **kwargs):
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

    if (None, DC.acronym, Literal(clean_name(acronym)) ) in oekg:
        response = JsonResponse('Factsheet exists', safe=False, content_type='application/json')
        patch_response_headers(response, cache_timeout=1)
        return response
    else:
        study_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(acronym) )
        oekg.add(( study_URI, RDF.type, OEO.OEO_00000364 ))
        oekg.add((study_URI, RDFS.label, Literal(acronym)))
        oekg.add((study_URI, DC.acronym, Literal(acronym)))
        oekg.add((study_URI, OEKG["full_name"], Literal(study_name)))
        oekg.add(( study_URI, DC.abstract, Literal(abstract) ))
        oekg.add(( study_URI, OEKG["report_title"], Literal(report_title) ))
        oekg.add(( study_URI, OEKG["date_of_publication"], Literal(date_of_publication) ))
        oekg.add(( study_URI, OEKG["place_of_publication"], Literal(place_of_publication) ))
        oekg.add(( study_URI, OEKG["link_to_study"], Literal(link_to_study) ))
        oekg.add(( study_URI, OEKG["doi"], Literal(doi) ))


        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add(( institution_URI, RDF.type, OEO.OEO_00000238 ))
            oekg.add(( institution_URI, DC.title, Literal(item['name']) ))
            oekg.add(( study_URI, OEO.OEO_00000510, institution_URI ))

        funding_sources = json.loads(funding_source) if funding_source is not None else []
        for item in funding_sources:
            funding_source_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add(( funding_source_URI, RDF.type, OEO.OEO_00090001 ))
            oekg.add(( funding_source_URI, DC.title,  Literal(item['name'])))
            oekg.add(( study_URI, OEO.RO_0002234, funding_source_URI ))

        contact_persons = json.loads(contact_person) if contact_person is not None else []
        for item in contact_persons:
            contact_person_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((contact_person_URI, RDF.type, OEO.OEO_00000107))
            oekg.add((contact_person_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OEO.OEO_0000050, contact_person_URI))

        _sector_divisions = json.loads(sector_divisions) if sector_divisions is not None else []
        for item in _sector_divisions:
            sector_divisions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((sector_divisions_URI, RDF.type, OEO.OEO_00000368))
            oekg.add((sector_divisions_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OEO["based_on_sector_division"], sector_divisions_URI))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            oekg.add((sector_URI, RDF.type, OEO.OEO_00000367))
            oekg.add((sector_URI, RDFS.label, Literal(item)))
            oekg.add((study_URI, OEO["covers_sector"], sector_URI))

        _energy_carriers = json.loads(energy_carriers) if energy_carriers is not None else []
        for item in _energy_carriers:
            energy_carriers_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            oekg.add((energy_carriers_URI, RDF.type, OEO.OEO_00020039))
            oekg.add((energy_carriers_URI, RDFS.label, Literal(item)))
            oekg.add((study_URI, OEO["covers_energy_carrier"], energy_carriers_URI))

        _energy_transformation_processes = json.loads(energy_transformation_processes) if energy_transformation_processes is not None else []
        for item in _energy_transformation_processes:
            energy_transformation_processes_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            oekg.add((energy_transformation_processes_URI, RDF.type, OEO.OEO_00020003))
            oekg.add((energy_transformation_processes_URI, RDFS.label, Literal(item)))
            oekg.add((study_URI, OEO["covers_transformation_processes"], energy_transformation_processes_URI))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            model_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((model_URI, RDF.type, OEO.OEO_00000274))
            oekg.add((model_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OEO["has_participant"], model_URI))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            framework_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((framework_URI, RDF.type, OEO.OEO_00000172))
            oekg.add((framework_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OEO["has_participant"], framework_URI))

        _authors = json.loads(authors) if authors is not None else []
        for item in _authors:
            author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((author_URI, RDF.type, OEO.OEO_00000064))
            oekg.add((author_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OEO.OEO_00000506, author_URI))

        response = JsonResponse('Factsheet saved', safe=False, content_type='application/json')
        patch_response_headers(response, cache_timeout=1)
        return response

@csrf_exempt
def update_factsheet(request, *args, **kwargs):
    request_body = json.loads(request.body)
    print(request_body)
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
    report_doi = request_body['report_doi']
    place_of_publication = request_body['place_of_publication']
    link_to_study = request_body['link_to_study']
    authors = request_body['authors']
    scenarios = request_body['scenarios']
    models = request_body['models']
    frameworks = request_body['frameworks']

    update_factsheet = "No"
    if (fsData["acronym"] != acronym):
        if (None, DC.acronym, Literal(clean_name(acronym)) ) in oekg:
            update_factsheet = "Duplicate"
        update_factsheet = "Yes"
    else:
        update_factsheet = "Yes"


    if update_factsheet ==  "Duplicate":
        response = JsonResponse('Factsheet exists', safe=False, content_type='application/json')
        patch_response_headers(response, cache_timeout=1)
        return response
        
    if update_factsheet ==  "Yes":
        old_Study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(fsData["acronym"]))
        study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(acronym))

        if old_Study_URI != study_URI:
            for s, p, o in oekg.triples(( old_Study_URI, None, None )):
                oekg.remove((s, p, o))

            oekg.add((study_URI, RDF.type, OEO.OEO_00000364 ))
            oekg.add((study_URI, RDFS.label, Literal(acronym)))
            oekg.add((study_URI, OEKG["full_name"], Literal(studyName)))
            oekg.add(( study_URI, OEKG["report_title"], Literal(report_title) ))
            oekg.add(( study_URI, OEKG["date_of_publication"], Literal(date_of_publication) ))
            oekg.add(( study_URI, OEKG["place_of_publication"], Literal(place_of_publication) ))
            oekg.add(( study_URI, OEKG["link_to_study"], Literal(link_to_study) ))
            oekg.add(( study_URI, OEKG["doi"], Literal(doi) ))
            print(doi)

        for s, p, o in oekg.triples((study_URI, OEO.OEO_00000510, None)):
            oekg.remove((s, p, o))
        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add(( institution_URI, RDF.type, OEO.OEO_00000238 ))
            oekg.add(( institution_URI, RDFS.label, Literal(item['name'])) )
            oekg.add(( study_URI, OEO.OEO_00000510, institution_URI ))

        for s, p, o in oekg.triples((study_URI, OEO.RO_0002234, None)):
            oekg.remove((s, p, o))
        funding_sources = json.loads(funding_source) if funding_source is not None else []
        for item in funding_sources:
            funding_source_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add(( funding_source_URI, RDF.type, OEO.OEO_00090001 ))
            oekg.add(( funding_source_URI, RDFS.label, Literal(item['name']) ))
            oekg.add(( study_URI, OEO.RO_0002234, funding_source_URI ))

        for s, p, o in oekg.triples((study_URI, DC.abstract, None)):
            oekg.remove((s, p, o))
        oekg.add(( study_URI, DC.abstract, Literal(abstract) ))

        for s, p, o in oekg.triples((study_URI, OEO.OEO_0000050, None)):
            oekg.remove((s, p, o))
        contact_persons = json.loads(contact_person) if contact_person is not None else []
        for item in contact_persons:
            contact_person_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((contact_person_URI, RDF.type, OEO.OEO_00000107))
            oekg.add((contact_person_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OEO.OEO_00000508, contact_person_URI))

        for s, p, o in oekg.triples((old_Study_URI, OEO["based_on_sector_division"], None)):
            oekg.remove((s, p, o))
        _sector_divisions = json.loads(sector_divisions) if sector_divisions is not None else []
        for item in _sector_divisions:
            sector_divisions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((sector_divisions_URI, RDF.type, OEO.OEO_00000368))
            oekg.add((sector_divisions_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OEO["based_on_sector_division"], sector_divisions_URI))

        for s, p, o in oekg.triples((old_Study_URI, OEO["covers_sector"], None)):
            oekg.remove((s, p, o))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            oekg.add((sector_URI, RDF.type, OEO.OEO_00000367))
            oekg.add((sector_URI,RDFS.label, Literal(item)))
            oekg.add((study_URI, OEO["covers_sector"], sector_URI))

        for s, p, o in oekg.triples((old_Study_URI, OEO["covers_energy_carrier"], None)):
            oekg.remove((s, p, o))

        _energy_carriers = json.loads(energy_carriers) if energy_carriers is not None else []
        for item in _energy_carriers:
            energy_carriers_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            oekg.add((energy_carriers_URI, RDF.type, OEO.OEO_00020039))
            oekg.add((energy_carriers_URI, RDFS.label, Literal(item)))
            oekg.add((study_URI, OEO["covers_energy_carrier"], energy_carriers_URI))

        for s, p, o in oekg.triples((old_Study_URI, OEO["covers_transformation_processes"], None)):
            oekg.remove((s, p, o))

        _energy_transformation_processes = json.loads(
            energy_transformation_processes) if energy_transformation_processes is not None else []
        for item in _energy_transformation_processes:
            energy_transformation_processes_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            oekg.add((energy_transformation_processes_URI, RDF.type, OEO.OEO_00020003))
            oekg.add((energy_transformation_processes_URI, RDFS.label, Literal(item)))
            oekg.add((study_URI, OEO["covers_transformation_processes"], energy_transformation_processes_URI))

        for s, p, o in oekg.triples((old_Study_URI, OEO["has_participant"], None)):
            oekg.remove((s, p, o))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            model_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((model_URI, RDF.type, OEO.OEO_00000274))
            oekg.add((model_URI, RDFS.label, Literal(clean_name(item['name']))))
            oekg.add((study_URI, OEO["has_participant"], model_URI))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            framework_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((framework_URI, RDF.type, OEO.OEO_00000172))
            oekg.add((framework_URI, RDFS.label, Literal(clean_name(item['name']))))
            oekg.add((study_URI, OEO["has_participant"], framework_URI))

        for s, p, o in oekg.triples((old_Study_URI, OEO.OEO_00000506, None)):
            oekg.remove((s, p, o))

        _authors = json.loads(authors) if authors is not None else []
        for item in _authors:
            author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((author_URI, RDF.type, OEO.OEO_00000064))
            oekg.add((author_URI, RDFS.label, Literal(clean_name(item['name']))))
            oekg.add((study_URI, OEO.OEO_00000506, author_URI))

        response = JsonResponse('factsheet updated!', safe=False, content_type='application/json')
        patch_response_headers(response, cache_timeout=1)
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
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(id))

    factsheet = {}
    for s, p, o in oekg.triples(( study_URI, RDFS.label, None )):
        factsheet['acronym'] = o

    for s, p, o in oekg.triples(( study_URI, OEKG.full_name, None )):
        factsheet['study_name'] = o

    for s, p, o in oekg.triples(( study_URI, DC.abstract, None )):
        factsheet['abstract'] = o

    for s, p, o in oekg.triples(( study_URI, OEKG["report_title"] , None )):
        factsheet['report_title'] = o

    for s, p, o in oekg.triples(( study_URI, OEKG["date_of_publication"] , None )):
        factsheet['date_of_publication'] = o

    for s, p, o in oekg.triples(( study_URI, OEKG["place_of_publication"] , None )):
        factsheet['place_of_publication'] = o

    for s, p, o in oekg.triples(( study_URI, OEKG["link_to_study"] , None )):
        factsheet['link_to_study'] = o
    
    for s, p, o in oekg.triples(( study_URI, OEKG["doi"] , None )):
        factsheet['doi'] = o

    factsheet['funding_sources'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.RO_0002234, None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['funding_sources'].append({ 'id': clean_name(label), 'name': clean_name(label) })
        
    factsheet['institution'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000510, None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['institution'].append({ 'id': clean_name(label), 'name': clean_name(label) })

    factsheet['contact_person'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000508, None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['contact_person'].append({ 'id': clean_name(label), 'name': clean_name(label) })

    factsheet['sector_divisions'] = []
    for s, p, o in oekg.triples(( study_URI, OEO["based_on_sector_division"], None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['sector_divisions'].append({ 'id': label, 'name': label })

    factsheet['sectors'] = []
    for s, p, o in oekg.triples(( study_URI, OEO["covers_sector"], None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['sectors'].append(label)

    factsheet['energy_carriers'] = []
    for s, p, o in oekg.triples(( study_URI, OEO["covers_energy_carrier"], None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['energy_carriers'].append(label)

    factsheet['energy_transformation_processes'] = []
    for s, p, o in oekg.triples(( study_URI, OEO["covers_transformation_processes"], None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['energy_transformation_processes'].append(label)

    factsheet['authors'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000506, None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['authors'].append({ 'id': label, 'name': label })

    response = JsonResponse(factsheet, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    return response

@csrf_exempt
def delete_factsheet_by_id(request, *args, **kwargs):
    id = request.GET.get('id')
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(id))
    oekg.remove((study_URI, None, None)) 
    response = JsonResponse('factsheet removed!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def get_entities_by_type(request, *args, **kwargs):
    entity_type = request.GET.get('entity_type')
    entity_URI = URIRef("http://openenergy-platform.org/ontology/oeo/" + entity_type )
    print(entity_URI)

    entities = []
    for s, p, o in oekg.triples(( None, RDF.type, entity_URI )):
        sl = oekg.value(s, RDFS.label)
        entities.append(sl)

    response = JsonResponse(entities, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response


@csrf_exempt
def add_entities(request, *args, **kwargs):
    request_body = json.loads(request.body)
    entity_type = request_body['entity_type']
    entity_label = request_body['entity_label']
    entity_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(entity_label) )

    oekg.add((entity_URI, RDF.type, OEO[entity_type]))
    oekg.add((entity_URI, RDFS.label, Literal(entity_label)))

    response = JsonResponse('A new entity added!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def add_a_fact(request, *args, **kwargs):
    request_body = json.loads(request.body)
    _subject = request_body['subject']
    _predicate = request_body['predicate']
    _object = request_body['object']

    _subject_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(_subject) )
    _predicate_URI = URIRef("http://openenergy-platform.org/ontology/oeo/" + clean_name(_predicate) )
    _object_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(_object) )

    oekg.add((_subject_URI, _predicate_URI, _object_URI))

    response = JsonResponse('A new fact added!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def delete_entities(request, *args, **kwargs):
    # request_body = json.loads(request.body)
    # entity_type = request_body['entity_type']
    # entity_label = request_body['entity_label']

    #oekg.remove((None, None, None)) 

    entity_type = request.GET.get('entity_type')
    entity_label = request.GET.get('entity_label')

    entity_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + entity_type )
    entity_Label = URIRef("http://openenergy-platform.org/ontology/oekg/" + (entity_label) )

    oekg.remove((entity_Label, None, None)) 
    oekg.remove((None, None, entity_Label)) 
    response = JsonResponse('entity removed!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def update_an_entity(request, *args, **kwargs):
    request_body = json.loads(request.body)
    entity_type =  request_body['entity_type']
    entity_label =  request_body['entity_label']
    new_entity_label =  request_body['new_entity_label']

    entity_type_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + entity_type )
    entity_Label_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(entity_label) )
    new_entity_label_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(new_entity_label))

    oekg.add((new_entity_label_URI, RDF.type, OEO[entity_type]))
    oekg.add((new_entity_label_URI, RDFS.label, Literal(new_entity_label)))

    entity_edit_history = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(new_entity_label) + "/edit_history")
    oekg.add((entity_edit_history, RDFS.label, Literal(new_entity_label)))
    oekg.add((entity_edit_history, RDF.type, OEKG["edit_history"]))
    oekg.add((entity_edit_history, OEKG["prev"], Literal(entity_label) ))
    oekg.add((entity_edit_history, OEKG["next"], Literal(new_entity_label) ))
    oekg.add((entity_edit_history, OEKG["date"], Literal(date.today()) ))

    for s, p, o in oekg.triples((None, None, entity_Label_URI)):
        oekg.add((s, p, new_entity_label_URI))
        oekg.remove((s, p, o))
    oekg.remove((entity_Label_URI, None, None)) 

    response = JsonResponse('entity updated!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def get_all_factsheets(request, *args, **kwargs):
    all_factsheets = []
    for s, p, o in oekg.triples(( None, RDF.type, OEO.OEO_00000364 )):
        element = {}
        element['acronym'] =  oekg.value(s, RDFS.label) 
        element['study_name'] = oekg.value(s, OEKG.full_name) 
        element['abstract'] = oekg.value(s, DC.abstract) 
        study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(oekg.value(s, RDFS.label) ))
        element['institution'] = []
        for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000510, None )):
            label = oekg.value(o, RDFS.label)
            if label != None:
                element['institution'].append(label)
        all_factsheets.append(element)

    response = JsonResponse(all_factsheets, safe=False, content_type='application/json') 
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def get_all_factsheets_as_turtle(request, *args, **kwargs):
    all_factsheets_as_turtle = oekg.serialize(format="ttl")
    response = JsonResponse(all_factsheets_as_turtle, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    return response

@csrf_exempt
def get_all_factsheets_as_json_ld(request, *args, **kwargs):
    all_factsheets_as_turtle = oekg.serialize(format="json-ld")
    response = JsonResponse(all_factsheets_as_turtle, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    return response


@csrf_exempt
def populate_factsheets_elements(request, *args, **kwargs):
    elements = {}

    energy_transformation_processes = []
    for s, p, o in oeo.triples(( None, RDFS.subClassOf, OEO.OEO_00020003 )):
        sl = oeo.value(s, RDFS.label)
        parent = {
            'value': sl,
            'label': sl
        }
        children = []
        for s1, p, o in oeo.triples(( None, RDFS.subClassOf, s )):
            sl1 = oeo.value(s1, RDFS.label)
            
            children2 = []
            for s2, p, o in oeo.triples(( None, RDFS.subClassOf, s1 )):
                sl2 = oeo.value(s2, RDFS.label)

                children2.append({
                    'value': sl2,
                    'label': sl2
                })

            if children2 != []:
                children.append({
                'value': sl1,
                'label': sl1,
                'children': children2
                })
            else:
                children.append({
                'value': sl1,
                'label': sl1
                })

        if children != []:
            parent['children'] = children

        energy_transformation_processes.append(parent)
        elements['energy_transformation_processes'] = energy_transformation_processes


    energy_carriers = []
    for s, p, o in oeo.triples(( None, RDFS.subClassOf, OEO.OEO_00020039 )):
        sl = oeo.value(s, RDFS.label)
        parent = {
            'value': sl,
            'label': sl
        }
        children = []
        for s1, p, o in oeo.triples(( None, RDFS.subClassOf, s )):
            sl1 = oeo.value(s1, RDFS.label)
            
            children2 = []
            for s2, p, o in oeo.triples(( None, RDFS.subClassOf, s1 )):
                sl2 = oeo.value(s2, RDFS.label)

                children2.append({
                    'value': sl2,
                    'label': sl2
                })

            if children2 != []:
                children.append({
                'value': sl1,
                'label': sl1,
                'children': children2
                })
            else:
                children.append({
                'value': sl1,
                'label': sl1
                })

        if children != []:
            parent['children'] = children

        energy_carriers.append(parent)
        elements['energy_carriers'] = energy_carriers


    response = JsonResponse(elements, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    return response

    
