from api import actions
from dataedit.metadata import v1_4 as __LATEST
from dataedit.metadata.v1_3 import TEMPLATE_v1_3
from dataedit.metadata.v1_4 import TEMPLATE_V1_4

METADATA_TEMPLATE = {
    4: TEMPLATE_V1_4,
    3: TEMPLATE_v1_3,
}

from .error import MetadataException

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
    :param parent: a parameter to link content keys with the nested structure of template
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
                # the value is a list, so we make a recursive call on the unique instances
                # in the list

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


def load_metadata_from_db(schema, table):
    """Get comment for a table in OEP database (contains the metadata)

    :param schema: name of the OEP schema
    :param table: name of the OEP table in the OEP schema
    :return:
    """
    metadata = actions.get_comment_table(schema, table)
    metadata = parse_meta_data(metadata, schema, table)
    return metadata


def parse_meta_data(metadata, schema, table):
    if "error" in metadata:
        return metadata
    if not metadata:
        metadata = __LATEST.get_empty(schema, table)
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
                        # This is not part of the actual metadata-schema. We move the fields to
                        # a higher level in order to avoid fetching the first resource in the
                        # templates.
                        res = metadata.get("resources", [])
                        if res:
                            metadata["fields"] = res[0].get("fields", [])
                    elif version[1] == 4:
                        # This is not part of the actual metadata-schema. We move the fields to
                        # a higher level in order to avoid fetching the first resource in the
                        # templates.
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
                "error": me.error.message
                if hasattr(me.error, "message")
                else str(me.error),
            }
    return metadata


def read_metadata_from_post(content_query, schema, table):
    """Prepare dict to modify the comment prop of a table in OEP database (contains the metadata)

    :param content_query: the content of the POST request

    :param schema: name of the OEP schema
    :param table: name of the OEP table in the OEP schema
    :return: metadata dict
    """
    version = get_metadata_version(content_query)
    if version is tuple and len(version) > 2:
        template = METADATA_TEMPLATE[version[1]].copy()
    else:
        template = METADATA_TEMPLATE[4].copy()
    metadata = assign_content_values_to_metadata(
        content=content_query, template=template
    )
    # TODO fill the "resource" field for v1.4
    # d["resources"] = [
    #     {
    #         "name": "%s.%s" % (schema, table),
    #         "format": "PostgreSQL",
    #         "fields": d["field"],
    #     }
    # ]
    # d["metadata_version"] = "1.3"

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
