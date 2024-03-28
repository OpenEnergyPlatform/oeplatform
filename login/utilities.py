import json
import logging
import re
from enum import Enum, auto

from django.templatetags.static import static

from functools import lru_cache
from pathlib import Path


from oeplatform.settings import STATIC_ROOT

#####################################################
# Utilities mainly used for the Tables profile page #
#####################################################

# Functions below implement the automated license check


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


# The following functions implement the retrieval of review badges
# from the oemetadata and handle the case when no sticker is available.


# TODO Refactor this to dataedit app?
class PeerReviewBadge(Enum):
    IRON = auto()
    BRONZE = auto()
    SILVER = auto()
    GOLD = auto()
    PLATINUM = auto()


def validate_badge_name_match(badge_name_normalized):
    matched_badge = None
    for badge in PeerReviewBadge:
        if badge_name_normalized == badge.name:
            matched_badge = badge
            break

    return matched_badge


def get_review_badge_from_table_metadata(django_table_obj):
    metadata = django_table_obj.oemetadata

    if metadata is None:
        return False, "Metadata is empty!"

    review = metadata.get("review")

    if not review:
        return False, "No review information available in the metadata."

    badge = review.get("badge")

    if badge is None and badge != "":
        return (
            False,
            "No badge information available in the metadata.Please start a community-based open peer review for this table first.",
        )

    badge_name_normalized = badge.upper()
    badge_check_result = validate_badge_name_match(badge_name_normalized)

    if badge_check_result:
        return True, badge_check_result.name
    else:
        return False, f"No match found for badge name: {badge}"


def get_badge_icon_path(badge_name):
    # Convert the badge name to lowercase and append "_badge.png"
    normalized_name = f"badge_{badge_name.lower()}.png"

    # Use the Django static function to get the correct static path
    icon_path = static(f"img/badges/{normalized_name}")

    return icon_path


#####################################################
# Utilities mainly used for the Review profile page #
#####################################################

# Add functionality here

###############################################################
# Utilities mainly used for the Group Management profile page #
###############################################################

# Add functionality here

#######################################################
# Utilities mainly used for the Settings profile page #
#######################################################

# Add functionality here
