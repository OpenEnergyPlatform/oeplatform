from metadata.v160.template import OEMETADATA_V160_TEMPLATE

from dataedit.metadata import v1_4 as __LATEST
from dataedit.metadata.v1_3 import TEMPLATE_v1_3
from dataedit.metadata.v1_4 import TEMPLATE_V1_4
from dataedit.metadata.v1_5 import TEMPLATE_V1_5

from .error import MetadataException

METADATA_TEMPLATE = {
    6: OEMETADATA_V160_TEMPLATE,
    5: TEMPLATE_V1_5,
    4: TEMPLATE_V1_4,
    3: TEMPLATE_v1_3,
}


# name of the metadata fields which should not be filled by the user
METADATA_HIDDEN_FIELDS = [
    "_comment",  # v1.4
    "metaMetadata",  # v1.4
    "metadata_version",  # v1.3
]


def format_content_key(parent, k):
    if parent != "":
        answer = "{}_{}".format(parent, k)
    else:
        answer = k

    return answer


def assign_content_values_to_metadata(content, template=None, parent=""):
    """Match a query dict onto a nested structure

    example :
    content = {
        "name": ["Example"]
        "sources0_title": ["S0"],
        "sources0_licenses0_name": ["first license source 0"],
        "sources1_title": ["S1"],
        "licenses0_name": ["first licence"],
    }

    template_dict = {
        "name": ""
        "sources": [
            {
                "title": "",
                "description": "",
                "path": "",
                "licenses": [{"name": "", ...}]
            }
        ],
        "licenses": [{name": "", ... }],
    }

    template_dict["sources"][0]["title"] will be assigned the values contained in
    content["sources0_title"]

    :param content: query dict
    :param template: dict (can be nested dicts)
    :param parent: a parameter to link content keys with the nested structure
        of template
    :return: the template with assigned values from the content query dict
    """
    for k in template:
        if k not in METADATA_HIDDEN_FIELDS:
            if isinstance(template[k], dict):
                # the value is a dict, so we make a recursive call
                template[k] = assign_content_values_to_metadata(
                    content=content,
                    template=template[k],
                    parent=format_content_key(parent, k),
                )
            elif isinstance(template[k], list):
                # the value is a list, so we make a recursive call on the
                # unique instances in the list

                # find the instances which start with the prefix in the content keys
                prefix = format_content_key(parent, k)
                matches = [i for i in content if i.startswith(prefix)]

                # count the number of unique instances among the matches
                # (in case of list of dicts, this is not equal to the number of matches)
                count = []
                item_list = []
                is_dict = isinstance((template[k][0]), dict)
                for i in matches:
                    idx = i.replace(prefix, "").split("_")[0]
                    if idx not in count:
                        count.append(idx)

                        if is_dict:
                            # it is a list of dict, so we make a recursive call
                            item_list.append(
                                assign_content_values_to_metadata(
                                    content=content,
                                    template=template[k][0].copy(),
                                    parent=format_content_key(
                                        parent, "{}{}".format(k, idx)
                                    ),
                                )
                            )
                        else:
                            # it is a list of string
                            item_list.append(
                                content[
                                    format_content_key(parent, "{}{}".format(k, idx))
                                ]
                            )

                if len(count) != 0:
                    template[k] = item_list
            elif isinstance(template[k], str):
                template[k] = content.get(format_content_key(parent, k), "")

    return template


def save_metadata_to_db(schema, table, updated_metadata):
    """
    Save updated metadata for a specific table in the OEP database.

    Args:
        schema (str): The name of the OEP schema.
        table (str): The name of the table in the OEP schema.
        updated_metadata (dict): The updated metadata dictionary.

    Note:
        This function loads the table object from the database,
        updates its metadata field, and then saves the updated
        table object back to the database.
    """

    from dataedit.models import Table

    # Load the table object
    table_obj = Table.load(schema=schema, table=table)

    # Update the oemetadata field
    table_obj.oemetadata = updated_metadata

    # Save the updated table object
    table_obj.save()


def load_metadata_from_db(schema, table):
    """
    Load metadata for a specific table from the OEP database.

    Args:
        schema (str): The name of the OEP schema.
        table (str): The name of the table in the OEP schema.

    Returns:
        dict: The loaded metadata dictionary.

    Note:
        The function currently loads metadata from the Table.oemetadata field.
        There is a consideration to change this function to use a different approach
        or keep the old functionality (TODO).
    """

    from dataedit.models import Table

    metadata = Table.load(schema=schema, table=table).oemetadata

    metadata = parse_meta_data(metadata, schema, table)
    return metadata


def parse_meta_data(metadata, schema, table):
    # if "error" in metadata:
    #     return metadata
    if not metadata:
        metadata = OEMETADATA_V160_TEMPLATE
    else:
        if "error" in metadata:
            return {"description": metadata["content"], "error": metadata["error"]}
        try:
            version = get_metadata_version(metadata)
            if version:
                if not isinstance(version, tuple):
                    version = (version,)
                if len(version) < 2:
                    version = (version[0], 0)
                if version[0] == 1:
                    if version[1] == 1:
                        metadata = __LATEST.from_v1_1(metadata, schema, table)
                    elif version[1] == 2:
                        metadata = __LATEST.from_v1_2(metadata)
                    elif version[1] == 3:
                        # This is not part of the actual metadata-schema. We move the
                        # fields to a higher level in order to avoid fetching the first
                        # resource in the templates.
                        res = metadata.get("resources", [])
                        if res:
                            metadata["fields"] = res[0].get("fields", [])
                    elif version[1] == 4:
                        # This is not part of the actual metadata-schema. We move the
                        # fields to a higher level in order to avoid fetching the
                        # first resource in the templates.
                        res = metadata.get("resources", [])
                        if res:
                            metadata["fields"] = (
                                res[0].get("schema", {}).get("fields", [])
                            )
                elif version[0] == 0:
                    metadata = __LATEST.from_v0(metadata, schema, table)
            else:
                metadata = __LATEST.from_v0(metadata, schema, table)
        except MetadataException as me:
            return {
                "description": metadata,
                "error": (
                    me.error.message if hasattr(me.error, "message") else str(me.error)
                ),
            }
    return metadata


def get_metadata_version(metadata):
    """Find the metadata version in the metadata

    :param metadata: a json-like dict
    :return: the version in (X, Y, Z) format
    """
    if "metaMetadata" in metadata:
        # v1.4
        version = metadata["metaMetadata"]["metadataVersion"]
        version = __parse_version(version.replace("OEP-", ""))
    elif "metaMetadata_metadataVersion" in metadata:
        # v1.4 from post request
        version = metadata["metaMetadata_metadataVersion"]
        version = __parse_version(version.replace("OEP-", ""))
    elif "metadata_version" in metadata:
        # v1.3
        version = __parse_version(metadata["metadata_version"])
    elif "meta_version" in metadata:
        # < v1.3
        version = __parse_version(metadata["meta_version"])
    elif "resources" in metadata:
        # < v1.3
        versions = [
            __parse_version(x["meta_version"])
            for x in metadata["resources"]
            if "meta_version" in x
        ]
        if not versions:
            version = None
        else:
            version = min(versions)
    else:
        version = (0, 0, 0)

    return version


def __parse_version(version_string):
    """Formats the string version to a tuple of int"""
    if version_string.count(".") == 1:
        version_string = version_string + ".0"
    return tuple(map(int, version_string.split(".")))
