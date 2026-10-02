"""
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 shara <https://github.com/SharanyaMohan-30> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

# TODO: This might have t be removed fully
from oemetadata.v2.v20.template import OEMETADATA_V20_TEMPLATE
from omi.validation import validate_metadata

from dataedit.metadata.v1_5 import TEMPLATE_V1_5
from dataedit.models import Table

METADATA_TEMPLATE = {
    5: TEMPLATE_V1_5,
    # 4: TEMPLATE_V1_4,
    # 3: TEMPLATE_v1_3,
}


# Keep for collection purposes
# name of the metadata fields which should not be filled by the user
METADATA_HIDDEN_FIELDS = [
    "_comment",  # v1.4
    "metaMetadata",  # v1.4
    "metadata_version",  # v1.3
]


def save_metadata_to_db(table: str, updated_metadata):
    """
    Save updated metadata for a specific table in the OEP database.

    Args:
        table (str): The name of the table in the OEP.
        updated_metadata (dict): The updated metadata dictionary.

    Note:
        This function loads the table object from the database,
        updates its metadata field, and then saves the updated
        table object back to the database.
    """

    # Load the table object
    table_obj = Table.load(name=table)

    # Update the oemetadata field
    table_obj.oemetadata = updated_metadata

    # Save the updated table object
    table_obj.save()


def load_metadata_from_db(table: str) -> dict:
    """
    Load metadata for a specific table from the OEP database.

    Args:
        table (str): The name of the table in the OEP.

    Returns:
        dict: The loaded metadata dictionary.

    Note:
        The function currently loads metadata from the Table.oemetadata field.
        There is a consideration to change this function to use a different approach
        or keep the old functionality (TODO).
    """

    table_obj = Table.load(name=table)
    metadata = table_obj.oemetadata
    if not metadata:
        # empty / new metadata

        # TODO: the template is full of empty strings, which are not valid metadata
        # so we use only parts of it

        metaMetadata = OEMETADATA_V20_TEMPLATE["metaMetadata"]
        name = table_obj.name

        metadata = {
            "name": name,
            "resources": [{"name": name}],
            "metaMetadata": metaMetadata,
        }
        validate_metadata(metadata, check_license=False)

    return metadata


def has_valid_filled_metadata(metadata: dict) -> bool:
    """
    Check if metadata has been meaningfully filled beyond the default fields
    that are automatically populated by load_metadata_from_db.

    The default fields set by load_metadata_from_db are:
        - "name": table name
        - "resources": [{"name": table name}]
        - "metaMetadata": from OEMETADATA_V20_TEMPLATE

    Returns False if metadata is empty or only contains these default fields.
    Returns True if at least one additional field has a meaningful value.

    Args:
        metadata: The OEMetadata dictionary

    Returns:
        bool: True if metadata has been filled beyond defaults, False otherwise
    """
    if not metadata:
        return False

    # Keys that are considered "default" / auto-filled and should be ignored
    DEFAULT_ONLY_KEYS = {"name", "metaMetadata"}

    def check_value(val):
        """Check if a value is considered non-empty."""
        if val is None:
            return False
        if isinstance(val, str):
            return val.strip() not in ("", "None", "null")
        if isinstance(val, (list, dict)):
            return len(val) > 0
        return True

    def is_default_resources(resources):
        """
        Check if resources only contains the default minimal entry
        set by load_metadata_from_db: [{"name": <table_name>}]
        """
        if not isinstance(resources, list):
            return False
        if len(resources) != 1:
            # More than one resource means user has added content
            return False

        resource = resources[0]
        if not isinstance(resource, dict):
            return False

        # Default resource only has "name" key
        return set(resource.keys()) == {"name"}

    def traverse(obj):
        """Recursively traverse the metadata structure."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in DEFAULT_ONLY_KEYS:
                    continue
                if key == "resources":
                    # Only skip if it matches the default minimal resources structure
                    if is_default_resources(value):
                        continue
                if check_value(value) or traverse(value):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if check_value(item) or traverse(item):
                    return True
        return False

    return traverse(metadata)
