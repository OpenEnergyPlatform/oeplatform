import re

from oekg.sparqlModels import DatasetConfig
from oekg.sparqlQuery import add_datasets_to_scenario, scenario_in_bundle


def validate_public_sparql_query(query):
    """
    Validate the SPARQL query to prevent injection attacks.
    """

    # Basic length check
    if not query or len(query) > 10000:  # Set an appropriate limit for your use case
        return False

    # Basic SPARQL syntax check using a regular expression (this is a simplistic check)
    pattern = re.compile(
        r"^\s*(PREFIX\s+[^\s]+:\s*<[^>]+>\s*)*(SELECT|CONSTRUCT|ASK|DESCRIBE)\s+",
        re.IGNORECASE,
    )
    if not pattern.match(query):
        return False

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
