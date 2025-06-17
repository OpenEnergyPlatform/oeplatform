# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

import re

import requests

from oekg.sparqlModels import DatasetConfig
from oekg.sparqlQuery import (
    add_datasets_to_scenario,
    scenario_bundle_filter_oekg,
    scenario_in_bundle,
)
from oeplatform.settings import OEKG_SPARQL_ENDPOINT_URL

# Whitelist of supported formats
SUPPORTED_FORMATS = {
    "json": "application/sparql-results+json",
    "json-ld": "application/ld+json",
    "xml": "application/rdf+xml",
    "turtle": "text/turtle",
}


def execute_filter_sparql_query(criteria) -> dict:
    """
    Executes the SPARQL query and returns the appropriate response.

    :param sparql_query: The SPARQL query string.
    :param response_format: The requested response format.
    :return: Tuple (response content, content_type)
    """
    result = scenario_bundle_filter_oekg(criteria)
    return result


def execute_sparql_query(sparql_query, response_format):
    """
    Executes the SPARQL query and returns the appropriate response.

    :param sparql_query: The SPARQL query string.
    :param response_format: The requested response format.
    :return: Tuple (response content, content_type)
    """
    if not sparql_query:
        raise ValueError("Missing 'query' parameter.")

    if response_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {response_format}")

    endpoint_url = OEKG_SPARQL_ENDPOINT_URL
    headers = {
        "Accept": SUPPORTED_FORMATS[response_format],
        # "Content-Type": SUPPORTED_FORMATS[response_format],
    }

    # Execute the SPARQL query
    response = requests.post(
        endpoint_url, data={"query": sparql_query}, headers=headers, timeout=10
    )

    if response.status_code != 200:
        raise ValueError(
            f"Failed to execute SPARQL query. Reason: {response.reason},"
            f"Status Code {response.status_code}."
        )

    return response.content, SUPPORTED_FORMATS[response_format]


def validate_public_sparql_query(query):
    """
    Validate the SPARQL query to prevent injection attacks.

    Note: not in use currently, keep for later. Review and remove if
    deprecated.
    """

    # Check for disallowed keywords (e.g., DROP, DELETE, INSERT)
    disallowed_keywords = ["DROP", "DELETE", "INSERT"]
    for keyword in disallowed_keywords:
        if re.search(rf"\b{keyword}\b", query, re.IGNORECASE):
            return False

    return True


def process_datasets_sparql_query(dataset_configs: list[DatasetConfig]):
    """
    Attempts to add each dataset to the scenario.
    Returns a count of added datasets and a list of skipped ones.
    """
    total_datasets = len(dataset_configs)
    added_count = 0
    skipped_datasets = []

    for dataset_config in dataset_configs:
        # Check if scenario is part of the scenario bundle

        if not scenario_in_bundle(
            dataset_config.bundle_uuid, dataset_config.scenario_uuid
        ):
            response: dict = {}
            response["error"] = (
                f"Scenario {dataset_config.scenario_uuid} is not part"
                f"of bundle {dataset_config.bundle_uuid}"
            )
            return response

        success = add_datasets_to_scenario(dataset_config)

        if success:
            added_count += 1
        else:
            skipped_datasets.append(dataset_config.dataset_label)

    # Construct a clear response
    response: dict = {
        "info": "successfully processed your request",
        "added_count": f"{added_count} / {total_datasets}",
    }

    if skipped_datasets:
        # TODO: Add return a reason from add_datasets_to_scenario if needed
        response["reason"] = "Dataset already exists in the scenario."
        response["skipped"] = skipped_datasets

    return response
