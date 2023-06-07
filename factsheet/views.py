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
from rdflib import ConjunctiveGraph, Graph, Literal, RDF, URIRef, BNode, XSD
from rdflib.plugins.stores import sparqlstore
from rdflib.namespace import XSD, Namespace
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default

import os
from oeplatform.settings import ONTOLOGY_FOLDER
from datetime import date
from SPARQLWrapper import SPARQLWrapper, JSON
import sys
from owlready2 import get_ontology

versions = os.listdir(f"{ONTOLOGY_FOLDER}/{'oeo'}")
version = max((d for d in versions), key=lambda d: [int(x) for x in d.split(".")])
path = f"{ONTOLOGY_FOLDER}/{'oeo'}/{version}"
file = "reasoned-oeo-full.owl"
#file = "oeo-full.owl"
Ontology_URI = os.path.join(path, file)


sys.path.append(path)

oeo = Graph()
oeo.parse(Ontology_URI)

oeo_owl = get_ontology(Ontology_URI).load()

#query_endpoint = 'http://localhost:3030/ds/query'
#update_endpoint = 'http://localhost:3030/ds/update'

query_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/query'
update_endpoint = 'https://toekb.iks.cs.ovgu.de:3443/oekg/update'

sparql = SPARQLWrapper(query_endpoint)

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
    uid = request_body['uid']
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
        study_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + uid )
        oekg.add(( study_URI, RDF.type, OEO.OEO_00010252 ))
        if acronym != '':
            oekg.add(( study_URI, DC.acronym, Literal(acronym)))
        if study_name != '':
            oekg.add((study_URI, OEKG["has_full_name"], Literal(study_name)))
        if abstract != '':
            oekg.add(( study_URI, DC.abstract, Literal(abstract) ))
        if report_title != '':
            oekg.add(( study_URI, OEKG["report_title"], Literal(report_title) ))
        if date_of_publication != '01-01-1900' and date_of_publication != '':
            oekg.add(( study_URI, OEKG["date_of_publication"], Literal(date_of_publication[:10], datatype=XSD.date) ))
        if place_of_publication:
            oekg.add(( study_URI, OEKG["place_of_publication"], Literal(place_of_publication) ))
        if link_to_study != '':
            oekg.add(( study_URI, OEKG["link_to_study"], Literal(link_to_study) ))
        if report_doi != '':
            oekg.add(( study_URI, OEKG["doi"], Literal(report_doi) ))

        _scenarios = json.loads(scenarios) if scenarios is not None else []
        for item in _scenarios:
            if item["acronym"] != '':
                scenario_URI = URIRef("http://openenergy-platform.org/ontology/oekg/scenario/" + item["id"]) 
                oekg.add(( study_URI, OEKG["has_scenario"], scenario_URI ))
                oekg.add(( scenario_URI, RDFS.label, Literal(item["acronym"])))
                if item["name"] != '':
                    oekg.add(( scenario_URI, OEKG["has_full_name"], Literal(item["name"])))
                    oekg.add(( scenario_URI, RDF.type, OEO.OEO_00000365))
                if item["abstract"] != '':
                    oekg.add(( scenario_URI, DC.abstract, Literal(item["abstract"]) ))

                oekg.add(( scenario_URI, OEKG['scenario_uuid'], Literal(item["id"]) ))

                if 'regions' in item:
                    for region in item['regions']:
                        region_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + region['iri'])
                        oekg.add(( scenario_URI, OEO.OEO_00000522, region_URI ))
                    
                if 'interacting_regions' in item:
                    for interacting_region in item['interacting_regions']:
                        interacting_regions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + interacting_region['iri'])
                        oekg.add(( scenario_URI, OEO['covers_interacting_regions'], interacting_regions_URI ))
                
                if 'scenario_years' in item:
                    for scenario_year in item['scenario_years']:
                        oekg.add(( scenario_URI, OEO.OEO_00020224, Literal(scenario_year['name']) ))

                if 'keywords' in item:
                    for keyword in item['keywords']:
                        oekg.add(( scenario_URI, OEO["has_scenario_descriptor"], Literal(keyword) ))

                if 'input_datasets' in item:
                    for input_dataset in item['input_datasets']:
                        input_dataset_URI = URIRef("http://openenergy-platform.org/ontology/oekg/input_datasets/" + input_dataset['key'])
                        oekg.add(( input_dataset_URI, RDF.type, OEO.OEO_00030030))
                        oekg.add(( input_dataset_URI, RDFS.label, Literal(input_dataset['value']['label'])))
                        oekg.add(( input_dataset_URI, OEO['has_iri'], Literal(input_dataset['value']['iri'])))
                        oekg.add(( input_dataset_URI, OEO['has_id'], Literal(input_dataset['idx'])))
                        oekg.add(( input_dataset_URI, OEO['has_key'], Literal(input_dataset['key'])))
                        oekg.add(( scenario_URI,  OEO.RO_0002233, input_dataset_URI ))

                if 'output_datasets' in item:
                    for output_dataset in item['output_datasets']:
                        output_dataset_URI = URIRef("http://openenergy-platform.org/ontology/oekg/output_datasets/" + output_dataset['key'])
                        oekg.add(( output_dataset_URI, RDF.type, OEO.OEO_00030029))
                        oekg.add(( output_dataset_URI, RDFS.label, Literal(output_dataset['value']['label'])))
                        oekg.add(( output_dataset_URI, OEO['has_iri'], Literal(output_dataset['value']['iri'])))
                        oekg.add(( output_dataset_URI, OEO['has_id'], Literal(output_dataset['idx'])))
                        oekg.add(( output_dataset_URI, OEO['has_key'], Literal(output_dataset['key'])))
                        oekg.add(( scenario_URI,  OEO.RO_0002234, output_dataset_URI ))

        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + item['iri'])
            oekg.add(( study_URI, OEO.OEO_00000510, institution_URI ))

        funding_sources = json.loads(funding_source) if funding_source is not None else []
        for item in funding_sources:
            funding_source_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + item['iri'])
            oekg.add(( study_URI, OEO.OEO_00000509, funding_source_URI ))

        contact_persons = json.loads(contact_person) if contact_person is not None else []
        for item in contact_persons:
            contact_person_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + item['iri'])
            oekg.add((study_URI, OEO.OEO_0000050, contact_person_URI))

        _sector_divisions = json.loads(sector_divisions) if sector_divisions is not None else []
        for item in _sector_divisions:
            sector_divisions_URI = URIRef(item['class'])
            oekg.add((study_URI, OEO["based_on_sector_division"], sector_divisions_URI))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef(item["class"])
            oekg.add((study_URI, OEO.OEO_00000505, sector_URI))

        _energy_carriers = json.loads(energy_carriers) if energy_carriers is not None else []
        for item in _energy_carriers:
            energy_carriers_URI = URIRef(item["class"])
            oekg.add((study_URI, OEO["covers_energy_carrier"], energy_carriers_URI))

        _energy_transformation_processes = json.loads(energy_transformation_processes) if energy_transformation_processes is not None else []
        for item in _energy_transformation_processes:
            energy_transformation_processes_URI = URIRef(item["class"])
            oekg.add((study_URI, OEO["covers_transformation_processes"], energy_transformation_processes_URI))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            oekg.add((study_URI, OEO["has_model"], Literal(item['name'])))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            oekg.add((study_URI, OEO["has_framework"], Literal(item['name'])))

        _authors = json.loads(authors) if authors is not None else []
        for item in _authors:
            author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + item['iri'])
            oekg.add((study_URI, OEO.OEO_00000506, author_URI))

        _study_keywords = json.loads(study_keywords) if study_keywords is not None else []
        if _study_keywords != []:
            for keyword in _study_keywords:
                oekg.add(( study_URI, OEO["has_study_keyword"], Literal(keyword) ))

        response = JsonResponse('Factsheet saved', safe=False, content_type='application/json')
        patch_response_headers(response, cache_timeout=1)
        return response

