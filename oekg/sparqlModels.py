# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class DatasetConfig:
    bundle_uuid: UUID
    scenario_uuid: UUID
    dataset_label: str
    dataset_url: str
    dataset_id: UUID
    dataset_type: str

    @classmethod
    def from_serializer_data(cls, validated_data: dict, dataset_entry: dict):
        """Converts validated serializer data into a DatasetConfig object."""
        return cls(
            bundle_uuid=validated_data["scenario_bundle"],
            scenario_uuid=validated_data["scenario"],
            dataset_label=dataset_entry["name"],
            dataset_url=dataset_entry["external_url"],
            dataset_id=uuid4(),
            dataset_type=dataset_entry["type"],  # "input" or "output"
        )
