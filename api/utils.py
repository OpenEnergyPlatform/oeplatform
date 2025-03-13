# SPDX-FileCopyrightText: 2025 Jonas Huber <jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT

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
