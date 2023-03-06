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



versions = os.listdir(f"{ONTOLOGY_FOLDER}{'oeo'}")
version = max((d for d in versions), key=lambda d: [int(x) for x in d.split(".")])
path = f"{ONTOLOGY_FOLDER}{'oeo'}/{version}"
file = "oeo-full.owl"
Ontology_URI = os.path.join(path, file)
oeo = Graph()
oeo.parse(Ontology_URI)


query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

#query_endpoint = 'http://localhost:3030/ds/query'
#update_endpoint = 'http://localhost:3030/ds/update'

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
            g.add(( study_URI, OEO.OEO_00000510, institution_URI ))

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
            g.add((contact_person_URI, RDFS.label, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO.OEO_0000050, contact_person_URI))

        _sector_divisions = json.loads(sector_divisions) if sector_divisions is not None else []
        for item in _sector_divisions:
            sector_divisions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((sector_divisions_URI, RDF.type, OEO.OEO_00000368))
            g.add((sector_divisions_URI, RDFS.label, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO["based_on_sector_division"], contact_person_URI))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            g.add((sector_URI, RDF.type, OEO.OEO_00000367))
            g.add((sector_URI, RDFS.label, Literal(clean_name(item))))
            g.add((study_URI, OEO["covers_sector"], sector_URI))

        _energy_carriers = json.loads(energy_carriers) if energy_carriers is not None else []
        for item in _energy_carriers:
            energy_carriers_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            g.add((energy_carriers_URI, RDF.type, OEO.OEO_00020039))
            g.add((energy_carriers_URI, RDFS.label, Literal(clean_name(item))))
            g.add((study_URI, OEO["covers_energy_carrier"], energy_carriers_URI))

        _energy_transformation_processes = json.loads(energy_transformation_processes) if energy_transformation_processes is not None else []
        for item in _energy_transformation_processes:
            energy_transformation_processes_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            g.add((energy_transformation_processes_URI, RDF.type, OEO.OEO_00020003))
            g.add((energy_transformation_processes_URI, RDFS.label, Literal(clean_name(item))))
            g.add((study_URI, OEO["covers_transformation_processes"], energy_transformation_processes_URI))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            model_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((model_URI, RDF.type, OEO.OEO_00000274))
            g.add((model_URI, RDFS.label, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO["has_participant"], model_URI))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            framework_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((framework_URI, RDF.type, OEO.OEO_00000172))
            g.add((framework_URI, RDFS.label, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO["has_participant"], framework_URI))

        _authors = json.loads(authors) if authors is not None else []
        for item in _authors:
            author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            g.add((author_URI, RDF.type, OEO.OEO_00000064))
            g.add((author_URI, RDFS.label, Literal(clean_name(item['name']))))
            g.add((study_URI, OEO.OEO_00000506, author_URI))

        response = JsonResponse('Factsheet saved', safe=False, content_type='application/json')
        patch_response_headers(response, cache_timeout=1)
        return response

