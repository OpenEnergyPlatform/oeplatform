# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
from collections import defaultdict
from pathlib import Path

from django.http import Http404
from rdflib import Graph

from oeplatform.settings import OEO_EXT_NAME, ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME


def get_ontology_version(path, version=None):
    if not path.exists():
        raise Http404

    versions = os.listdir(path)
    versions.remove(".DS_Store")
    if not version:
        version = max(
            (d for d in versions), key=lambda d: [int(x) for x in d.split(".")]
        )

    return version


def collect_modules(path):
    modules = dict()

    for file in os.listdir(path):
        if not os.path.isdir(os.path.join(path, file)):
            match = re.match(r"^(?P<filename>.*)\.(?P<extension>\w+)$", file)
            filename, extension = match.groups()
            if filename not in modules:
                modules[filename] = dict(extensions=[], comment="No description found")
            if extension == "owl":
                g = Graph()
                g.parse(os.path.join(path, file))

                # Set the namespaces in the graph
                for prefix, uri in g.namespaces():
                    g.bind(prefix, uri)

                # Extract the description from the RDF graph (rdfs:comment)
                comment_query = f"""
                    SELECT ?description
                    WHERE {{
                        ?ontology rdf:type owl:Ontology .
                        ?ontology rdfs:comment ?description .
                    }}
                """  # noqa
                # Execute the SPARQL query for comment
                comment_results = g.query(comment_query)

                # Update the comment in the modules dictionary if found
                for row in comment_results:
                    modules[filename]["comment"] = row[0]

                # If the comment is still "No description found," try
                # extracting from dc:description
                if modules[filename]["comment"] == "No description found":
                    description_query = f"""
                        SELECT ?description
                        WHERE {{
                            ?ontology rdf:type owl:Ontology .
                            ?ontology dc:description ?description .
                        }}
                    """  # noqa
                    # Execute the SPARQL query for description
                    description_results = g.query(description_query)

                    # Update the comment in the modules dictionary if found
                    for row in description_results:
                        modules[filename]["comment"] = row[0]

            modules[filename]["extensions"].append(extension)
    return modules


def read_oeo_context_information(path, file, ontology=None):
    Ontology_URI = path / file
    g = Graph()
    g.parse(Ontology_URI.as_posix())

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

    ontology_description = ""
    for row in q_main_description:
        if row.s.split("/")[-1] == "":
            ontology_description = row.o

    if ontology in [OPEN_ENERGY_ONTOLOGY_NAME]:
        q_definition = g.query(
            """
            SELECT DISTINCT ?s ?o
            WHERE { ?s obo:IAO_0000115 ?o }
            """
        )

        q_note = g.query(
            """
            SELECT DISTINCT ?s ?o
            WHERE { ?s obo:IAO_0000116 ?o }
            """
        )

        classes_definitions = defaultdict(list)
        for row in q_definition:
            class_name = row.s.split("/")[-1]
            classes_definitions[class_name].append(row.o)

        classes_notes = defaultdict(list)
        for row in q_note:
            class_name = row.s.split("/")[-1]
            classes_notes[class_name].append(row.o)

    else:
        classes_definitions = defaultdict(list)
        classes_notes = defaultdict(list)

    result = {
        "q_global": q_global,
        "classes_name": classes_name,
        "classes_definitions": dict(classes_definitions),
        "classes_notes": dict(classes_notes),
        "ontology_description": ontology_description,
    }

    return result


def get_common_data(ontology, file="oeo-full.owl", version=None, path=None):
    if ontology in [OEO_EXT_NAME]:
        version = "1.0.0"  # TODO remove this
    else:
        onto_base_path = Path(ONTOLOGY_ROOT, ontology)
        version = get_ontology_version(onto_base_path, version=version)

    if not path:
        onto_base_path = Path(ONTOLOGY_ROOT, ontology)
        path = onto_base_path / version
    oeo_context_data = read_oeo_context_information(
        path=path, file=file, ontology=ontology
    )

    return {
        "ontology": ontology,
        "version": version,
        "path": path,
        "oeo_context_data": oeo_context_data,
    }
