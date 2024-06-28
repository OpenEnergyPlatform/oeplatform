import os
from pathlib import Path

from owlready2 import get_ontology
from rdflib import Graph
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from rdflib.plugins.stores import sparqlstore

# from datetime import date
from SPARQLWrapper import SPARQLWrapper

from oeo_ext.oekb.namespaces import bind_all_namespaces
from oeplatform.settings import ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME, RDF_DATABASES

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
query_endpoint = "http://%(host)s:%(port)s/%(name)s/query" % rdfdb
update_endpoint = "http://%(host)s:%(port)s/%(name)s/update" % rdfdb

sparql = SPARQLWrapper(query_endpoint)

store = sparqlstore.SPARQLUpdateStore()

store.open((query_endpoint, update_endpoint))
oekb_oeo_ext = Graph(store, identifier=default)

oekb_with_namespaces = bind_all_namespaces(oekb_oeo_ext)
