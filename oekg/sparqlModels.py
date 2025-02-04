from dataclasses import dataclass
from uuid import UUID


@dataclass
class DatasetConfig:
    bundle_uuid: UUID
    scenario_uuid: UUID
    dataset_label: str
    dataset_url: str
    dataset_id: int
    dataset_key: bool
    dataset_type: str
