"""SPARQL queries related to filtering scenario bundles in the OEKG.

SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
from http.client import HTTPResponse
from typing import Union
from uuid import UUID

import requests
from rdflib import URIRef
from SPARQLWrapper import JSON, POST

from factsheet.oekg.connection import sparql, sparql_wrapper_update, update_endpoint
from oekg.sparqlModels import DatasetConfig

logger = logging.getLogger("oeplatform")


def bundle_scenarios_filter(bundle_uri: Union[str, URIRef], return_format=JSON) -> dict:
    """
    Return scenarios that are part-of the given bundle URI.
    """
    u = str(bundle_uri).strip()
    if not (u.startswith("<") and u.endswith(">")):
        u = f"<{u}>"

    sparql_query = f"""
        PREFIX obo:  <http://purl.obolibrary.org/obo/>
        PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/>
        PREFIX dc:   <http://purl.org/dc/terms/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX oekg: <https://openenergyplatform.org/ontology/oekg/>

        SELECT DISTINCT ?o ?label ?abstract ?fullName ?uid
        WHERE {{

            VALUES ?bundle {{ {u} }}
            ?bundle obo:BFO_0000051 ?o .

            ?o a oeo:OEO_00000365 .

            OPTIONAL {{ ?o dc:acronym  ?label }}
            OPTIONAL {{ ?o dc:abstract ?abstract }}
            OPTIONAL {{ ?o rdfs:label  ?fullName }}
            OPTIONAL {{ ?o oeo:OEO_00390095 ?uid }}
        }}
    """

    sparql.setReturnFormat(return_format)
    sparql.setQuery(sparql_query)
    return sparql.query().convert()  # type:ignore (if json, convert() -> dict)


def scenario_in_bundle(bundle_uuid: UUID, scenario_uuid: UUID) -> bool:
    """
    Check if a scenario is part of a scenario bundle in the KG.
    """
    sparql_query = f"""
    PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/>

    ASK {{
        <https://openenergyplatform.org/ontology/oekg/{bundle_uuid}> ?p
            <https://openenergyplatform.org/ontology/oekg/scenario/{scenario_uuid}> .
    }}
    """
    sparql.setQuery(sparql_query)
    sparql.setMethod(POST)
    sparql.setReturnFormat(JSON)
    response: dict = (
        sparql.query().convert()
    )  # type:ignore (if json, convert() -> dict)

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
        <https://openenergyplatform.org/ontology/oekg/scenario/{scenario_uuid}> ?p ?dataset .
        ?dataset oeo:has_iri "{dataset_url}" .
    }}

    """  # noqa

    sparql.setQuery(sparql_query)
    sparql.setMethod(POST)
    sparql.setReturnFormat(JSON)
    response: dict = (
        sparql.query().convert()
    )  # type:ignore (if json, convert() -> dict)

    return response.get("boolean", False)  # Returns True if dataset exists


def add_datasets_to_scenario(oekgDatasetConfig: DatasetConfig) -> bool:
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
        <https://openenergyplatform.org/ontology/oekg/input_datasets/{oekgDatasetConfig.dataset_id}> a oeo:{type_entity} ;
            rdfs:label "{oekgDatasetConfig.dataset_label}" ;
            oeo:has_iri "{oekgDatasetConfig.dataset_url}" ;
            oeo:has_key "{oekgDatasetConfig.dataset_id}" .

        <https://openenergyplatform.org/ontology/oekg/scenario/{oekgDatasetConfig.scenario_uuid}> oeo:{rel_property}
            <https://openenergyplatform.org/ontology/oekg/input_datasets/{oekgDatasetConfig.dataset_id}> .
    }}
    """  # noqa

    sparql_wrapper_update.setQuery(sparql_query)
    sparql_wrapper_update.setMethod(POST)
    sparql_wrapper_update.setReturnFormat(JSON)
    try:
        response = sparql_wrapper_update.query()
        http_response: HTTPResponse = (
            response.response
        )  # type:ignore (according to documentation)
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
        GRAPH <https://openenergyplatform.org/ontology/oekg/{scenario_uuid}> {{
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

    values_items = " ".join(f"{author}" for author in authors)
    authors_exp = ""
    if authors:
        authors_exp = f"""
            ?s OBO:BFO_0000051 ?publication .
            ?publication OEO:OEO_00000506 ?author .

            # Use full IRIs here (examples)
            VALUES ?author {{ {values_items} }}
        """

    institutes_exp = build_filter_block("institutes", "OEO:OEO_00000510", institutes)
    funding_sources_exp = build_filter_block(
        "funding_sources", "OEO:OEO_00000509", funding_sources
    )

    values_items = " ".join(f'"{kw}"' for kw in study_keywords)
    study_keywords_exp = ""
    if values_items:
        study_keywords_exp = f"""
            ?s OEO:OEO_00390071 ?descriptor_iri .
            ?descriptor_iri RDFS:label ?descriptor .

            VALUES ?descriptor {{ {values_items} }}
        """

    # Scenario year clause
    scenario_year_exp = ""
    try:
        if year_start and year_end:
            year_start = int(year_start)
            year_end = int(year_end)
            scenario_year_exp = f"""
                ?s OBO:BFO_0000051 ?scenario .
                ?scenario OEO:OEO_00020440 ?scenario_date .
                BIND (YEAR(?scenario_date) AS ?scenario_year)
                FILTER (?scenario_year >= {year_start} && ?scenario_year <= {year_end})
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
                ?s OBO:BFO_0000051 ?publication .
                ?publication OEO:OEO_00390096 ?publication_date .
                BIND (YEAR(?publication_date) AS ?pub_year)
                FILTER (?pub_year >= {pub_date_start} && ?pub_year <= {pub_date_end})
            """

    except ValueError:
        pass

    # Final query ... keep http it is mandatory
    query_structure = f"""
        PREFIX OBO:  <http://purl.obolibrary.org/obo/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX RDFS: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX OEO: <https://openenergyplatform.org/ontology/oeo/>
        PREFIX OEKG: <https://openenergyplatform.org/ontology/oekg/>
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
    return sparql.query().convert()  # type:ignore (if json, convert() -> dict)


