from api import actions
from dataedit.metadata import v1_3

from omi.dialects.oep.dialect import OEP_V_1_3_Dialect, OEP_V_1_4_Dialect

TEMPLATE_V1_4 = {
    "name": "",
    "title": "",
    "id": "",
    "description": "",
    "language": [""],
    "keywords": [""],
    "publicationDate": "",
    "context": {
        "homepage": "",
        "documentation": "",
        "sourceCode": "",
        "contact": "",
        "grantNo": "",
        "fundingAgency": "",
        "fundingAgencyLogo": "",
        "publisherLogo": ""
    },
    "spatial": {
        "location": "",
        "extent": "",
        "resolution": ""
    },
    "temporal": {
        "referenceDate": "",
        "timeseries": {
            "start": "",
            "end": "",
            "resolution": "",
            "alignment": "",
            "aggregationType": ""
        }
    },
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
        },
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
    "contributors": [
        {"title": "", "email": "", "date": "", "object": "", "comment": ""},
        {"title": "", "email": "", "date": "", "object": "", "comment": ""}
    ],
    "resources": [
        {
            "profile": "",
            "name": "",
            "path": "",
            "format": "",
            "encoding" : "",
            "schema": {
                "fields": [
                    {"name": "", "description": "", "type": "", "unit": ""},
                    {"name": "", "description": "", "type": "", "unit": ""}
                ],
                "primaryKey": [""],
                "foreignKeys": [{
                    "fields": [""],
                    "reference": {
                        "resource": "",
                        "fields": [""] } } ] },
            "dialect":
                {
                    "delimiter": "",
                    "decimalSeparator": "."
                }
        }
    ],
    "review": {
        "path": "",
        "badge": ""
    },
    "metaMetadata":{
        "metadataVersion": "OEP-1.4.0",
        "metadataLicense":
            {
                "name": "CC0-1.0",
                "title": "Creative Commons Zero v1.0 Universal",
                "path": "https://creativecommons.org/publicdomain/zero/1.0/"
            }
    },
    "_comment":
        {
            ""
            "metadata": "Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/organisation/wiki/metadata)",
            "dates": "Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",
            "units": "Use a space between numbers and units (100 m)",
            "languages": "Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
            "licenses": "License name must follow the SPDX License List (https://spdx.org/licenses/)",
            "review": "Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/wiki)",
            "null": "If not applicable use (null)"
        }
}


def get_empty(schema, table):
    template = TEMPLATE_V1_4.copy()
    columns = actions.analyze_columns(schema, table)
    # TODO: check how the fields should
    template["resources"][0]["schema"]["fields"] = [
        {"name": col["id"], "description": "", "unit": ""}
        for col in columns
    ]
    return template


def from_v0(comment_on_table, schema, table):
    return from_v1_3(v1_3.from_v0(comment_on_table, schema, table))


def from_v1_1(comment_on_table, schema, table):
    return from_v1_3(v1_3.from_v1_1(comment_on_table, schema, table))


def from_v1_2(comment_on_table):
    return from_v1_3(v1_3.from_v1_2(comment_on_table))


def from_v1_3(comment):
    d13 = OEP_V_1_3_Dialect()
    d14 = OEP_V_1_4_Dialect()
    return d14.compile(d13._parser().parse(comment))
