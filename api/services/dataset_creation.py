# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from copy import deepcopy
from typing import Any

from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE
from oemetadata.v2.v20.template import OEMETADATA_V20_TEMPLATE

from dataedit.models import Dataset


class DatasetNameTaken(Exception):
    """Raised when creating a dataset under a name that already exists."""


def assemble_dataset_metadata(
    validated_data: dict[str, Any], oemetadata: dict = OEMETADATA_V20_TEMPLATE
) -> dict[str, Any]:
    # set the context
    oemetadata = deepcopy(oemetadata)
    oemetadata["@context"] = OEMETADATA_V20_EXAMPLE["@context"]
    # resources are never stored on the dataset; they are assembled live
    # from the member tables on every read
    oemetadata.pop("resources", None)

    oemetadata["@id"] = validated_data.get("at_id")
    oemetadata["name"] = validated_data["name"]
    oemetadata["title"] = validated_data["title"]
    oemetadata["description"] = validated_data["description"]

    return oemetadata


def create_dataset(validated_data: dict[str, Any], creator) -> Dataset:
    """Create a creator-owned dataset from validated dataset-level fields.

    Shared by the JSON API and the dashboard UI so both enforce the same
    rules. Raises DatasetNameTaken on a name collision (the name is the
    permanent identifier, so it must be unique).
    """
    name = validated_data["name"]
    if Dataset.objects.filter(name=name).exists():
        raise DatasetNameTaken(
            f"A dataset named '{name}' already exists. Names are permanent "
            "identifiers and can not be reused."
        )

    metadata = assemble_dataset_metadata(validated_data)
    return Dataset.objects.create(metadata=metadata, name=name, creator=creator)
