from uuid import UUID

import requests
from SPARQLWrapper import JSON, POST

from factsheet.oekg.connection import sparql_wrapper_update, update_endpoint
from oekg.sparqlModels import DatasetConfig


def add_datasets_to_scenario(oekgDatasetConfig: DatasetConfig):
    """
    Function to add datasets to a scenario bundle in Jena Fuseki.
    """

    new_dataset_uid = UUID()

    if oekgDatasetConfig.dataset_type == "input":
        rel_property = "RO_0002233"
    elif oekgDatasetConfig.dataset_type == "output":
        rel_property = "RO_0002234"

    sparql_query = f"""
    PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    INSERT DATA {{
        GRAPH <http://openenergy-platform.org/ontology/oekg/{oekgDatasetConfig.scenario_uuid}> {{
            <http://openenergy-platform.org/ontology/oekg/input_datasets/{new_dataset_uid}> a oeo:OEO_00030030 ;
                rdfs:label "{oekgDatasetConfig.dataset_label}" ;
                oeo:has_iri "{oekgDatasetConfig.dataset_url}" ;
                oeo:has_id "{oekgDatasetConfig.dataset_id}" ;
                oeo:has_key "{oekgDatasetConfig.dataset_key}" .

            <http://openenergy-platform.org/ontology/oekg/{oekgDatasetConfig.scenario_uuid}> oeo:{rel_property}
                <http://openenergy-platform.org/ontology/oekg/input_datasets/{new_dataset_uid}> .
        }}
    }}
    """  # noqa

    print(sparql_query)
    # response = send_sparql_update(sparql_query)
    sparql_wrapper_update.setQuery(sparql_query)
    sparql_wrapper_update.setMethod(POST)
    sparql_wrapper_update.setReturnFormat(JSON)
    response = sparql_wrapper_update.query()
    http_response = response.response
    if not http_response.status == 200:
        return False  # Return False if any query fails
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