@csrf_exempt
def update_factsheet(request, *args, **kwargs):
    request_body = json.loads(request.body)
    fsData = request_body['fsData']
    id = request_body['id']
    uid = request_body['uid']
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
        study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + uid)

        for s, p, o in oekg.triples(( study_URI, OEKG["has_scenario"], None )):
            oekg.remove((s, p, o))

        _scenarios = json.loads(scenarios) if scenarios is not None else []
        for item in _scenarios:
            if item["acronym"] != '':
                scenario_URI = URIRef("http://openenergy-platform.org/ontology/oekg/scenario/" + item["id"])

                for s, p, o in oekg.triples((scenario_URI, OEKG['scenario_uuid'], None)):
                    oekg.remove((s, p, o))

                # prev_scenario = [e for e in fsData["scenarios"] if e['id'] == item['id']]
                # if prev_scenario != []:
                #     prev_scenario_id = prev_scenario[0]['id']
                # else:
                oekg.add(( scenario_URI, OEKG['scenario_uuid'], Literal(item["id"]) ))
                oekg.add(( scenario_URI, RDF.type, OEO.OEO_00000365 ))

                for s, p, o in oekg.triples(( scenario_URI, RDFS.label, None )):
                    oekg.remove((s, p, o))
                oekg.add(( scenario_URI, RDFS.label, Literal(item["acronym"])))

                for s, p, o in oekg.triples(( scenario_URI, OEKG["has_full_name"], None )):
                    oekg.remove((s, p, o))
                if item["name"] != '':
                    oekg.add(( scenario_URI, OEKG["has_full_name"], Literal(item["name"])))

                for s, p, o in oekg.triples(( scenario_URI, DC.abstract, None )):
                    oekg.remove((s, p, o))
                if item["abstract"] != '' and item["abstract"] != None:
                    oekg.add(( scenario_URI, DC.abstract, Literal(item["abstract"]) ))

                for s, p, o in oekg.triples(( scenario_URI, OEO.OEO_00000522, None )):
                    oekg.remove((s, p, o))

                for s, p, o in oekg.triples(( scenario_URI, OEO['covers_interacting_regions'], None )):
                    oekg.remove((s, p, o))

                for s, p, o in oekg.triples(( scenario_URI, OEO.OEO_00020224, None )):
                    oekg.remove((s, p, o))

                for s, p, o in oekg.triples(( scenario_URI, OEO["has_scenario_descriptor"], None )):
                    oekg.remove((s, p, o))

                if 'regions' in item:
                    for region in item['regions']:
                        region_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + region['iri'])
                        oekg.add(( scenario_URI, OEO.OEO_00000522, region_URI ))
                    
                if 'interacting_regions' in item:
                    for interacting_region in item['interacting_regions']:
                        interacting_regions_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + interacting_region['iri'])
                        oekg.add(( scenario_URI, OEO['covers_interacting_regions'], interacting_regions_URI ))
                
                if 'scenario_years' in item:
                    for scenario_year in item['scenario_years']:
                        oekg.add(( scenario_URI, OEO.OEO_00020224, Literal(scenario_year['name']) ))

                if 'keywords' in item:
                    for keyword in item['keywords']:
                        oekg.add(( scenario_URI, OEO["has_scenario_descriptor"], Literal(keyword) ))

                for s, p, o in oekg.triples(( scenario_URI, OEO.RO_0002233, None )):
                    oekg.remove((s, p, o))
                if 'input_datasets' in item:
                    for input_dataset in item['input_datasets']:
                        input_dataset_URI = URIRef("http://openenergy-platform.org/ontology/oekg/input_datasets/" + input_dataset['key'])
                        oekg.add(( input_dataset_URI, RDF.type, OEO.OEO_00030030))
                        oekg.add(( input_dataset_URI, RDFS.label, Literal(input_dataset['value']['label'])))
                        oekg.add(( input_dataset_URI, OEO['has_iri'], Literal(input_dataset['value']['iri'])))
                        oekg.add(( input_dataset_URI, OEO['has_id'], Literal(input_dataset['idx'])))
                        oekg.add(( input_dataset_URI, OEO['has_key'], Literal(input_dataset['key'])))
                        oekg.add(( scenario_URI,  OEO.RO_0002233, input_dataset_URI ))

                for s, p, o in oekg.triples(( scenario_URI, OEO.RO_0002234, None )):
                    oekg.remove((s, p, o))
                if 'output_datasets' in item:
                    for output_dataset in item['output_datasets']:
                        output_dataset_URI = URIRef("http://openenergy-platform.org/ontology/oekg/output_datasets/" + output_dataset['key'])
                        oekg.add(( output_dataset_URI, RDF.type, OEO.OEO_00030029))
                        oekg.add(( output_dataset_URI, RDFS.label, Literal(output_dataset['value']['label'])))
                        oekg.add(( output_dataset_URI, OEO['has_iri'], Literal(output_dataset['value']['iri'])))
                        oekg.add(( output_dataset_URI, OEO['has_id'], Literal(output_dataset['idx'])))
                        oekg.add(( output_dataset_URI, OEO['has_key'], Literal(output_dataset['key'])))
                        oekg.add(( scenario_URI,  OEO.RO_0002234, output_dataset_URI ))

                oekg.add(( study_URI, OEKG["has_scenario"], scenario_URI ))
                
        for s, p, o in oekg.triples((study_URI, DC.acronym, None)):
            oekg.remove((s, p, o))
        if acronym != '':
            oekg.add((study_URI, DC.acronym, Literal(acronym)))

        for s, p, o in oekg.triples((study_URI, OEKG["has_full_name"], None)):
            oekg.remove((s, p, o))
        if studyName != '':
            oekg.add((study_URI, OEKG["has_full_name"], Literal(studyName)))

        for s, p, o in oekg.triples((study_URI, OEKG["report_title"], None)):
            oekg.remove((s, p, o))
        if report_title != '':
            oekg.add(( study_URI, OEKG["report_title"], Literal(report_title) ))

        for s, p, o in oekg.triples((study_URI, OEKG["date_of_publication"], None)):
            oekg.remove((s, p, o))
        if date_of_publication != '01-01-1900' and date_of_publication != '':
            oekg.add(( study_URI, OEKG["date_of_publication"], Literal(date_of_publication[:10], datatype=XSD.date) ))

        for s, p, o in oekg.triples((study_URI, OEKG["place_of_publication"], None)):
            oekg.remove((s, p, o))
        if place_of_publication != '':
            oekg.add(( study_URI, OEKG["place_of_publication"], Literal(place_of_publication) ))

        for s, p, o in oekg.triples((study_URI, OEKG["link_to_study"], None)):
            oekg.remove((s, p, o))
        if link_to_study != '':
            oekg.add(( study_URI, OEKG["link_to_study"], Literal(link_to_study) ))

        for s, p, o in oekg.triples((study_URI, OEKG["doi"], None)):
            oekg.remove((s, p, o))
        if report_doi != '':
            oekg.add(( study_URI, OEKG["doi"], Literal(report_doi) ))

        for s, p, o in oekg.triples((study_URI, OEO.OEO_00000510, None)):
            oekg.remove((s, p, o))
        institutions = json.loads(institution) if institution is not None else []
        for item in institutions:
            institution_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + item['iri'])
            oekg.add(( study_URI, OEO.OEO_00000510, institution_URI ))

        for s, p, o in oekg.triples((study_URI, OEO.RO_0002234, None)):
            oekg.remove((s, p, o))
        funding_sources = json.loads(funding_source) if funding_source is not None else []
        for item in funding_sources:
            funding_source_URI =  URIRef("http://openenergy-platform.org/ontology/oekg/" + item['iri'])
            oekg.add(( study_URI, OEO.OEO_00000509, funding_source_URI ))

        for s, p, o in oekg.triples((study_URI, DC.abstract, None)):
            oekg.remove((s, p, o))
        if abstract != '':
            oekg.add(( study_URI, DC.abstract, Literal(abstract) ))

        for s, p, o in oekg.triples((study_URI, OEO.OEO_00000508, None)):
            oekg.remove((s, p, o))
        contact_persons = json.loads(contact_person) if contact_person is not None else []
        for item in contact_persons:
            contact_person_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + item['iri'])
            oekg.add((study_URI, OEO.OEO_00000508, contact_person_URI))

        for s, p, o in oekg.triples((study_URI, OEO["based_on_sector_division"], None)):
            oekg.remove((s, p, o))

        _sector_divisions = json.loads(sector_divisions) if sector_divisions is not None else []
        for item in _sector_divisions:
            sector_divisions_URI = URIRef(item['class'])
            oekg.add((study_URI, OEO["based_on_sector_division"], sector_divisions_URI))

        for s, p, o in oekg.triples((study_URI, OEO.OEO_00000505, None)):
            oekg.remove((s, p, o))

        _sectors = json.loads(sectors) if sectors is not None else []
        for item in _sectors:
            sector_URI = URIRef(item["class"])
            oekg.add((study_URI, OEO.OEO_00000505, sector_URI))

        for s, p, o in oekg.triples((study_URI, OEO["covers_energy_carrier"], None)):
            oekg.remove((s, p, o))

        _energy_carriers = json.loads(energy_carriers) if energy_carriers is not None else []
        for item in _energy_carriers:
            energy_carriers_URI = URIRef(item["class"])
            oekg.add((study_URI, OEO["covers_energy_carrier"], energy_carriers_URI))

        for s, p, o in oekg.triples((study_URI, OEO["covers_transformation_processes"], None)):
            oekg.remove((s, p, o))

        _energy_transformation_processes = json.loads(energy_transformation_processes) if energy_transformation_processes is not None else []
        for item in _energy_transformation_processes:
            energy_transformation_processes_URI = URIRef(item["class"])
            oekg.add((study_URI, OEO["covers_transformation_processes"], energy_transformation_processes_URI))

        for s, p, o in oekg.triples((study_URI, OBO.RO_0000057, None)):
            oekg.remove((s, p, o))

        _models = json.loads(models) if models is not None else []
        for item in _models:
            oekg.add((study_URI, OEO["has_model"], Literal(item['name'])))

        _frameworks = json.loads(frameworks) if frameworks is not None else []
        for item in _frameworks:
            oekg.add((study_URI, OEO["has_framework"], Literal(item['name'])))

        for s, p, o in oekg.triples((study_URI, OEO.OEO_00000506, None)):
            oekg.remove((s, p, o))

        _authors = json.loads(authors) if authors is not None else []
        for item in _authors:
            author_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + item['iri'])
            oekg.add((study_URI, OEO.OEO_00000506, author_URI))

        for s, p, o in oekg.triples((study_URI, OEO["has_study_keyword"], None)):
            oekg.remove((s, p, o))
        _study_keywords = json.loads(study_keywords) if study_keywords is not None else []
        for keyword in _study_keywords:
            oekg.add(( study_URI, OEO["has_study_keyword"], Literal(keyword) ))

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

    uid = request.GET.get('id')
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + uid)
    factsheet = {}

    acronym = ''
    study_name = ''
    abstract = ''
    report_title = ''
    date_of_publication = '01-01-1900'
    place_of_publication = ''
    link_to_study = ''
    report_doi = ''

    for s, p, o in oekg.triples(( study_URI, DC.acronym, None )):
        acronym = o
    
    for s, p, o in oekg.triples(( study_URI, OEKG["has_full_name"], None )):
        study_name = o

    for s, p, o in oekg.triples((  study_URI, DC.abstract, None )):
        abstract = o

    #for s, p, o in oekg.triples(( study_URI, OEKG["report_title"], None )):
    report_title = ''

    for s, p, o in oekg.triples(( study_URI, OEKG["date_of_publication"], None )):
        date_of_publication = o

    for s, p, o in oekg.triples(( study_URI, OEKG["place_of_publication"], None )):
        place_of_publication = o

    for s, p, o in oekg.triples(( study_URI, OEKG["link_to_study"], None )):
        link_to_study = o

    for s, p, o in oekg.triples(( study_URI, OEKG["doi"], None )):
        report_doi = o

    factsheet['acronym'] = acronym
    factsheet['uid'] = uid
    factsheet['study_name'] = study_name
    factsheet['abstract'] = abstract
    factsheet['report_title'] = report_title
    factsheet['date_of_publication'] = date_of_publication
    factsheet['place_of_publication'] = place_of_publication
    factsheet['link_to_study'] = link_to_study
    factsheet['report_doi'] = report_doi

    factsheet['funding_sources'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000509, None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['funding_sources'].append({ "iri": str(o).split("/")[-1], "id": label, "name": label })
   
    factsheet['institution'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000510, None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['institution'].append({ "iri": str(o).split("/")[-1], "id": label, "name": label })

    factsheet['contact_person'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000508, None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['contact_person'].append({ "iri": str(o).split("/")[-1], "id": label, "name": label })

    factsheet['sector_divisions'] = []
    for s, p, o in oekg.triples(( study_URI, OEO["based_on_sector_division"], None )):
        label = oeo.value(o, RDFS.label)
        class_iri = o
        if label != None:
            factsheet['sector_divisions'].append({ 'value': label, 'name': label, 'class': class_iri })

    factsheet['sectors'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000505, None )):
        label = oeo.value(o, RDFS.label)
        class_iri = o
        if label != None:
            factsheet['sectors'].append({  "value": label, "label":label, 'class': class_iri })

    factsheet['energy_carriers'] = []
    for s, p, o in oekg.triples(( study_URI, OEO["covers_energy_carrier"], None )):
        label = oeo.value(o, RDFS.label)
        class_label = oeo.value(o, RDFS.label)
        if label != None:
            factsheet['energy_carriers'].append({ "value": label, "label":label, "class": o })

    factsheet['energy_transformation_processes'] = []
    for s, p, o in oekg.triples(( study_URI, OEO["covers_transformation_processes"], None )):
        label = oeo.value(o, RDFS.label)
        if label != None:
            factsheet['energy_transformation_processes'].append({ "value": label, "label":label, "class": o })

    factsheet['authors'] = []
    for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000506, None )):
        label = oekg.value(o, RDFS.label)
        if label != None:
            factsheet['authors'].append({ "iri": str(o).split("/")[-1], "id": label, "name": label })

    factsheet['study_keywords'] = []
    for s, p, o in oekg.triples(( study_URI, OEO["has_study_keyword"], None )):
        if o != None:
            factsheet['study_keywords'].append(o)

    factsheet['models'] = []
    factsheet['frameworks'] = []

    for s, p, o in oekg.triples(( study_URI, OEO["has_framework"], None )):
        factsheet['frameworks'].append({ "id": o, "name": o })
    
    for s, p, o in oekg.triples(( study_URI, OEO["has_model"], None )):
        factsheet['models'].append({ "id": o, "name": o })

    factsheet['scenarios'] = []
    for s, p, o in oekg.triples(( study_URI, OEKG['has_scenario'], None )):
        scenario = {}
        label = oekg.value(o, RDFS.label)
        scenario_uuid = oekg.value(o, OEKG['scenario_uuid'])

        if label != None:
            scenario['acronym'] = label
        
        scenario['id'] = scenario_uuid
        scenario['scenario_years'] = []
        scenario['regions'] = []
        scenario['interacting_regions'] = []
        scenario['keywords'] = []
        scenario['input_datasets'] = []
        scenario['output_datasets'] = []

        abstract = oekg.value(o, DC.abstract)
        name = oekg.value(o, OEKG["has_full_name"])
        scenario['name'] = name
        scenario['abstract'] = abstract

        for s1, p1, o1 in oekg.triples(( o, OEO.OEO_00000522, None )):
            o1_type = oekg.value(o1, RDF.type)
            o1_label = oekg.value(o1, RDFS.label)
            if (o1_type == OBO.BFO_0000006):
                scenario['regions'].append({  "iri":str(o1).split("/")[-1], 'id': o1_label, 'name': o1_label})
            if (o1_type == OEO.OEO_00020036):
                scenario['interacting_regions'].append({ "iri":str(o1).split("/")[-1], 'id': o1_label, 'name': o1_label})
        
        for s11, p11, o11 in oekg.triples(( o, OEO["has_scenario_descriptor"], None )):
            scenario['keywords'].append(o11)

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
        
        for s4, p4, o4 in oekg.triples(( o, OEO.OEO_00020224, None )):
            scenario['scenario_years'].append({'id': o4, 'name': o4})

        factsheet['scenarios'].append(scenario)

    response = JsonResponse(factsheet, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    return response

@csrf_exempt
def query_oekg(request, *args, **kwargs):
    request_body = json.loads(request.body)
    criteria = request_body['criteria']

    institutes_list = criteria['institutions']
    authors_list = criteria['authors']
    funding_sources_list = criteria['fundingSource']
    publication_date_start_value = criteria['startDateOfPublication']
    publication_date_end_value = criteria['endDateOfPublication']
    study_keywords_list = criteria['studyKewords']
    scenario_year_start_value = criteria['scenarioYearValue'][0]
    scenario_year_end_value = criteria['scenarioYearValue'][1]

    query_structure = '''
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX RDFS: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX OEO: <http://openenergy-platform.org/ontology/oeo/>
        PREFIX OEKG: <http://openenergy-platform.org/ontology/oekg/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX DC: <http://purl.org/dc/terms/>

        SELECT DISTINCT ?study_acronym 
        WHERE 
        {{
        ?s OEO:OEO_00000510 ?institutes ;
            {authors_exp}
            {funding_source_exp}
            OEKG:date_of_publication ?publication_date ;
            OEO:has_study_keyword ?study_keywords ;;
            DC:acronym ?study_acronym .

        FILTER ((?institutes IN ({institutes}) )
        || (?authors IN ({authors}) )
        || (?funding_sources IN ({funding_sources}) )
        || (?publication_date >= "{publication_date_start}"^^xsd:date && ?publication_date <= "{publication_date_end}"^^xsd:date)
        || (?study_keywords IN ({study_keywords}) ) )

        }}'''

    final_query = query_structure.format(institutes = str(institutes_list).replace('[', '').replace(']', '').replace("'", ''),
                authors = str(authors_list).replace('[', '').replace(']', '').replace("'", ''),
                funding_sources = str(funding_sources_list).replace('[', '').replace(']', '').replace("'", ''),
                publication_date_start = publication_date_start_value,
                publication_date_end = publication_date_end_value,
                study_keywords = str(study_keywords_list).replace('[', '').replace(']', ''),
                scenario_year_start = scenario_year_start_value ,
                scenario_year_end = scenario_year_end_value,
                funding_source_exp = "OEO:OEO_00000509 ?funding_sources ;" if funding_sources_list != [] else "",
                authors_exp = "OEO:OEO_00000506 ?authors ;" if authors_list != [] else ""
                )

    print(final_query)
    
    sparql.setReturnFormat(JSON)
    sparql.setQuery(final_query)
    results = sparql.query().convert()

    response = JsonResponse(results["results"]["bindings"], safe=False, content_type='application/json')
    return response

@csrf_exempt
def delete_factsheet_by_id(request, *args, **kwargs):
    id = request.GET.get('id')
    study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + id)
    print(study_URI)
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
        entities.append({ "name": sl, "id": sl, "iri":str(s).split("/")[-1] })

    response = JsonResponse(entities, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response


@csrf_exempt
def add_entities(request, *args, **kwargs):
    request_body = json.loads(request.body)
    entity_type = request_body['entity_type']
    entity_label = request_body['entity_label']
    entity_iri = request_body['entity_iri']

    vocab = entity_type.split('.')[0]
    classId = entity_type.split('.')[1]
    prefix = ''
    if vocab == 'OEO':
        prefix = "http://openenergy-platform.org/ontology/oeo/"
    if vocab == 'OBO':
        prefix = "http://purl.obolibrary.org/obo/"

    entity_type_URI = URIRef(prefix + classId)

    entity_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + entity_iri )

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
    entity_id = request_body['entity_iri']

    vocab = entity_type.split('.')[0]
    classId = entity_type.split('.')[1]
    prefix = ''
    if vocab == 'OEO':
        prefix = "http://openenergy-platform.org/ontology/oeo/"
    if vocab == 'OBO':
        prefix = "http://purl.obolibrary.org/obo/"

    entity_type_URI = URIRef(prefix + classId)
    entity_IRI = URIRef("http://openenergy-platform.org/ontology/oekg/" + (entity_id) )

    oekg.add((entity_IRI, RDFS.label, Literal(new_entity_label)))
    oekg.remove((entity_IRI, RDFS.label, Literal(entity_label)))

    response = JsonResponse('entity updated!', safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def get_all_factsheets(request, *args, **kwargs):
    all_factsheets = []
    for s, p, o in oekg.triples(( None, RDF.type, OEO.OEO_00010252 )):
        uid = str(s).split("/")[-1]
        element = {}
        acronym = oekg.value(s, DC.acronym)
        study_name = oekg.value(s, OEKG["has_full_name"]) 
        abstract = oekg.value(s, DC.abstract) 
        element['uid'] =  uid
        element['acronym'] =  acronym if acronym != None else ''
        element['study_name'] = study_name if study_name != None else '' 
        element['abstract'] = abstract if abstract != None else ''
        study_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + uid)
        element['institutions'] = []
        for s, p, o in oekg.triples(( study_URI, OEO.OEO_00000510, None )):
            label = oekg.value(o, RDFS.label)
            if label != None:
                element['institutions'].append(label)
        element['scenarios'] = []
        
        element['date_of_publication'] = oekg.value(study_URI,OEKG["date_of_publication"])
        for s, p, o in oekg.triples(( study_URI, OEKG['has_scenario'], None )):
            label = oekg.value(o, RDFS.label)
            if label != None:
                element['scenarios'].append(label)

        all_factsheets.append(element)

    response = JsonResponse(all_factsheets, safe=False, content_type='application/json') 
    patch_response_headers(response, cache_timeout=1)
    return response

