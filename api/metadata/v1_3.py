from api import actions

from . import v1_2


TEMPLATE_v1_3 = {
    "title": "",
    "description": "",
    "language": [""],
    "spatial":
        {
            "location": "",
            "extent": "",
            "resolution": ""
        },
    "temporal":
        {
            "reference_date": "",
            "start": "",
            "end": "",
            "resolution": ""
        },
    "sources": [
        {"name": "", "description": "", "url": "", "license": "", "copyright": ""},
    ],
    "license":
        {
            "id": "",
            "name": "",
            "version": "",
            "url": "",
            "instruction": "",
            "copyright": ""
        },
    "contributors": [
        {"name": "", "email": "", "date": "", "comment": ""},
    ],
    "resources": [
        {
            "name": "",
            "format": "",
            "fields": [
                {"name": "id", "description": "", "unit": ""},
                {"name": "year", "description": "", "unit": ""},
                {"name": "value", "description": "", "unit": ""},
                {"name": "geom", "description": "", "unit": ""}
            ]
        }
    ],
    "metadata_version": "1.3",
    "_comment": {
        "_url": "https://github.com/OpenEnergyPlatform/examples/tree/master/metadata",
        "_copyright": "© Reiner Lemoine Institut",
        "_metadata_license": "Creative Commons Zero v1.0 Universal (CC0-1.0)",
        "_metadata_license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "_contains": " http://www.json.org/; http://stackoverflow.com/questions/383692/what-is-json-and-why-would-i-use-it",
        "_additional_information": {
            "_dates": "Dates must follow the ISO8601 (JJJJ-MM-TT)",
            "_units": "Use a space between Numbers and units (100 m)",
            "_none": "If not applicable use 'none'"
        }
    }
}


def from_v1_2(comment_on_table):
    if comment_on_table.get("spatial", False):
        comment_on_table["spatial"] = comment_on_table["spatial"][0]
    else:
        comment_on_table["spatial"] = (
            {"location": "", "extent": "", "resolution": ""},
        )

    comment_on_table["temporal"] = {
        "reference_date": comment_on_table.get("reference_date", ""),
        "start": "",
        "end": "",
        "resolution": "",
    }

    proper_license = False
    if comment_on_table.get("license", False):
        licenses = comment_on_table.get("license", [])
        if licenses:
            comment_on_table["license"] = licenses[0]
            proper_license = True

    if not proper_license:
        comment_on_table["license"] = {
            "id": "",
            "name": "",
            "version": "",
            "url": "",
            "instruction": "",
            "copyright": "",
        }

    for i in range(len(comment_on_table["resources"])):
        comment_on_table["resources"][i] = {
            "name": "",
            "format": "PostgreSQL",
            "fields": comment_on_table["resources"][i]["schema"]["fields"],
        }

    comment_on_table["metadata_version"] = "1.3"

    return comment_on_table


def from_v1_1(comment_on_table, schema, table):
    return from_v1_2(v1_2.from_v1_1(comment_on_table, schema, table))


def from_v0(comment_on_table, schema, table):
    return from_v1_2(v1_2.from_v0(comment_on_table, schema, table))


def get_empty(schema, table):
    columns = actions.analyze_columns(schema, table)
    comment_on_table = {
        "title": "",
        "description": "",
        "language": ["eng"],
        "spatial": {"location": "", "extent": "", "resolution": ""},
        "temporal": {"reference_date": "", "start": "", "end": "", "resolution": ""},
        "sources": [
            {"name": "", "description": "", "url": "", "license": "", "copyright": ""}
        ],
        "license": {
            "id": "",
            "name": "",
            "version": "",
            "url": "",
            "instruction": "",
            "copyright": "",
        },
        "contributors": [],
        "resources": [
            {
                "name": "",
                "format": "PostgreSQL",
                "fields": [
                    {"name": col["id"], "description": "", "unit": ""}
                    for col in columns
                ],
            }
        ],
        "metadata_version": "1.3",
    }
    return comment_on_table
