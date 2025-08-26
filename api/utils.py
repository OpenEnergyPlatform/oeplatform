# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Collection of utility functions for the API used to define various action
like processing steps.
"""

from typing import Union

from oekg.sparqlModels import DatasetConfig
from oeplatform.settings import DATASETS_SCHEMA, SANDBOX_SCHEMA, TEST_SCHEMA


def get_dataset_configs(validated_data) -> list[DatasetConfig]:
    """Converts validated serializer data into a list of DatasetConfig objects."""
    return [
        DatasetConfig.from_serializer_data(validated_data, dataset_entry)
        for dataset_entry in validated_data["datasets"]
    ]


def check_if_oem_license_exists(metadata: dict):
    # already parsed but need to check if metaMetadata version exists

    if "metaMetadata" not in metadata:
        return None, "No metaMetadata information in metadata."
    if "metadataVersion" not in metadata["metaMetadata"]:
        return None, "No version info in metaMetadata."
    if (
        metadata["metaMetadata"]["metadataVersion"] == ""
        or metadata["metaMetadata"]["metadataVersion"] is None
    ):
        return None, "The version info in metaMetadata is empty."

    return metadata["metaMetadata"]["metadataVersion"], None


def get_valid_schema(schema: Union[str, None] = None) -> str:
    if schema is None:
        return SANDBOX_SCHEMA
    elif schema in {SANDBOX_SCHEMA, DATASETS_SCHEMA, TEST_SCHEMA}:
        # TODO wingechr: test schema should only be allowed if run in test environment
        return schema
    elif schema in {"_" + SANDBOX_SCHEMA, "_" + DATASETS_SCHEMA, "_" + TEST_SCHEMA}:
        # TODO wingechr: meta schema should not be tested once schema is allowed
        return schema
    raise Exception(f"Invalid schema: {schema}")
