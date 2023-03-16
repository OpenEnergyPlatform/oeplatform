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
file = "reasoned-oeo-full.owl"
Ontology_URI = os.path.join(path, file)


print(Ontology_URI)
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
    report_doi = request_body['report_doi']
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
        oekg.add(( study_URI, RDF.type, OEO.OEO_00010252 ))
        oekg.add((study_URI, RDFS.label, Literal(acronym)))
        oekg.add((study_URI, DC.acronym, Literal(acronym)))
        oekg.add((study_URI, OEKG["full_name"], Literal(study_name)))
        oekg.add(( study_URI, DC.abstract, Literal(abstract) ))
        oekg.add(( study_URI, OEKG["report_title"], Literal(report_title) ))
        oekg.add(( study_URI, OEKG["date_of_publication"], Literal(date_of_publication) ))
        oekg.add(( study_URI, OEKG["place_of_publication"], Literal(place_of_publication) ))
        oekg.add(( study_URI, OEKG["link_to_study"], Literal(link_to_study) ))
        oekg.add(( study_URI, OEKG["doi"], Literal(report_doi) ))

        _scenarios = json.loads(scenarios) if scenarios is not None else []
        for item in _scenarios:
            scenario_URI = URIRef("http://openenergy-platform.org/ontology/oekg/scenario/" + clean_name(item["acronym"]))
            oekg.add(( study_URI, OEKG["has_scenario"], scenario_URI ))
            oekg.add(( scenario_URI, RDFS.label, Literal(item["acronym"])))
            oekg.add(( scenario_URI, OEKG["full_name"], Literal(item["name"])))
            oekg.add(( scenario_URI, DC.abstract, Literal(item["abstract"]) ))
            oekg.add(( scenario_URI, OEKG['scenario_uuid'], Literal(item["id"]) ))

            if 'regions' in item:
                for region in item['regions']:
                    region_URI = URIRef("http://openenergy-platform.org/ontology/oekg/region/" + clean_name(region['name']))
                    oekg.add(( region_URI, RDF.type, OEO.BFO_0000006))
                    oekg.add(( region_URI, RDFS.label, Literal(region['name'])))
                    oekg.add(( scenario_URI, OEO.OEO_00000522, region_URI ))
                
            if 'interacting_regions' in item:
                for interacting_region in item['interacting_regions']:
                    interacting_regions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/interactin_region/" + clean_name(interacting_region['name']))
                    oekg.add(( interacting_regions_URI, RDF.type, OEO.OEO_00020036))
                    oekg.add(( interacting_regions_URI, RDFS.label, Literal(interacting_region['name'])))
                    oekg.add(( scenario_URI, OEO.OEO_00000522, interacting_regions_URI ))
            
            if 'scenario_years' in item:
                for scenario_year in item['scenario_years']:
                    scenario_years_URI = URIRef("http://openenergy-platform.org/ontology/oekg/scenario_year/" + clean_name(scenario_year['name']))
                    oekg.add(( scenario_years_URI, RDF.type, OEO.OEO_00020097))
                    oekg.add(( scenario_years_URI, RDFS.label, Literal(scenario_year['name'])))
                    oekg.add(( scenario_URI, OEO.OEO_00000522, scenario_years_URI ))

            if 'keywords' in item:
                for keyword in item['keywords']:
                    oekg.add(( scenario_URI,  OEO.OEO_00000522, Literal(keyword) ))

            if 'input_datasets' in item:
                for input_dataset in item['input_datasets']:
                    input_dataset_URI = URIRef("http://openenergy-platform.org/ontology/oekg/input_datasets/" + clean_name(input_dataset['value']['label']))
                    oekg.add(( input_dataset_URI, RDF.type, OEO.OEO_00020097))
                    oekg.add(( input_dataset_URI, RDFS.label, Literal(input_dataset['value']['label'])))
                    oekg.add(( input_dataset_URI, OEO['has_iri'], Literal(input_dataset['value']['iri'])))
                    oekg.add(( input_dataset_URI, OEO['has_id'], Literal(input_dataset['idx'])))
                    oekg.add(( input_dataset_URI, OEO['has_key'], Literal(input_dataset['key'])))
                    oekg.add(( scenario_URI,  OEO.RO_0002233, input_dataset_URI ))

            if 'output_datasets' in item:
                for output_dataset in item['output_datasets']:
                    output_dataset_URI = URIRef("http://openenergy-platform.org/ontology/oekg/output_datasets/" + clean_name(output_dataset['value']['label']))
                    oekg.add(( output_dataset_URI, RDF.type, OEO.OEO_00020097))
                    oekg.add(( output_dataset_URI, RDFS.label, Literal(output_dataset['value']['label'])))
                    oekg.add(( output_dataset_URI, OEO['has_iri'], Literal(output_dataset['value']['iri'])))
                    oekg.add(( output_dataset_URI, OEO['has_id'], Literal(output_dataset['idx'])))
                    oekg.add(( output_dataset_URI, OEO['has_key'], Literal(output_dataset['key'])))
                    oekg.add(( scenario_URI,  OEO.RO_0002234, output_dataset_URI ))


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
            oekg.add((study_URI, OEO.OEO_00000505, sector_URI))

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
            oekg.add((study_URI, OBO.RO_0000057, model_URI))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            framework_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((framework_URI, RDF.type, OEO.OEO_00000172))
            oekg.add((framework_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OBO.RO_0000057, framework_URI))

        _authors = json.loads(authors) if authors is not None else []
        for item in _authors:
            author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/authors/" + clean_name(item['name']))
            oekg.add((author_URI, RDF.type, OEO.OEO_00000064))
            oekg.add((author_URI, RDFS.label, Literal(item['name'])))
            oekg.add((study_URI, OEO.OEO_00000506, author_URI))

        _study_keywords = json.loads(study_keywords) if study_keywords is not None else []
        if _study_keywords != []:
            for item in study_keywords:
                study_keyword_URI = URIRef("http://openenergy-platform.org/ontology/oekg/keywords/" + clean_name(item))
                oekg.add((study_keyword_URI, RDF.type, OEKG['keyword']))
                oekg.add((study_keyword_URI, RDFS.label, Literal(item)))
                oekg.add((study_URI, OEO.OEO_00000522, study_keyword_URI))
        

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

            oekg.add((study_URI, RDF.type, OEO.OEO_00010252 ))
            oekg.add((study_URI, RDFS.label, Literal(acronym)))

        
        for s, p, o in oekg.triples((study_URI, OEKG["has_scenario"], None)):
            oekg.remove((s, p, o))
        

        _scenarios = json.loads(scenarios) if scenarios is not None else []
        for item in _scenarios:
            print(item)
            scenario_URI = URIRef("http://openenergy-platform.org/ontology/oekg/scenario/" + clean_name(item["acronym"]))

            for s, p, o in oekg.triples((scenario_URI, OEKG['scenario_uuid'], None)):
                oekg.remove((s, p, o))

            prev_scenario = [e for e in fsData["scenarios"] if e['id'] == item['id']]
            if prev_scenario != []:
                prev_scenario_id = prev_scenario[0]['id']
                oekg.add(( scenario_URI, OEKG['scenario_uuid'], Literal(prev_scenario_id) ))
            else:
                oekg.add(( scenario_URI, OEKG['scenario_uuid'], Literal(item["id"]) ))

            for s, p, o in oekg.triples(( scenario_URI, RDFS.label, None )):
                oekg.remove((s, p, o))
            oekg.add(( scenario_URI, RDFS.label, Literal(item["acronym"])))

            for s, p, o in oekg.triples(( scenario_URI, OEKG["full_name"], None )):
                oekg.remove((s, p, o))
            oekg.add(( scenario_URI, OEKG["full_name"], Literal(item["name"])))

            for s, p, o in oekg.triples(( scenario_URI, DC.abstract, None )):
                oekg.remove((s, p, o))
            oekg.add(( scenario_URI, DC.abstract, Literal(item["abstract"]) ))

            for s, p, o in oekg.triples(( scenario_URI, OEO.OEO_00000522, None )):
                oekg.remove((s, p, o))

            if 'regions' in item:
                for region in item['regions']:
                    region_URI = URIRef("http://openenergy-platform.org/ontology/oekg/region/" + clean_name(region['name']))
                    oekg.add(( region_URI, RDF.type, OEO.BFO_0000006))
                    oekg.add(( region_URI, RDFS.label, Literal(region['name'])))
                    oekg.add(( scenario_URI, OEO.OEO_00000522, region_URI ))
                
            if 'interacting_regions' in item:
                for interacting_region in item['interacting_regions']:
                    interacting_regions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/interactin_region/" + clean_name(interacting_region['name']))
                    oekg.add(( interacting_regions_URI, RDF.type, OEO.OEO_00020036))
                    oekg.add(( interacting_regions_URI, RDFS.label, Literal(interacting_region['name'])))
                    oekg.add(( scenario_URI, OEO.OEO_00000522, interacting_regions_URI ))
            
            if 'scenario_years' in item:
                for scenario_year in item['scenario_years']:
                    scenario_years_URI = URIRef("http://openenergy-platform.org/ontology/oekg/scenario_year/" + clean_name(scenario_year['name']))
                    oekg.add(( scenario_years_URI, RDF.type, OEO.OEO_00020097))
                    oekg.add(( scenario_years_URI, RDFS.label, Literal(scenario_year['name'])))
                    oekg.add(( scenario_URI, OEO.OEO_00000522, scenario_years_URI ))

            if 'keywords' in item:
                for keyword in item['keywords']:
                    oekg.add(( scenario_URI,  OEO.OEO_00000522, Literal(keyword) ))

            for s, p, o in oekg.triples(( scenario_URI, OEO.RO_0002233, None )):
                oekg.remove((s, p, o))
            if 'input_datasets' in item:
                for input_dataset in item['input_datasets']:
                    input_dataset_URI = URIRef("http://openenergy-platform.org/ontology/oekg/input_datasets/" + clean_name(input_dataset['value']['label']))
                    oekg.add(( input_dataset_URI, RDF.type, OEO.OEO_00020097))
                    oekg.add(( input_dataset_URI, RDFS.label, Literal(input_dataset['value']['label'])))
                    oekg.add(( input_dataset_URI, OEO['has_iri'], Literal(input_dataset['value']['iri'])))
                    oekg.add(( input_dataset_URI, OEO['has_id'], Literal(input_dataset['idx'])))
                    oekg.add(( input_dataset_URI, OEO['has_key'], Literal(input_dataset['key'])))
                    oekg.add(( scenario_URI,  OEO.RO_0002233, input_dataset_URI ))

            for s, p, o in oekg.triples(( scenario_URI, OEO.RO_0002234, None )):
                oekg.remove((s, p, o))
            if 'output_datasets' in item:
                for output_dataset in item['output_datasets']:
                    output_dataset_URI = URIRef("http://openenergy-platform.org/ontology/oekg/output_datasets/" + clean_name(output_dataset['value']['label']))
                    oekg.add(( output_dataset_URI, RDF.type, OEO.OEO_00020097))
                    oekg.add(( output_dataset_URI, RDFS.label, Literal(output_dataset['value']['label'])))
                    oekg.add(( output_dataset_URI, OEO['has_iri'], Literal(output_dataset['value']['iri'])))
                    oekg.add(( output_dataset_URI, OEO['has_id'], Literal(output_dataset['idx'])))
                    oekg.add(( output_dataset_URI, OEO['has_key'], Literal(output_dataset['key'])))
                    oekg.add(( scenario_URI,  OEO.RO_0002234, output_dataset_URI ))

            oekg.add(( study_URI, OEKG["has_scenario"], scenario_URI ))
                

        for s, p, o in oekg.triples((study_URI, OEKG["full_name"], None)):
            oekg.remove((s, p, o))
        oekg.add((study_URI, OEKG["full_name"], Literal(studyName)))

        for s, p, o in oekg.triples((study_URI, OEKG["report_title"], None)):
            oekg.remove((s, p, o))
        oekg.add(( study_URI, OEKG["report_title"], Literal(report_title) ))

        for s, p, o in oekg.triples((study_URI, OEKG["date_of_publication"], None)):
            oekg.remove((s, p, o))
        oekg.add(( study_URI, OEKG["date_of_publication"], Literal(date_of_publication) ))


        for s, p, o in oekg.triples((study_URI, OEKG["place_of_publication"], None)):
            oekg.remove((s, p, o))
        oekg.add(( study_URI, OEKG["place_of_publication"], Literal(place_of_publication) ))


        for s, p, o in oekg.triples((study_URI, OEKG["link_to_study"], None)):
            oekg.remove((s, p, o))
        oekg.add(( study_URI, OEKG["link_to_study"], Literal(link_to_study) ))


        for s, p, o in oekg.triples((study_URI, OEKG["doi"], None)):
            oekg.remove((s, p, o))
        oekg.add(( study_URI, OEKG["doi"], Literal(report_doi) ))


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

        for s, p, o in oekg.triples((old_Study_URI, OEO.OEO_00000505, None)):
            oekg.remove((s, p, o))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item))
            oekg.add((sector_URI, RDF.type, OEO.OEO_00000367))
            oekg.add((sector_URI,RDFS.label, Literal(item)))
            oekg.add((study_URI, OEO.OEO_00000505, sector_URI))

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

        for s, p, o in oekg.triples((old_Study_URI, OBO.RO_0000057, None)):
            oekg.remove((s, p, o))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            model_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((model_URI, RDF.type, OEO.OEO_00000274))
            oekg.add((model_URI, RDFS.label, Literal(clean_name(item['name']))))
            oekg.add((study_URI, OBO.RO_0000057, model_URI))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            framework_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(item['name']))
            oekg.add((framework_URI, RDF.type, OEO.OEO_00000172))
            oekg.add((framework_URI, RDFS.label, Literal(clean_name(item['name']))))
            oekg.add((study_URI, OBO.RO_0000057, framework_URI))

        for s, p, o in oekg.triples((old_Study_URI, OEO.OEO_00000506, None)):
            oekg.remove((s, p, o))

        _authors = json.loads(authors) if authors is not None else []
        for item in _authors:
            author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/authors/" + clean_name(item['name']))
            oekg.add((author_URI, RDF.type, OEO.OEO_00000064))
            oekg.add((author_URI, RDFS.label, Literal(clean_name(item['name']))))
            oekg.add((study_URI, OEO.OEO_00000506, author_URI))

        _study_keywords = json.loads(study_keywords) if study_keywords is not None else []
        for item in _study_keywords:
            study_keyword_URI = URIRef("http://openenergy-platform.org/ontology/oekg/keywords/" + clean_name(item))
            oekg.add((study_keyword_URI, RDF.type, OEKG['keyword']))
            oekg.add((study_keyword_URI, RDFS.label, Literal(item)))
            oekg.add((study_URI, OEO.OEO_00000522, study_keyword_URI))

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
        factsheet['report_doi'] = o

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
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000505, None )):
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

    factsheet['models'] = []
    factsheet['frameworks'] = []
    for s, p, o in oekg.triples(( study_URI, OBO.RO_0000057, None )):
        o_label = oekg.value(o, RDFS.label)
        o_type = oekg.value(o, RDF.type)
        if (o_type == OEO.OEO_00000172):
            factsheet['frameworks'].append({'id': o_label, 'name': o_label})
        if (o_type == OEO.OEO_00000274):
            factsheet['models'].append({'id': o_label, 'name': o_label})

    factsheet['scenarios'] = []
    for s, p, o in oekg.triples(( study_URI, OEKG['has_scenario'], None )):
        scenario = {}
        label = oekg.value(o, RDFS.label)
        abstract = oekg.value(o, DC.abstract)
        scenario_uuid = oekg.value(o, OEKG['scenario_uuid'])

        if label != None:
            scenario['name'] = label
            scenario['acronym'] = label

        scenario['abstract'] = abstract
        scenario['id'] = scenario_uuid

        scenario['scenario_years'] = []
        scenario['regions'] = []
        scenario['interacting_regions'] = []
        scenario['keywords'] = []
        scenario['input_datasets'] = []
        scenario['output_datasets'] = []

        for s1, p1, o1 in oekg.triples(( o, OEO.OEO_00000522, None )):
            o1_type = oekg.value(o1, RDF.type)
            o1_label = oekg.value(o1, RDFS.label)
            if (o1_type == OEO.OEO_00020097):
                scenario['scenario_years'].append({'id': o1_label, 'name': o1_label})
            if (o1_type == OEO.BFO_0000006):
                scenario['regions'].append({'id': o1_label, 'name': o1_label})
            if (o1_type == OEO.OEO_00020036):
                scenario['interacting_regions'].append({'id': o1_label, 'name': o1_label})
            if (o1_type == None):
                scenario['keywords'].append(o1)

        for s2, p2, o2 in oekg.triples(( o, OEO.RO_0002233, None )):
            o2_iri = oekg.value(o2, OEO['has_iri'])
            o2_label = oekg.value(o2, RDFS.label)
            o2_key = oekg.value(o2, OEO['has_key'])
            o2_idx = oekg.value(o2, OEO['has_id'])

            scenario['input_datasets'].append({ "key": o2_key, "idx": o2_idx, "value": { "label": o2_label, "iri": o2_iri} })

        for s3, p3, o3 in oekg.triples(( o, OEO.RO_0002234, None )):
            o3_iri = oekg.value(o3, OEO['has_iri'])
            o3_label = oekg.value(o3, RDFS.label)
            o3_key = oekg.value(o3, OEO['has_key'])
            o3_idx = oekg.value(o3, OEO['has_id'])

            scenario['output_datasets'].append({ "key": o3_key, "idx": o3_idx, "value": { "label": o3_label, "iri": o3_iri} })

        factsheet['scenarios'].append(scenario)
            

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
    vocab = entity_type.split('.')[0]
    classId = entity_type.split('.')[1]
    prefix = ''
    if vocab == 'OEO':
        prefix = "http://openenergy-platform.org/ontology/oeo/"
    if vocab == 'OBO':
        prefix = "http://purl.obolibrary.org/obo/"

    entity_URI = URIRef(prefix + classId)

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

    vocab = entity_type.split('.')[0]
    classId = entity_type.split('.')[1]
    prefix = ''
    if vocab == 'OEO':
        prefix = "http://openenergy-platform.org/ontology/oeo/"
    if vocab == 'OBO':
        prefix = "http://purl.obolibrary.org/obo/"

    entity_type_URI = URIRef(prefix + classId)

    entity_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(entity_label) )

    oekg.add((entity_URI, RDF.type, entity_type_URI ))
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

    vocab = entity_type.split('.')[0]
    classId = entity_type.split('.')[1]
    prefix = ''
    if vocab == 'OEO':
        prefix = "http://openenergy-platform.org/ontology/oeo/"
    if vocab == 'OBO':
        prefix = "http://purl.obolibrary.org/obo/"

    entity_type_URI = URIRef(prefix + classId)
    entity_Label_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(entity_label) )
    new_entity_label_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(new_entity_label))

    oekg.add((new_entity_label_URI, RDF.type, entity_type_URI))
    oekg.add((new_entity_label_URI, RDFS.label, Literal(new_entity_label)))

    """  entity_edit_history = URIRef("http://openenergy-platform.org/ontology/oekg/" + clean_name(new_entity_label) + "/edit_history")
    oekg.add((entity_edit_history, RDFS.label, Literal(new_entity_label)))
    oekg.add((entity_edit_history, RDF.type, OEKG["edit_history"]))
    oekg.add((entity_edit_history, OEKG["prev"], Literal(entity_label) ))
    oekg.add((entity_edit_history, OEKG["next"], Literal(new_entity_label) ))
    oekg.add((entity_edit_history, OEKG["date"], Literal(date.today()) )) """

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
    for s, p, o in oekg.triples(( None, RDF.type, OEO.OEO_00010252 )):
        print(s)
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
            'value': str(uuid.uuid1()),
            'label': sl
        }
        children = []
        for s1, p, o in oeo.triples(( None, RDFS.subClassOf, s )):
            sl1 = oeo.value(s1, RDFS.label)
            children2 = []
            for s2, p, o in oeo.triples(( None, RDFS.subClassOf, s1 )):
                sl2 = oeo.value(s2, RDFS.label)
                children3 = []
                for s3, p, o in oeo.triples(( None, RDFS.subClassOf, s2 )):
                    sl3 = oeo.value(s3, RDFS.label)
                    children3.append({
                        'value': str(uuid.uuid1()),
                        'label': sl3
                    })

                if children3 != []:
                    children2.append({
                        'value': str(uuid.uuid1()),
                        'label': sl2,
                        'children': children3
                    })
                else:
                    children2.append({
                        'value': str(uuid.uuid1()),
                        'label': sl2,
                    })


            if children2 != []:
                children.append({
                'value': str(uuid.uuid1()),
                'label': sl1,
                'children': children2
                })
            else:
                children.append({
                'value': str(uuid.uuid1()),
                'label': sl1
                })


        if children != []:
            parent['children'] = children

        energy_transformation_processes.append(parent)
    elements['energy_transformation_processes'] = energy_transformation_processes

    energy_carriers = []
    unique_energy_carriers = []
    for s, p, o in oeo.triples(( None, RDFS.subClassOf, OEO.OEO_00020039 )):
        sl = oeo.value(s, RDFS.label)
        if str(sl) not in unique_energy_carriers:
            unique_energy_carriers.append(str(sl))
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
                if str(sl2) not in unique_energy_carriers:
                    unique_energy_carriers.append(str(sl2))
                    children2.append({
                        'value': sl2,
                        'label': sl2
                    })

            if str(sl1) not in unique_energy_carriers:
                unique_energy_carriers.append(str(sl1))
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

    
