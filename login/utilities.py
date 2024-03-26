import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from oeplatform.settings import STATIC_ROOT


def normalize_license_name(name):
    # Replace whitespaces with hyphens and convert to uppercase
    return re.sub(r"\s", "-", name).upper()


@lru_cache(maxsize=None)
def read_spdx_licenses_from_static():
    # Specify the path to your JSON file
    file = "data_licenses/licenses.json"
    json_file_path = Path(STATIC_ROOT, file)

    try:
        # Open the file in read mode
        if json_file_path:
            with open(json_file_path, "r", encoding="utf-8") as file:
                # Load the JSON data into a Python dictionary
                data_dict = json.load(file)

        return data_dict
    except FileNotFoundError as e:
        logging.error(f"The licenses files was not found in {json_file_path}")
        raise e


@lru_cache(maxsize=None)
def create_license_id_set():
    licenses = read_spdx_licenses_from_static()
    # Check if the "licenses" key exists in the dictionary
    if "licenses" in licenses:
        # Create a set of unique licenseId values
        return {
            license_info.get("licenseId").upper()
            for license_info in licenses["licenses"]
        }

    else:
        return set()


LICENSES = create_license_id_set()


def search_oem_license_in_spdx_list(input_license_id, license_set=LICENSES):
    processed_input = normalize_license_name(input_license_id)
    return processed_input in license_set


def validate_open_data_license(django_table_obj):
    metadata = django_table_obj.oemetadata
    if metadata is None:
        return False, "Metadata is empty!"

    licenses = metadata.get("licenses", [])

    if not licenses:
        return False, "No license information available in the metadata."

    first_license = licenses[0]
    if not first_license.get("name"):
        return (
            False,
            "The license name is missing "
            "(only checked the first license element in the oemetadata).",
        )

    identifier = first_license["name"]
    if not search_oem_license_in_spdx_list(input_license_id=identifier):
        return (
            False,
            "The license name was not found in the SPDX licenses list. (See "
            "https://github.com/spdx/license-list-data/blob/main/json/licenses.json)",
        )

    return True, None
