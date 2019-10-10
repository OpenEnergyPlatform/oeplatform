from api import actions
from dataedit.metadata import v1_3 as __LATEST

from dataedit.metadata.v1_4 import TEMPLATE_V1_4

from .error import MetadataException

# name of the metadata fields which should not be filled by the user
METADATA_HIDDEN_FIELDS = [
    '_comment',  # v1.4
    'resources',  # v1.4
    'metaMetadata',  # v1.4
    'metadata_version'  # v1.3
]
# names of the metadata fields which have string values
STR_FIELD = [
    "name",
    "title",
    "id",
    "description",
    "publicationDate"
]
# names of the metadata fields which have dict values
DICT_FIELD = [
    "context",
    "spatial",
    "temporal",
    "review",
    "timeseries"
]
# name of the metadata fields which have list values
LIST_FIELD = [
    "language",
    "keywords",
    "sources",
    "licenses",
    "contributors",
    "resources",
    "fields"
]



def load_metadata_from_db(schema, table):
    """Get comment for a table in OEP database (contains the metadata)

    :param schema: name of the OEP schema
    :param table: name of the OEP table in the OEP schema
    :return:
    """
    metadata = actions.get_comment_table(schema, table)
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
                        metadata["fields"] = metadata["resources"][0]["fields"]

                    elif version[1] == 4:
                        # This is not part of the actual metadata-schema. We move the fields to
                        # a higher level in order to avoid fetching the first resource in the
                        # templates.
                        metadata["fields"] = metadata["resources"][0]["schema"]["fields"]
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

    def format_content_key(parent, k):
        if parent != '':
            answer = '{}_{}'.format(parent, k)
        else:
            answer = k

        return answer

    def assign_content_values(content, template=None, parent=''):
        """Match a query dict onto a nested structure

        example :
        content = {
            "name": ["Example"]
            "sources0_title": ["S0"],
            "sources0_description": ["desc S0"],
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
                    "licenses": [
                        {
                            "name": "",
                            "title": "",
                            "path": "",
                            "instruction": "",
                            "attribution": ""
                        }
                    ]
                }
            ],
            "licenses": [
                {
                    "name": "",
                    "title": "",
                    "path": "",
                    "instruction": "",
                    "attribution": ""
                }
            ],
        }

        template_dict["sources"][0]["title"] will have the values contained in
        content["sources0_title"]

        :param content: query dict
        :param template: dict (can be nested dicts)
        :param parent: a parameter to link content keys with the nested structure of template
        :return: the template with assigned values from the content query dict
        """

        if template is not None:
            for k in template:
                if k not in METADATA_HIDDEN_FIELDS:
                    if k in DICT_FIELD:
                        # the value is a dict, so we make a recursive call
                        template[k] = assign_content_values(
                            content=content,
                            template=template[k],
                            parent=format_content_key(parent, k)
                        )
                    elif k in LIST_FIELD:
                        # the value is a list, so we make a recursive call on the unique instances
                        # in the list

                        # find the matches with the prefix in the content
                        prefix = format_content_key(parent, k)
                        matches = [i for i in content if i.startswith(prefix)]

                        # count the number of instances among the matches
                        # (in case of list of dicts, this is not equal to the number of matches)
                        count = []
                        for i in matches:
                            num = i.replace(prefix, '').split('_')[0]
                            if num not in count:
                                count.append(num)
                        count = len(count)

                        item_list = []
                        is_dict = isinstance(template[k][0], dict)
                        for j in range(count):
                            if is_dict:
                                # it is a list of dict
                                item_list.append(assign_content_values(
                                    content=content,
                                    template=template[k][0],
                                    parent=format_content_key(parent, f'{k}{j}')))
                            else:
                                # it is a list of string
                                item_list.append(
                                    assign_content_values(
                                        content=content[format_content_key(parent, f'{k}{j}')][0]
                                    )
                                )

                    elif k in STR_FIELD:
                        template[k] = content[format_content_key(parent, k)]
        else:
            template = content
        return template

    metadata = assign_content_values(content=content_query, template=TEMPLATE_V1_4.copy())

    # TODO fill the "resource" field here
    # d["resources"] = [
    #     {
    #         "name": "%s.%s" % (schema, table),
    #         "format": "PostgreSQL",
    #         "fields": d["field"],
    #     }
    # ]
    # d["metadata_version"] = "1.3"
    # del d["field"]

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
    if version_string.count('.') == 1:
        version_string = version_string + '.0'
    return tuple(map(int, version_string.split(".")))
