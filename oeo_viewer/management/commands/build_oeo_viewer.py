# SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

import json
import os
import subprocess as sp
from collections import defaultdict

from django.apps import apps
from django.core.management.base import BaseCommand
from rdflib import Graph
from rdflib.namespace import Namespace

from oeplatform.settings import ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME

_OEO_OWL_FILE = "oeo-full.owl"


def execute(cmd, cwd):
    """run os command

    Args:
        cmd (list): command and arguments as list
        cwd (str): path to work directory

    """
    proc = sp.run(cmd, cwd=cwd)
    assert proc.returncode == 0


class Command(BaseCommand):
    help = "build oeo viewer web app in static"

    def handle(self, *args, **options):
        OEO = Namespace("http://openenergy-platform.org/ontology/oeo/")
        OBO = Namespace("http://purl.obolibrary.org/obo/")
        DC = Namespace("http://purl.org/dc/terms/")
        RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        NPG = Namespace("http://ns.nature.com/terms/")
        SCHEMA = Namespace("https://schema.org/")
        OEKG = Namespace("http://openenergy-platform.org/ontology/oekg/")
        DBO = Namespace("http://dbpedia.org/ontology/")

        versions = os.listdir(f"{ONTOLOGY_ROOT}/{OPEN_ENERGY_ONTOLOGY_NAME}")
        version = max(
            (d for d in versions), key=lambda d: [int(x) for x in d.split(".")]
        )

        path = f"{ONTOLOGY_ROOT}/{OPEN_ENERGY_ONTOLOGY_NAME}/{version}"

        Ontology_URI = os.path.join(path, _OEO_OWL_FILE)

        g = Graph()

        g.bind("oeo", OEO)
        g.bind("obo", OBO)
        g.bind("dc", DC)
        g.bind("rdfs", RDFS)
        g.bind("npg", NPG)
        g.bind("schema", SCHEMA)
        g.bind("oekg", OEKG)
        g.bind("dbo", DBO)

        g.parse(Ontology_URI)

        q_global = g.query(
            """
            SELECT DISTINCT ?s ?o
            WHERE { ?s rdfs:subClassOf ?o
            filter(!isBlank(?o))
            }
            """
        )

        q_label = g.query(
            """
            SELECT DISTINCT ?s ?o
            WHERE { ?s rdfs:label ?o }
            """
        )

        q_definition = g.query(
            """
            PREFIX obo: <http://purl.obolibrary.org/obo/>
            SELECT DISTINCT ?s ?o
            WHERE { ?s obo:IAO_0000115 ?o }
            """
        )

        q_note = g.query(
            """
            PREFIX obo: <http://purl.obolibrary.org/obo/>
            SELECT DISTINCT ?s ?o
            WHERE { ?s obo:IAO_0000116 ?o }
            """
        )

        q_main_description = g.query(
            """
            SELECT ?s ?o
            WHERE { ?s dc:description ?o }
            """
        )

        classes_name = {}
        for row in q_label:
            class_name = row.s.split("/")[-1]
            classes_name[class_name] = row.o

        classes_definitions = defaultdict(list)
        for row in q_definition:
            class_name = row.s.split("/")[-1]
            classes_definitions[class_name].append(row.o)

        classes_notes = defaultdict(list)
        for row in q_note:
            class_name = row.s.split("/")[-1]
            classes_notes[class_name].append(row.o)

        # TODO: noqa F841:variable assigned to but never used
        ontology_description = ""  # noqa: F841
        for row in q_main_description:
            if row.s.split("/")[-1] == "":
                # noqa F841: TODO: variable assigned to but never used
                ontology_description = row.o  # noqa: F841

        # Begin prepare data for oeo-viewer. Only need to be executed once per release
        graphLinks = []
        graphNodes = []

        for row in q_global:
            source = row.o.split("/")[-1]
            target = row.s.split("/")[-1]

            # if source in classes_name.keys() and target in classes_name.keys():
            graphLinks.append({"source": source, "target": target})

            target_found = False
            source_found = False

            for item in graphNodes:
                if item["id"] == target:
                    target_found = True
                if item["id"] == source:
                    source_found = True

            try:
                if not target_found:
                    graphNodes.append(
                        {
                            "id": target,
                            "name": classes_name[target],
                            "description": classes_definitions[target],
                            "editor_note": classes_notes[target],
                        }
                    )

                if not source_found:
                    graphNodes.append(
                        {
                            "id": source,
                            "name": classes_name[source],
                            "description": classes_definitions[source],
                            "editor_note": classes_notes[source],
                        }
                    )
            except Exception:
                pass

        # static_path = settings.STATIC_ROOT
        # oeo_viewer_data_path = os.path.join(static_path, 'oeo_viewer')

        app_config = apps.get_app_config("oeo_viewer")
        app_path = app_config.path

        oeo_viewer_data_path = os.path.join(app_path, "data")
        oeo_viewer_data_file = "oeo_viewer_json_data.json"

        oeo_viewer_file_path = os.path.join(oeo_viewer_data_path, oeo_viewer_data_file)

        with open(oeo_viewer_file_path, "w", encoding="utf-8") as f:
            json.dump({"nodes": graphNodes, "links": graphLinks}, f)

        print("The data for OEO viewer app has been created successfully!")

        pwd = os.path.join(os.path.dirname(__file__), "..", "..", "client")
        # execute(["npm", "install", "--legacy-peer-deps", "--no-save"], cwd=pwd)
        execute(["npm", "run", "build"], cwd=pwd)

        print("The OEO viewer app has been compiled and deployed successfully!")
