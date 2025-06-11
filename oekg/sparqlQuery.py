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
    PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/>

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
    PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/>
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
    PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/>
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
    PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/>
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


def iri_list(values):
    return ", ".join(f"<{v}>" if not v.startswith("OEKG:") else v for v in values)


def build_filter_block(var, predicate, values):
    if not values:
        return ""
    return f"""
        ?s {predicate} ?{var} .
        FILTER(?{var} IN ({iri_list(values)}))
    """


def build_filter_block_string_values(predicate: str, values: list[str]) -> str:
    if not values:
        return ""
    return "\n".join(f'?s {predicate} "{v}" .' for v in values)


def scenario_bundle_filter_oekg(criteria: dict, return_format=JSON) -> dict:
    """
    Function to filter scenario bundles in the OEKG based on various criteria.

    :param criteria: Dictionary containing filter criteria from frontend.
    :param return_format: Format for the SPARQL query result.
    :return: Filtered scenario bundles.
    """

    # Extract filters with safe defaults
    institutes = criteria.get("institutions", [])
    authors = criteria.get("authors", [])
    funding_sources = criteria.get("fundingSource", [])
    pub_date_start = criteria.get("startDateOfPublication", "")
    pub_date_end = criteria.get("endDateOfPublication", "")
    study_keywords = criteria.get("studyKeywords", criteria.get("studyKewords", []))
    scenario_year_range = criteria.get("scenarioYearValue", ["", ""])
    year_start, year_end = (
        scenario_year_range if len(scenario_year_range) == 2 else ("", "")
    )

    # Pagination
    results_per_page = int(criteria.get("resultsPerPage", 25))
    page = int(criteria.get("page", 1))
    offset = (page - 1) * results_per_page

    # Build required triple+filter blocks
    authors_exp = build_filter_block("authors", "OEO:OEO_00000506", authors)
    institutes_exp = build_filter_block("institutes", "OEO:OEO_00000510", institutes)
    funding_sources_exp = build_filter_block(
        "funding_sources", "OEO:OEO_00000509", funding_sources
    )
    study_keywords_exp = build_filter_block_string_values(
        "OEO:has_study_keyword", study_keywords
    )

    # Scenario year clause
    scenario_year_exp = ""
    try:
        if year_start and year_end:
            year_start = int(year_start)
            year_end = int(year_end)
            scenario_year_exp = f"""
                ?s OEKG:has_scenario ?scenario .
                ?scenario OEO:OEO_00020224 ?scenario_year .
                FILTER (
                    xsd:integer(?scenario_year) >= {year_start} &&
                    xsd:integer(?scenario_year) <= {year_end}
                )
            """
    except ValueError:
        pass

    # Publication date filter
    pub_date_exp = ""
    try:
        if pub_date_start and pub_date_end:
            pub_date_start = int(pub_date_start)
            pub_date_end = int(pub_date_end)
            pub_date_exp = f"""
                ?s OEKG:has_publication ?publication .
                ?publication OEKG:date_of_publication ?publication_date .
                BIND(xsd:integer(SUBSTR(STR(?publication_date), 1, 4)) AS ?pub_year)
                FILTER (?pub_year >= {pub_date_start} && ?pub_year <= {pub_date_end})
            """
        else:
            # Still need to bind ?publication if no date filtering is applied
            pub_date_exp = "?s OEKG:has_publication ?publication ."
    except ValueError:
        pass

    # Final query
    query_structure = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX RDFS: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX OEO: <https://openenergyplatform.org/ontology/oeo/>
        PREFIX OEKG: <http://openenergy-platform.org/ontology/oekg/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX DC: <http://purl.org/dc/terms/>

        SELECT DISTINCT ?study_acronym
        WHERE {{
            ?s DC:acronym ?study_acronym .
            {pub_date_exp}
            {authors_exp}
            {institutes_exp}
            {funding_sources_exp}
            {study_keywords_exp}
            {scenario_year_exp}
        }}
        LIMIT {results_per_page}
        OFFSET {offset}
    """

    # Run query
    sparql.setReturnFormat(return_format)
    sparql.setQuery(query_structure)
    return sparql.query().convert()
