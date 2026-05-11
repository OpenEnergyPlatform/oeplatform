"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from django.http import Http404
from rdflib import Graph
from rdflib.namespace import DC, OWL, RDF, RDFS
from rdflib.query import ResultRow

from oeplatform.settings import OEO_EXT_NAME, ONTOLOGY_ROOT, OPEN_ENERGY_ONTOLOGY_NAME

# Use your project's custom logger
logger = logging.getLogger("oeplatform")


def get_ontology_version(path, version=None):
    if not path.exists():
        raise Http404

    versions = os.listdir(path)
    if not version:
        version = max(
            (d for d in versions), key=lambda d: [int(x) for x in d.split(".")]
        )

    return version


def _extract_description_fast(g):
    """
    Extracts the ontology description using direct graph traversal instead of SPARQL.

    This method is significantly faster for initial cache-building as it avoids
    the overhead of compiling and executing SPARQL queries. It searches for a node
    declared as an owl:Ontology and attempts to find its rdfs:comment or
    dc:description.

    Args:
        g (rdflib.Graph): The parsed RDF graph of the ontology module.

    Returns:
        str: The extracted description/comment, or a fallback string
             ("No description found") if neither property exists.
    """
    # Find the subject node that is declared as an owl:Ontology
    ontology_node = g.value(predicate=RDF.type, object=OWL.Ontology)

    if ontology_node:
        # Try finding rdfs:comment
        comment = g.value(subject=ontology_node, predicate=RDFS.comment)
        if comment:
            return str(comment)

        # Try finding dc:description
        description = g.value(subject=ontology_node, predicate=DC.description)
        if description:
            return str(description)

    return "No description found"


def collect_modules(path_str):
    """
    Scans a directory for ontology modules, parses them, and extracts their metadata.

    Iterates through all files in the given directory. For files with an '.owl'
    extension, it attempts to parse them as RDF/XML and extract their description.
    Errors during parsing (e.g., due to invalid XML/RDF formats like idranges.owl)
    are caught and logged, preventing application crashes.

    Args:
        path_str (str or os.PathLike): The directory path containing the ontology
        files.

    Returns:
        dict: A dictionary where keys are the module filenames (without extension)
              and values are dictionaries containing:
              - "extensions" (list of str): List of file extensions found for this
                module.
              - "comment" (str): The description extracted from the ontology graph.

              Example:
              {
                  "oeo-core": {
                      "extensions": ["owl"],
                      "comment": "The core module of the Open Energy Ontology."
                  }
              }
    """
    modules = {}
    target_path = Path(path_str)

    # Safety check in case the directory doesn't exist yet
    if not target_path.exists():
        return modules

    for file_path in target_path.iterdir():
        # Skip directories
        if file_path.is_dir():
            continue

        # Extract filename (e.g., 'oeo-core') and extension without the dot
        # (e.g., 'owl')
        filename = file_path.stem
        extension = file_path.suffix.lstrip(".")

        # Initialize the module dict if it doesn't exist yet
        module_info = modules.setdefault(
            filename, {"extensions": [], "comment": "No description found"}
        )

        module_info["extensions"].append(extension)

        if extension == "owl":
            try:
                g = Graph()
                # Parsing the XML is the only "slow" part left, but unavoidable
                g.parse(str(file_path))

                # Replaces SPARQL queries with the fast extraction method
                description = _extract_description_fast(g)
                if description != "No description found":
                    module_info["comment"] = description

            except Exception as e:
                # Catches ExpatErrors and prevents 500 Server Errors
                logger.warning(
                    f"Failed to parse ontology file '{file_path.name}'. Error: {e}"
                )

    return modules


def read_oeo_context_information(path, file, ontology=None):
    Ontology_URI = path / file
    g = Graph()
    g.parse(Ontology_URI.as_posix())

    q_global = g.query("""
        SELECT DISTINCT ?s ?o
        WHERE { ?s rdfs:subClassOf ?o
        filter(!isBlank(?o))
        }
        """)

    q_label: Iterable[ResultRow] = g.query("""
        SELECT DISTINCT ?s ?o
        WHERE { ?s rdfs:label ?o }
        """)  # type: ignore

    q_main_description: Iterable[ResultRow] = g.query("""
        SELECT ?s ?o
        WHERE { ?s dc:description ?o }
        """)  # type: ignore

    classes_name = {}
    for row in q_label:
        class_name = row.s.split("/")[-1]
        classes_name[class_name] = row.o

    ontology_description = ""
    for row in q_main_description:
        if row.s.split("/")[-1] == "":
            ontology_description = row.o

    if ontology in [OPEN_ENERGY_ONTOLOGY_NAME]:
        q_definition: Iterable[ResultRow] = g.query("""
            SELECT DISTINCT ?s ?o
            WHERE { ?s obo:IAO_0000115 ?o }
            """)  # type: ignore

        q_note: Iterable[ResultRow] = g.query("""
            SELECT DISTINCT ?s ?o
            WHERE { ?s obo:IAO_0000116 ?o }
            """)  # type: ignore

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
