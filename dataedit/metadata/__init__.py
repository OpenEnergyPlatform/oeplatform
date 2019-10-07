from api import actions
from dataedit.metadata import v1_3 as __LATEST

from .error import MetadataException


def load_comment_from_db(schema, table):
    """Get comment for a table in OEP database (contains the metadata)

    :param schema: name of the OEP schema
    :param table: name of the OEP table in the OEP schema
    :return:
    """
    comment = actions.get_comment_table(schema, table)
    if "error" in comment:
        return comment
    if not comment:
        comment_on_table = __LATEST.get_empty(schema, table)
    else:
        if "error" in comment:
            return {"description": comment["content"], "error": comment["error"]}
        try:
            version = get_metadata_version(comment)
            if version:
                if not isinstance(version, tuple):
                    version = (version,)
                if len(version) < 2:
                    version = (version[0], 0)
                if version[0] == 1:
                    if version[1] == 1:
                        comment_on_table = __LATEST.from_v1_1(comment, schema, table)
                    elif version[1] == 2:
                        comment_on_table = __LATEST.from_v1_2(comment)
                    elif version[1] == 3:
                        comment_on_table = comment
                        # This is not part of the actual metadata-schema. We move the fields to
                        # a higher level in order to avoid fetching the first resource in the
                        # templates.
                        comment_on_table["fields"] = comment_on_table["resources"][0]["fields"]

                    elif version[1] == 4:
                        comment_on_table = comment
                        # This is not part of the actual metadata-schema. We move the fields to
                        # a higher level in order to avoid fetching the first resource in the
                        # templates.
                        comment_on_table["fields"] = comment_on_table["resources"][0]["schema"]["fields"]
                elif version[0] == 0:
                    comment_on_table = __LATEST.from_v0(comment, schema, table)
                else:
                    comment_on_table = comment
            else:
                comment_on_table = __LATEST.from_v0(comment, schema, table)
        except MetadataException as me:
            return {
                "description": comment,
                "error": me.error.message
                if hasattr(me.error, "message")
                else str(me.error),
            }

    return comment_on_table


def read_metadata_from_post(c, schema, table):
    d = {
        "title": c["title"],
        "description": c["description"],
        "spatial": {
            "location": c["spatial_location"],
            "extent": c["spatial_extend"],
            "resolution": c["spatial_resolution"],
        },
        "temporal": {
            "reference_date": c["temporal_reference_date"],
            "start": c["temporal_start"],
            "end": c["temporal_end"],
            "resolution": c["temporal_resolution"],
        },
        "license": {
            "id": c["license_id"],
            "name": c["license_name"],
            "version": c["license_version"],
            "url": c["license_url"],
            "instruction": c["license_instruction"],
            "copyright": c["license_copyright"],
        },
    }

    for prefix, f, props in [
        ("language", load_language, 1),
        ("sources", load_sources, 5),
        ("contributors", load_contributors, 4),
        ("field", load_field, 3),
    ]:
        count = len([(k, c[k]) for k in c if k.startswith(prefix)]) // props
        d[prefix] = [
            f(
                {
                    k[len("%s%d" % (prefix, i + 1)) + 1 :]: c[k]
                    for k in c
                    if k.startswith("%s%d" % (prefix, i + 1))
                }
            )
            for i in range(count)
        ]

    d["resources"] = [
        {
            "name": "%s.%s" % (schema, table),
            "format": "PostgreSQL",
            "fields": d["field"],
        }
    ]
    d["metadata_version"] = "1.3"
    del d["field"]

    return d


def load_sources(x):
    return {
        "name": x["name"],
        "description": x["description"],
        "url": x["url"],
        "license": x["license"],
        "copyright": x["copyright"],
    }


def load_language(x):
    # This looks weird, but makes things way more convenient
    # all other 'load'-functions expect dictionaries but languages do not have
    # labels. Thus, for the sake of convenience, an empty label is generated.
    return x[""]


def load_contributors(x):
    return x


def load_field(x):
    return {"name": x["name"], "description": x["description"], "unit": x["unit"]}


def load_metaversion(x):
    return x[""]


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
