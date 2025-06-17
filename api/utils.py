# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Collection of utility functions for the API used to define various action
like processing steps.
"""

from oekg.sparqlModels import DatasetConfig


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
