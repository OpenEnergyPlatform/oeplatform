# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

from rdflib.namespace import Namespace

# TODO- Alot of hardcoded URL, transfer to settings or other config
OEO = Namespace("https://openenergyplatform.org/ontology/oeo/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
DC = Namespace("http://purl.org/dc/terms/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
NPG = Namespace("http://ns.nature.com/terms/")
SCHEMA = Namespace("https://schema.org/")
OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
DBO = Namespace("http://dbpedia.org/ontology/")


def bind_all_namespaces(graph):
    graph.bind("OEO", OEO)
    graph.bind("OBO", OBO)
    graph.bind("DC", DC)
    graph.bind("RDFS", RDFS)
    graph.bind("NPG", NPG)
    graph.bind("SCHEMA", SCHEMA)
    graph.bind("OEKG", OEKG)
    graph.bind("DBO", DBO)

    return graph
