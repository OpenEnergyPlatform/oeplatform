# SPDX-FileCopyrightText: 2025 Jonas Huber <jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT

import json
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

# Import your conversion functions and helpers.
from omi.base import get_metadata_version
from omi.conversion import convert_metadata
from omi.validation import validate_metadata

from dataedit.models import Table

# Define the constants used in your conversion process.
cc_by_4 = {
    "name": "CC-BY-4.0",
    "title": "Creative Commons Attribution 4.0 International",
    "path": "https://creativecommons.org/licenses/by/4.0/legalcode",
    "instruction": "You are free to share and adapt, but you must attribute. See https://creativecommons.org/licenses/by/4.0/deed.en for further information.",  # noqa: E501
    "attribution": "",
    "copyrightStatement": "https://www.ipcc.ch/copyright/",
}


# Configure logging to write errors to a file
logger = logging.getLogger("oeplatform")


def fix_metadata_v2(metadata, table_name, table_schema):
    """
    Fix and validate metadata by converting it to the OEMetadata v2.0 format.

    Args:
        metadata (obj|str): Python object of metadata or JSON string.
        table_name (str): Name of the table.
        table_schema (str): Schema name for the table.

    Returns:
        Fixed and validated metadata object.
    """
    # Ensure metadata is a string then load it as a Python object
    if not isinstance(metadata, str):
        metadata = json.dumps(metadata)
    metadata = json.loads(metadata)

    try:
        version = get_metadata_version(metadata)
        if version not in ["OEMetadata-2.0", "OEP-1.5.2, OEP-1.6.0"]:
            metadata["metaMetadata"]["metadataVersion"] = "OEP-1.6.0"
    except Exception as e:
        logger.error(
            f"Error in metadata version for table {table_schema}:{table_name}: {e}"
        )

    try:
        result_conversion = convert_metadata(
            metadata=metadata, target_version="OEMetadata-2.0"
        )
    except Exception as e:
        logger.error(
            f"Conversion error in metadata for table {table_schema}:{table_name}: {e}"
        )
        # Optionally re-raise or handle the error
        raise

    license_error = False
    try:
        check_license = False if table_schema == "model_draft" else True
        validate_metadata(result_conversion, check_license)
    except Exception as e:
        license_error = True
        logger.error(
            "Validation error in converted metadata"
            f" for table {table_schema}:{table_name}: {e}"
        )

    try:
        if license_error:
            result_conversion["resources"][0]["licenses"][0].update(cc_by_4)
            validate_metadata(result_conversion)
            logger.info(
                "Added CC-BY-4.0 license to published table"
                f" {table_schema}:{table_name}"
            )
    except Exception as e:
        license_error = True
        logger.error(
            "After adding a license the validation still failed for"
            f" {table_schema}:{table_name}: {e}"
        )

    return result_conversion


class Command(BaseCommand):
    help = "Convert Table.oemetadata to OEMetadata v2.0 format."

    def handle(self, *args, **options):
        tables = Table.objects.all()

        # Process each table in a transaction for safety.
        for table in tables:
            # Assume that the JSON metadata is stored in the 'oemetadata' field.
            oemetadata = table.oemetadata
            table_name = table.name  # Adjust based on your actual field names.
            table_schema = table.schema  # Adjust based on your actual field names.

            if not oemetadata:
                self.stdout.write(f"Skipping table {table_name}: no metadata found.")
                continue

            self.stdout.write(f"Processing table: {table_name}")

            try:
                # Convert the metadata using the fix_metadata_v2 function.
                new_metadata = fix_metadata_v2(oemetadata, table_name, table_schema)
            except Exception as e:
                self.stdout.write(
                    f"Error converting metadata for table {table_name}: {e}"
                )
                continue

            # Save the converted metadata back to the table.
            try:
                with transaction.atomic():
                    table.oemetadata = new_metadata
                    table.save(update_fields=["oemetadata"])
                self.stdout.write(
                    f"Successfully updated metadata for table {table_name}"
                )
            except Exception as e:
                logger.error(f"Error saving metadata for table {table_name}: {e}")
                self.stdout.write(f"Error saving metadata for table {table_name}: {e}")
