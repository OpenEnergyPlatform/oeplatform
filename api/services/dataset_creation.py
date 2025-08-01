# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Any

from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE
from oemetadata.v2.v20.template import OEMETADATA_V20_TEMPLATE


def assemble_dataset_metadata(
    validated_data: dict[str, Any], oemetadata: dict = OEMETADATA_V20_TEMPLATE
) -> dict[str, Any]:
    # set the context
    oemetadata["@context"] = OEMETADATA_V20_EXAMPLE["@context"]
    oemetadata["resources"] = []  # Remove resources

    oemetadata["@id"] = validated_data.get("at_id")
    oemetadata["name"] = validated_data["name"]
    oemetadata["title"] = validated_data["title"]
    oemetadata["description"] = validated_data["description"]

    return oemetadata
