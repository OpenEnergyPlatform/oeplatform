from pathlib import Path

from owlready2 import get_ontology
from rdflib import Graph
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from rdflib.plugins.stores import sparqlstore

# from datetime import date
from SPARQLWrapper import SPARQLWrapper

from oeo_ext.oekb.namespaces import bind_all_namespaces
from oeplatform.settings import (
    OEO_EXT_OWL_PATH,
    ONTOLOGY_ROOT,
    OPEN_ENERGY_ONTOLOGY_FULL_OWL_NAME,
    OPEN_ENERGY_ONTOLOGY_NAME,
    RDF_DATABASES,
)
from ontology.utils import get_ontology_version

OEO_BASE_PATH = Path(ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME)
OEO_VERSION = get_ontology_version(OEO_BASE_PATH)
OEO_PATH = OEO_BASE_PATH / OEO_VERSION  # TODO bad - windows dev will get path error

########################################################
#                           oeo                     ####
########################################################
Ontology_URI = OEO_PATH / OPEN_ENERGY_ONTOLOGY_FULL_OWL_NAME
Ontology_URI_STR = Ontology_URI.as_posix()

oeo = Graph()
oeo.parse(Ontology_URI.as_uri())

oeo_owl = get_ontology(Ontology_URI_STR).load()

########################################################
#                 oeo extended                      ####
########################################################

oeo_ext = Graph()
oeo_ext.parse(OEO_EXT_OWL_PATH.as_uri())
oeo_ext_owl = get_ontology(OEO_EXT_OWL_PATH.as_posix()).load()


########################################################
#           oeo/oeo_ext SPARQL endpoints               #
########################################################

rdfdb = RDF_DATABASES["knowledge"]
oeo_query_endpoint = "http://%(host)s:%(port)s/%(name)s/query" % rdfdb
oeo_update_endpoint = "http://%(host)s:%(port)s/%(name)s/update" % rdfdb

oeo_sparql = SPARQLWrapper(oeo_query_endpoint)

oeo_store = sparqlstore.SPARQLUpdateStore()

oeo_store.open((oeo_query_endpoint, oeo_update_endpoint))
oekb_oeo = Graph(oeo_store, identifier=default)

# ---- import this in other modules
oekb_with_namespaces = bind_all_namespaces(oekb_oeo)

rdfdb = RDF_DATABASES["oeo_ext"]
oeo_ext_query_endpoint = "http://%(host)s:%(port)s/%(name)s/query" % rdfdb
oeo_ext_update_endpoint = "http://%(host)s:%(port)s/%(name)s/update" % rdfdb

sparql = SPARQLWrapper(oeo_ext_query_endpoint)

oeo_ext_store = sparqlstore.SPARQLUpdateStore()

oeo_ext_store.open((oeo_ext_query_endpoint, oeo_ext_update_endpoint))
oekb_oeo_ext = Graph(oeo_ext_store, identifier=default)

# ---- import this in other modules
oekb_with_namespaces = bind_all_namespaces(oekb_oeo_ext)
