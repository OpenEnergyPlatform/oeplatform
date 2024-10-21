import requests

from factsheet.oekg.connection import update_endpoint


def add_datasets_to_scenario(scenario_uuid, dataset_name, dataset_type):
    """
    Function to add datasets to a scenario bundle in Jena Fuseki.
    """

    sparql_query = f"""
    PREFIX oeo: <http://example.org/ontology#>
    INSERT DATA {{
        GRAPH <http://example.org/scenario/{scenario_uuid}> {{
            oeo:{dataset_name} a oeo:{dataset_type}Dataset .
        }}
    }}
    """
    response = send_sparql_update(sparql_query)
    if not response.ok:
        return False  # Return False if any query fails
    return True


def remove_datasets_from_scenario(scenario_uuid, dataset_name, dataset_type):
    """
    Function to remove datasets from a scenario bundle in Jena Fuseki.
    """
    sparql_query = f"""
    PREFIX oeo: <http://example.org/ontology#>
    DELETE DATA {{
        GRAPH <http://example.org/scenario/{scenario_uuid}> {{
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