# --- filter helpers (reusable) -------------------------------------


def authors_filter_block(authors):
    """
    Accepts values like 'OEKG:…' or full IRIs. Reuses iri_list().
    """
    if not authors:
        return ""
    return f"""
        ?s OBO:BFO_0000051 ?publication .
        ?publication OEO:OEO_00000506 ?author .
        FILTER(?author IN ({iri_list(authors)}))
    """


def descriptors_filter_block_ci(labels):
    """
    Case-insensitive exact match on rdfs:label for descriptors.
    """
    items = [la for la in (labels or []) if la]
    if not items:
        return ""
    quoted = ", ".join(f'"{la.lower()}"' for la in items)
    return f"""
        ?s OEO:OEO_00390071 ?descriptor_iri .
        ?descriptor_iri RDFS:label ?descriptor .
        BIND(LCASE(STR(?descriptor)) AS ?_desc_lc)
        FILTER(?_desc_lc IN ({quoted}))
    """


def scenario_year_filter_block(year_start, year_end):
    try:
        ys = int(year_start) if year_start not in ("", None) else None
        ye = int(year_end) if year_end not in ("", None) else None
    except ValueError:
        ys = ye = None
    if not (ys and ye):
        return ""
    return f"""
        ?s OBO:BFO_0000051 ?scenario .
        ?scenario OEO:OEO_00020440 ?scenario_date .
        BIND (YEAR(?scenario_date) AS ?scenario_year)
        FILTER (?scenario_year >= {ys} && ?scenario_year <= {ye})
    """


def publication_year_filter_block(start_year, end_year):
    try:
        ys = int(start_year) if start_year not in ("", None) else None
        ye = int(end_year) if end_year not in ("", None) else None
    except ValueError:
        ys = ye = None
    if not (ys and ye):
        return ""
    return f"""
        ?s OBO:BFO_0000051 ?pub .
        ?pub OEO:OEO_00390096 ?publication_date .
        BIND (YEAR(?publication_date) AS ?pub_year)
        FILTER (?pub_year >= {ys} && ?pub_year <= {ye})
    """


# --- fast list query to get all factsheets (bundles) ---------------------------
# Use in SB react app instead of slow rdflib loops