@csrf_exempt
def get_scenarios(request, *args, **kwargs):
    scenarios_acronym = [i.replace('%20', ' ') for i in  json.loads(request.GET.get('scenarios_acronym'))]

    scenarios = []
    print(scenarios_acronym)

    for s, p, o in oekg.triples(( None, RDF.type, OEO.OEO_00000365 )):
        print(str(oekg.value(s, RDFS.label) ))
        if str(oekg.value(s, RDFS.label) ) in scenarios_acronym:
            descriptors = []
            regions = []
            interacting_regions = []
            scenario_years = []
            input_datasets = []
            output_datasets = []
            for s1, p1, o1 in oekg.triples(( s, OEO['has_scenario_descriptor'], None )):
                descriptors.append(o1)
            for s2, p2, o2 in oekg.triples(( s, OEO.OEO_00000522, None )):
                regions.append(oekg.value(o2, RDFS.label))
            for s3, p3, o3 in oekg.triples(( s, OEO['covers_interacting_regions'], None )):
                interacting_regions.append(oekg.value(o3, RDFS.label))
            for s4, p4, o4 in oekg.triples(( s, OEO.OEO_00020224, None )):
                scenario_years.append(o4)
            for s5, p5, o5 in oekg.triples(( s, OEO.RO_0002233, None )):
                input_datasets.append(oekg.value(o5, RDFS.label))
            for s6, p6, o6 in oekg.triples(( s, OEO.RO_0002234, None )):
                output_datasets.append(oekg.value(o6, RDFS.label))
                

            scenarios.append({ 'acronym' : oekg.value(s, RDFS.label), 'data': { 
                'descriptors': descriptors, 
                'regions': regions, 
                'interacting_regions': interacting_regions, 
                'scenario_years': scenario_years,
                'input_datasets': input_datasets,
                'output_datasets': output_datasets 
                } })

    response = JsonResponse(scenarios, safe=False, content_type='application/json') 
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

