# SPDX-FileCopyrightText: 2025 jh-RLI <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

import logging
from uuid import UUID

import requests
from SPARQLWrapper import JSON, POST

from factsheet.oekg.connection import sparql, sparql_wrapper_update, update_endpoint
from oekg.sparqlModels import DatasetConfig

logger = logging.getLogger("oeplatform")


def scenario_in_bundle(bundle_uuid: UUID, scenario_uuid: UUID) -> bool:
    """
    Check if a scenario is part of a scenario bundle in the KG.
    """
    sparql_query = f"""
    PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>

    ASK {{
        <http://openenergy-platform.org/ontology/oekg/{bundle_uuid}> ?p
            <http://openenergy-platform.org/ontology/oekg/scenario/{scenario_uuid}> .
    }}
    """
    sparql.setQuery(sparql_query)
    sparql.setMethod(POST)
    sparql.setReturnFormat(JSON)
    response = sparql.query().convert()

    return response.get(
        "boolean", False
    )  # Returns True if scenario is part of the bundle


def dataset_exists(scenario_uuid: UUID, dataset_url: str) -> bool:
    """
    Check if a dataset with the same label already exists.
    """

    sparql_query = f"""
    PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    ASK {{
        <http://openenergy-platform.org/ontology/oekg/scenario/{scenario_uuid}> ?p ?dataset .
        ?dataset oeo:has_iri "{dataset_url}" .
    }}

    """  # noqa

    sparql.setQuery(sparql_query)
    sparql.setMethod(POST)
    sparql.setReturnFormat(JSON)
    response = sparql.query().convert()

    return response.get("boolean", False)  # Returns True if dataset exists


def add_datasets_to_scenario(oekgDatasetConfig: DatasetConfig):
    """
    Function to add datasets to a scenario bundle in Jena Fuseki.
    """

    # Check if a dataset with the same label exists
    if dataset_exists(oekgDatasetConfig.scenario_uuid, oekgDatasetConfig.dataset_url):
        return False  # Skip insertion

    # Check: used constant string values here. Get ids from oeo
    # graph to make sure ids still exists?
    if oekgDatasetConfig.dataset_type == "input":
        rel_property = "RO_0002233"
        type_entity = "OEO_00030029"
    elif oekgDatasetConfig.dataset_type == "output":
        rel_property = "RO_0002234"
        type_entity = "OEO_00030030"

    # oeo:has_id "{oekgDatasetConfig.dataset_id}" ;
    # The above seems to be deprecated in the OEKG
    sparql_query = f"""
    PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    INSERT DATA {{
        <http://openenergy-platform.org/ontology/oekg/input_datasets/{oekgDatasetConfig.dataset_id}> a oeo:{type_entity} ;
            rdfs:label "{oekgDatasetConfig.dataset_label}" ;
            oeo:has_iri "{oekgDatasetConfig.dataset_url}" ;
            oeo:has_key "{oekgDatasetConfig.dataset_id}" .

        <http://openenergy-platform.org/ontology/oekg/scenario/{oekgDatasetConfig.scenario_uuid}> oeo:{rel_property}
            <http://openenergy-platform.org/ontology/oekg/input_datasets/{oekgDatasetConfig.dataset_id}> .
    }}
    """  # noqa

    print(sparql_query)
    # response = send_sparql_update(sparql_query)
    sparql_wrapper_update.setQuery(sparql_query)
    sparql_wrapper_update.setMethod(POST)
    sparql_wrapper_update.setReturnFormat(JSON)
    try:
        response = sparql_wrapper_update.query()
        http_response = response.response
        if not http_response.status == 200:
            return False  # Return False if any query fails
    except Exception as e:
        logger.error(f"Failed to update datasets in OEKG: {e}")
        return False

    return True


def remove_datasets_from_scenario(scenario_uuid, dataset_name, dataset_type):
    """
    Function to remove datasets from a scenario bundle in Jena Fuseki.
    """
    sparql_query = f"""
    PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
    DELETE DATA {{
        GRAPH <http://openenergy-platform.org/ontology/oekg/{scenario_uuid}> {{
            oeo:{dataset_name} a oeo:{dataset_type}Dataset .
        }}
    }}
    """
    response = send_sparql_update(sparql_query)
    if not response.ok:
        return False  # Return False if any query fails
    return True


def send_sparql_update(query):
    """
    Helper function to send a SPARQL update query to Fuseki.
    """
    headers = {"Content-Type": "application/sparql-update"}
    response = requests.post(update_endpoint, data=query, headers=headers)
    return response