@csrf_exempt
def update_factsheet(request, *args, **kwargs):
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
        g.add(( institution_URI, RDFS.label, Literal(clean_name(item['name'])) ))
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
        g.add((contact_person_URI, RDFS.label, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO.OEO_0000050, contact_person_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["based_on_sector_division"], None)):
        g.remove((s, p, o))

    _sector_divisions = json.loads(sector_divisions) if sector_divisions is not None else []
    for item in _sector_divisions:
        sector_divisions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((sector_divisions_URI, RDF.type, OEO.OEO_00000368))
        g.add((sector_divisions_URI, RDFS.label, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO["based_on_sector_division"], sector_divisions_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["covers_sector"], None)):
        g.remove((s, p, o))

    _sectors = json.loads(sectors) if sectors is not None else []
    for item in _sectors:
        sector_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
        g.add((sector_URI, RDF.type, OEO.OEO_00000367))
        g.add((sector_URI,RDFS.label, Literal(clean_name(item))))
        g.add((study_URI, OEO["covers_sector"], sector_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["covers_energy_carrier"], None)):
        g.remove((s, p, o))

    _energy_carriers = json.loads(energy_carriers) if energy_carriers is not None else []
    for item in _energy_carriers:
        energy_carriers_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
        g.add((energy_carriers_URI, RDF.type, OEO.OEO_00020039))
        g.add((energy_carriers_URI, RDFS.label, Literal(clean_name(item))))
        g.add((study_URI, OEO["covers_energy_carrier"], energy_carriers_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["covers_transformation_processes"], None)):
        g.remove((s, p, o))

    _energy_transformation_processes = json.loads(
        energy_transformation_processes) if energy_transformation_processes is not None else []
    for item in _energy_transformation_processes:
        energy_transformation_processes_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
        g.add((energy_transformation_processes_URI, RDF.type, OEO.OEO_00020003))
        g.add((energy_transformation_processes_URI, RDFS.label, Literal(clean_name(item))))
        g.add((study_URI, OEO["covers_transformation_processes"], energy_transformation_processes_URI))

    for s, p, o in g.triples((old_Study_URI, OEO["has_participant"], None)):
        g.remove((s, p, o))

    _models = json.loads(models) if models is not None else []
    for item in _models:
        model_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((model_URI, RDF.type, OEO.OEO_00000274))
        g.add((model_URI, RDFS.label, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO["has_participant"], model_URI))

    _frameworks = json.loads(frameworks) if frameworks is not None else []
    for item in _frameworks:
        framework_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((framework_URI, RDF.type, OEO.OEO_00000172))
        g.add((framework_URI, RDFS.label, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO["has_participant"], framework_URI))

    for s, p, o in g.triples((old_Study_URI, OEO.OEO_00000506, None)):
        g.remove((s, p, o))

    _authors = json.loads(authors) if authors is not None else []
    for item in _authors:
        author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
        g.add((author_URI, RDF.type, OEO.OEO_00000064))
        g.add((author_URI, RDFS.label, Literal(clean_name(item['name']))))
        g.add((study_URI, OEO.OEO_00000506, author_URI))

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
    for s, p, o in g.triples(( study_URI, RDFS.label, None )):
        factsheet['acronym'] = o

    for s, p, o in g.triples(( study_URI, OEKG.full_name, None )):
        factsheet['study_name'] = o

    for s, p, o in g.triples(( study_URI, DC.abstract, None )):
        factsheet['abstract'] = o

    factsheet['funding_sources'] = []
    for s, p, o in g.triples(( study_URI, OEO.RO_0002234, None )):
        label = g.value(o, RDFS.label)
        if label != None:
            factsheet['funding_sources'].append({ 'id': clean_name(label), 'name': clean_name(label) })
        
    factsheet['institution'] = []
    for s, p, o in g.triples(( study_URI, OEO.OEO_00000510, None )):
        label = g.value(o, RDFS.label)
        if label != None:
            factsheet['institution'].append({ 'id': clean_name(label), 'name': clean_name(label) })

    factsheet['contact_person'] = []
    for s, p, o in g.triples(( study_URI, OEO.OEO_0000050, None )):
        label = g.value(o, RDFS.label)
        if label != None:
            factsheet['contact_person'].append({ 'id': clean_name(label), 'name': clean_name(label) })

    factsheet['sector_divisions'] = []
    for s, p, o in g.triples(( study_URI, OEO["based_on_sector_division"], None )):
        label = g.value(o, RDFS.label)
        if label != None:
            factsheet['sector_divisions'].append({ 'id': clean_name(label), 'name': clean_name(label) })

    factsheet['sectors'] = []
    for s, p, o in g.triples(( study_URI, OEO["covers_sector"], None )):
        label = g.value(o, RDFS.label)
        if label != None:
            factsheet['sectors'].append({ 'id': clean_name(label), 'name': clean_name(label) })

    factsheet['energy_carriers'] = []
    for s, p, o in g.triples(( study_URI, OEO["covers_energy_carrier"], None )):
        label = g.value(o, RDFS.label)
        if label != None:
            factsheet['energy_carriers'].append({ 'id': clean_name(label), 'name': clean_name(label) })

    response = JsonResponse(factsheet, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    return response

@csrf_exempt
def delete_factsheet_by_id(request, *args, **kwargs):
    id = request.GET.get('id')
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(id))
    g.remove((study_URI, None, None)) 
    response = JsonResponse('factsheet removed!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def get_entities_by_type(request, *args, **kwargs):
    entity_type = request.GET.get('entity_type')
    entity_URI = URIRef("http://openenergy-platform.org/ontology/oeo/" + entity_type )

    entities = []
    for s, p, o in g.triples(( None, RDF.type, entity_URI )):
        # use the label instead of split
        entities.append(s.split('/')[-1])

    response = JsonResponse(entities, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response


@csrf_exempt
def add_entities(request, *args, **kwargs):
    request_body = json.loads(request.body)
    entity_type = request_body['entity_type']
    entity_label = request_body['entity_label']
    entity_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(entity_label) )

    g.add((entity_URI, RDF.type, OEO[entity_type]))
    g.add((entity_URI, RDFS.label, Literal(clean_name(entity_label))))

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

    g.add((_subject_URI, _predicate_URI, _object_URI))

    response = JsonResponse('A new fact added!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def delete_entities(request, *args, **kwargs):
    # request_body = json.loads(request.body)
    # entity_type = request_body['entity_type']
    # entity_label = request_body['entity_label']

    g.remove((None, None, None)) 

    entity_type = request.GET.get('entity_type')
    entity_label = request.GET.get('entity_label')

    entity_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + entity_type )
    entity_Label = URIRef("http://openenergy-platform.org/ontology/oekg/" + entity_label )

    g.remove((entity_Label, None, None)) 
    g.remove((None, None, entity_Label)) 
    response = JsonResponse('entity removed!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def get_all_factsheets(request, *args, **kwargs):
    all_factsheets = []
    for s, p, o in g.triples(( None, RDF.type, OEO.OEO_00000364 )):
        element = {}
        element['acronym'] =  g.value(s, RDFS.label) 
        element['study_name'] = g.value(s, OEKG.full_name) 
        element['abstract'] = g.value(s, DC.abstract) 
        all_factsheets.append(element)

    response = JsonResponse(all_factsheets, safe=False, content_type='application/json') 
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def get_all_factsheets_as_turtle(request, *args, **kwargs):
    all_factsheets_as_turtle = g.serialize(format="ttl")
    response = JsonResponse(all_factsheets_as_turtle, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    return response

@csrf_exempt
def get_all_factsheets_as_json_ld(request, *args, **kwargs):
    all_factsheets_as_turtle = g.serialize(format="json-ld")
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

    