def list_factsheets_oekg(criteria: dict, return_format=JSON) -> dict:
    """
    Aggregated list for bundles, replacing slow rdflib loops in the view.
    Returns SPARQL JSON that your view can map to the same structure as before.
    """

    # Pagination
    results_per_page = int(criteria.get("resultsPerPage", 25))
    page = int(criteria.get("page", 1))
    offset = (page - 1) * results_per_page

    # Filters (use same keys you already send from React)
    institutes = criteria.get("institutions", [])
    authors = criteria.get("authors", [])
    funding_sources = criteria.get("fundingSource", [])
    study_keywords = criteria.get("studyKeywords", criteria.get("studyKewords", []))
    scenario_range = criteria.get("scenarioYearValue", ["", ""])
    year_start, year_end = scenario_range if len(scenario_range) == 2 else ("", "")
    pub_date_start = criteria.get("startDateOfPublication", "")
    pub_date_end = criteria.get("endDateOfPublication", "")

    # Compose dynamic filter blocks (re-using your build_filter_block)
    blocks = "\n".join(
        [
            publication_year_filter_block(pub_date_start, pub_date_end),
            authors_filter_block(authors),
            build_filter_block("institutes", "OEO:OEO_00000510", institutes),
            build_filter_block("funding_sources", "OEO:OEO_00000509", funding_sources),
            descriptors_filter_block_ci(study_keywords),
            scenario_year_filter_block(year_start, year_end),
        ]
    )

    # Use a safe separator for GROUP_CONCAT
    SEP = "||"

    sparql_query = f"""
        PREFIX OBO:  <http://purl.obolibrary.org/obo/>
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX RDFS: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX OEO:  <https://openenergyplatform.org/ontology/oeo/>
        PREFIX OEKG: <https://openenergyplatform.org/ontology/oekg/>
        PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
        PREFIX DC:   <http://purl.org/dc/terms/>

        SELECT ?s ?uid ?study_acronym ?study_name ?abstract
               (GROUP_CONCAT(DISTINCT ?inst_label;         separator="{SEP}") AS ?institutions)
               (GROUP_CONCAT(DISTINCT ?fund_label;         separator="{SEP}") AS ?funding_sources)
               (GROUP_CONCAT(DISTINCT ?model_label;        separator="{SEP}") AS ?models)
               (GROUP_CONCAT(DISTINCT ?framework_label;    separator="{SEP}") AS ?frameworks)
               (GROUP_CONCAT(DISTINCT STR(?pub_date);      separator="{SEP}") AS ?collected_pub_dates)
        WHERE {{
          # bundles (factsheets)
          ?s a OEO:OEO_00020227 ;
             DC:acronym ?study_acronym .
          OPTIONAL {{ ?s RDFS:label   ?study_name }}
          OPTIONAL {{ ?s DC:abstract  ?abstract }}

          # institutions
          OPTIONAL {{
            ?s OEO:OEO_00000510 ?inst_iri .
            ?inst_iri RDFS:label ?inst_label .
          }}

          # funding sources
          OPTIONAL {{
            ?s OEO:OEO_00000509 ?fund_iri .
            ?fund_iri RDFS:label ?fund_label .
          }}

          OPTIONAL {{
            ?s OBO:BFO_0000051 ?modelPart .
            ?modelPart RDFS:label ?model_label .
            FILTER(CONTAINS(STR(?modelPart), "/models/"))
          }}

          OPTIONAL {{
            ?s OBO:BFO_0000051 ?frameworkPart .
            ?frameworkPart RDFS:label ?framework_label .
            FILTER(CONTAINS(STR(?frameworkPart), "/framework"))
          }}

          # publication dates of parts (for collected list)
          OPTIONAL {{
            ?s OBO:BFO_0000051 ?p .
            ?p OEO:OEO_00390096 ?pub_date .
          }}

          # dynamic filters
          {blocks}

          # uid for your frontend
          BIND( STRAFTER(STR(?s), "https://openenergyplatform.org/ontology/oekg/") AS ?uid )
        }}
        GROUP BY ?s ?uid ?study_acronym ?study_name ?abstract
        ORDER BY ?study_acronym
        # LIMIT {results_per_page}
        # OFFSET {offset}
    """  # noqa:E501

    sparql.setReturnFormat(return_format)
    sparql.setQuery(sparql_query)
    return sparql.query().convert()  # type:ignore (if json, convert() -> dict)


def normalize_factsheets_rows(res_json: dict) -> list[dict]:
    """
    Convert SPARQL JSON rows into your existing list structure,
    keeping keys your frontend already expects.
    """
    SEP = "||"
    out = []
    for row in res_json.get("results", {}).get("bindings", []):

        def get(var):
            return row[var]["value"] if var in row else ""

        def split(var):
            return [v for v in (get(var).split(SEP) if get(var) else []) if v]

        out.append(
            {
                "uid": get("uid"),
                "acronym": get("study_acronym"),
                "study_name": get("study_name"),
                "abstract": get("abstract"),
                "institutions": split("institutions"),
                "funding_sources": split("funding_sources"),
                "models": split("models"),
                "frameworks": split("frameworks"),
                "collected_scenario_publication_dates": split("collected_pub_dates"),
            }
        )
    return out