def get_all_sub_classes(cls, visited=None):
    if visited is None:
        visited = set()

    visited.add(cls.label.first())
    #"value": cls.label.first(),  "label": cls.label.first(), , "iri": cls.iri
   
    childCount = len(list(cls.subclasses()))
    subclasses = cls.subclasses()
    value = 10 if childCount > 5 else 500

    dict = { "name": cls.label.first(),  "label": cls.label.first(), "value": cls.label.first(), "iri": cls.iri}

    if childCount > 0:
      dict["children"] = [get_all_sub_classes(subclass, visited) for subclass in subclasses if subclass.label.first() not in visited ]
    return dict


@csrf_exempt
def populate_factsheets_elements(request, *args, **kwargs):

    energy_carrier_class = oeo_owl.search_one(iri="http://openenergy-platform.org/ontology/oeo/OEO_00020039")
    energy_carriers = get_all_sub_classes(energy_carrier_class)

    energy_transformation_process_class = oeo_owl.search_one(iri="http://openenergy-platform.org/ontology/oeo/OEO_00020003")
    energy_transformation_processes = get_all_sub_classes(energy_transformation_process_class)
    

    sector_divisions = ['OEO_00010056', 'OEO_00000242', 'OEO_00010304']

    sector_divisions_list = []
    sectors_list = []
    for sd in sector_divisions:
        sector_division_URI = URIRef("http://openenergy-platform.org/ontology/oeo/" + sd)
        sector_division_label = oeo.value(sector_division_URI, RDFS.label)
        sector_divisions_list.append({'class': sector_division_URI, 'label': sector_division_label, 'name': sector_division_label, 'value': sector_division_label})
        for s, p, o in oeo.triples(( None, OEO.OEO_00000504, OEO[sd] )):
            sector_label = oeo.value(s, RDFS.label)
            sectors_list.append({'iri': s, 'label': sector_label, 'value': sector_label, 'sector_division': sector_division_URI})

    elements = {}
    elements['energy_carriers'] = [energy_carriers]
    elements['energy_transformation_processes'] = [energy_transformation_processes]
    elements['sector_divisions'] = sector_divisions_list
    elements['sectors'] = sectors_list

    # for s, p, o in oeo.triples(( None, RDFS.subClassOf, OEO.OEO_00020003 )):
    #     sl = oeo.value(s, RDFS.label)
    #     parent = {
    #         'value': str(sl),
    #         'label': sl,
    #         'class': s
    #     }
    #     children = []
    #     for s1, p, o in oeo.triples(( None, RDFS.subClassOf, s )):
    #         sl1 = oeo.value(s1, RDFS.label)
    #         children2 = []
    #         for s2, p, o in oeo.triples(( None, RDFS.subClassOf, s1 )):
    #             sl2 = oeo.value(s2, RDFS.label)
    #             children3 = []
    #             for s3, p, o in oeo.triples(( None, RDFS.subClassOf, s2 )):
    #                 sl3 = oeo.value(s3, RDFS.label)
    #                 children3.append({
    #                     'value': str(sl) + str(sl1) + str(sl2) + str(sl3),
    #                     'label': sl3,
    #                     'class': s3
    #                 })

    #             if children3 != []:
    #                 children2.append({
    #                     'value': str(sl) + str(sl1) + str(sl2),
    #                     'label': sl2,
    #                     'class': s2,
    #                     'children': children3
    #                 })
    #             else:
    #                 children2.append({
    #                     'value': str(sl) + str(sl1) + str(sl2),
    #                     'class': s2,
    #                     'label': sl2,
    #                 })


    #         if children2 != []:
    #             children.append({
    #             'value': str(sl) + str(sl1),
    #             'label': sl1,
    #             'class': s1,
    #             'children': children2
    #             })
    #         else:
    #             children.append({
    #             'value': str(sl) + str(sl1),
    #             'class': s1,
    #             'label': sl1
    #             })


    #     if children != []:
    #         parent['children'] = children

    #     energy_transformation_processes.append(parent)

    

    # energy_carriers = []
    # for s, p, o in oeo.triples(( None, RDFS.subClassOf, OEO.OEO_00020039 )):
    #     sl = oeo.value(s, RDFS.label)
    #     parent = {
    #         'value': str(sl),
    #         'label': sl,
    #         'class': s
    #     }
    #     children = []
    #     for s1, p, o in oeo.triples(( None, RDFS.subClassOf, s )):
    #         sl1 = oeo.value(s1, RDFS.label)
    #         children2 = []
    #         for s2, p, o in oeo.triples(( None, RDFS.subClassOf, s1 )):
    #             sl2 = oeo.value(s2, RDFS.label)
    #             children3 = []
    #             for s3, p, o in oeo.triples(( None, RDFS.subClassOf, s2 )):
    #                 sl3 = oeo.value(s3, RDFS.label)
    #                 children3.append({
    #                     'value': str(sl) + "^^" + str(sl1) + "^^" + str(sl2) + "^^" + str(sl3),
    #                     'label': sl3,
    #                     'class': s3
    #                 })

    #             if children3 != []:
    #                 children2.append({
    #                     'value': str(sl) + "^^" + str(sl1) + "^^" + str(sl2),
    #                     'label': sl2,
    #                     'class': s2,
    #                     'children': children3
    #                 })
    #             else:
    #                 children2.append({
    #                     'value': str(sl) + "^^" + str(sl1) + "^^" + str(sl2),
    #                     'label': sl2,
    #                 })


    #         if children2 != []:
    #             children.append({
    #             'value': str(sl) + "^^" + str(sl1),
    #             'label': sl1,
    #             'class': s1,
    #             'children': children2
    #             })
    #         else:
    #             children.append({
    #             'value': str(sl) + "^^" + str(sl1),
    #             'class': s1,
    #             'label': sl1
    #             })

    #     if children != []:
    #         parent['children'] = children

    #     energy_carriers.append(parent)


    response = JsonResponse(elements, safe=False, content_type='application/json')
    patch_response_headers(response, cache_timeout=1)

    return response

    
