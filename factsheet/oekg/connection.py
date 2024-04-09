import logging

from rdflib import Graph, Literal, RDF, URIRef
from rdflib.plugins.stores import sparqlstore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
import os

# from datetime import date
from SPARQLWrapper import SPARQLWrapper
import sys
from owlready2 import get_ontology
from pathlib import Path

from oeplatform.settings import (
    ONTOLOGY_ROOT,
    RDF_DATABASES,
    OPEN_ENERGY_ONTOLOGY_NAME,
    DEBUG,
)
from factsheet.oekg.namespaces import bind_all_namespaces

versions = os.listdir(
    Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)
)  # TODO bad - windows dev will get path error
# Bryans custom hack!! print(versions.remove(".DS_Store"))
version = max((d for d in versions), key=lambda d: [int(x) for x in d.split(".")])
onto_base_path = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)
path = onto_base_path / version  # TODO bad - windows dev will get path error
# file = "reasoned-oeo-full.owl" # TODO- set in settings
file = "oeo-full.owl"  # TODO- set in settings

Ontology_URI = path / file
Ontology_URI_STR = Ontology_URI.as_posix()

# sys.path.append(path)

oeo = Graph()
oeo.parse(Ontology_URI.as_uri())

oeo_owl = get_ontology(Ontology_URI_STR).load()

rdfdb = RDF_DATABASES["knowledge"]
query_endpoint = "%(host)s:%(port)s/{%(name)s}/query" % rdfdb
update_endpoint = "%(host)s:%(port)s/{%(name)s}/update" % rdfdb


sparql = SPARQLWrapper(query_endpoint)

""" store = sparqlstore.SPARQLUpdateStore(
    auth=(
        RDF_DATABASES.get("factsheet").get("dbuser"), 
        RDF_DATABASES.get("factsheet").get("dbpasswd")
    )
) """


store = sparqlstore.SPARQLUpdateStore()

store.open((query_endpoint, update_endpoint))
oekg = Graph(store, identifier=default)

oekg_with_namespaces = bind_all_namespaces(oekg)
