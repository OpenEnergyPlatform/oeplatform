# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg # noqa:E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import subprocess as sp
import uuid

from django.core.management.base import BaseCommand
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from rdflib.namespace import Namespace
from rdflib.plugins.stores import sparqlstore
from SPARQLWrapper import SPARQLWrapper

# query_endpoint = "http://oekb.iks.cs.ovgu.de:3030/oekg_main/query"
# update_endpoint = "http://oekb.iks.cs.ovgu.de:3030/oekg_main/update"

query_endpoint = "http://localhost:3030/ds/query"
update_endpoint = "http://localhost:3030/ds/update"

sparql = SPARQLWrapper(query_endpoint)

store = sparqlstore.SPARQLUpdateStore()
store.open((query_endpoint, update_endpoint))
oekg = Graph(store, identifier=default)


OEO = Namespace("https://openenergyplatform.org/ontology/oeo/")
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


def execute(cmd, cwd):
    proc = sp.run(cmd, cwd=cwd)
    assert proc.returncode == 0


class Command(BaseCommand):
    def handle(self, *args, **options):
        all_bundles_uids = []
        for s, p, o in oekg.triples((None, RDF.type, OEO.OEO_00010252)):
            uid = str(s).split("/")[-1]
            all_bundles_uids.append(uid)

        for uid in all_bundles_uids:
            bundle_URI = URIRef("http://openenergy-platform.org/ontology/oekg/" + uid)

            if (bundle_URI, OEKG["report_title"], None) in oekg:
                publication_uuid = str(uuid.uuid4())
                publications_URI = URIRef(
                    "http://openenergy-platform.org/ontology/oekg/publication/"
                    + publication_uuid
                )

                oekg.add(
                    (
                        publications_URI,
                        OEKG["publication_uuid"],
                        Literal(publication_uuid),
                    )
                )

                for s, p, o in oekg.triples((bundle_URI, OEKG["report_title"], None)):
                    oekg.add((publications_URI, RDFS.label, o))

                for s, p, o in oekg.triples(
                    (bundle_URI, OEKG["date_of_publication"], None)
                ):
                    oekg.add(
                        (
                            publications_URI,
                            OEKG["date_of_publication"],
                            o,
                        )
                    )

                for s, p, o in oekg.triples(
                    (bundle_URI, OEKG["place_of_publication"], None)
                ):
                    oekg.add(
                        (
                            publications_URI,
                            OEKG["place_of_publication"],
                            o,
                        )
                    )

                for s, p, o in oekg.triples((bundle_URI, OEKG["link_to_study"], None)):
                    oekg.add(
                        (
                            publications_URI,
                            OEKG["link_to_study"],
                            o,
                        )
                    )

                for s, p, o in oekg.triples((bundle_URI, OEKG["doi"], None)):
                    oekg.add((publications_URI, OEO.OEO_00390098, o))

                for s, p, o in oekg.triples((bundle_URI, OEO.OEO_00000506, None)):
                    oekg.add((publications_URI, OEO.OEO_00000506, o))

                oekg.add((bundle_URI, OEKG["has_publication"], publications_URI))

                print(
                    "The bundle with id {id} has been updated to handle multiple publications!".format(  # noqa:E501
                        id=uid
                    )
                )
            else:
                print(
                    "The bundle with id {id} did not have any publication!".format(
                        id=uid
                    )
                )
