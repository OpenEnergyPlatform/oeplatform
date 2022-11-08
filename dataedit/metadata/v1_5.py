from omi.dialects.oep.dialect import OEP_V_1_5_Dialect
from api import actions

TEMPLATE_V1_5 = {
    "name": "",
    "title": "",
    "id": "",
    "description": "",
    "language": [],
    "subject": [
        {
            "name": "",
            "path": ""
        }
    ],
    "keywords": [],
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
        "timeseries": [
            {
                "start": "",
                "end": "",
                "resolution": "",
                "alignment": "",
                "aggregationType": ""
            },
            {
                "start": "",
                "end": "",
                "resolution": "",
                "alignment": "",
                "aggregationType": ""
            }
        ]
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
        {
            "title": "",
            "email": "",
            "date": "",
            "object": "",
            "comment": ""
        }
    ],
    "resources": [
        {
            "profile": "",
            "name": "",
            "path": "",
            "format": "",
            "encoding": "",
            "schema": {
                "fields": [],
                "primaryKey": [],
                "foreignKeys": []
            },
            "dialect": {
                "delimiter": "",
                "decimalSeparator": "."
            }
        }
    ],
    "@id": "",
    "@context": "",
    "review": {
        "path": "",
        "badge": ""
    },
    "metaMetadata": {
        "metadataVersion": "OEP-1.5.0",
        "metadataLicense": {
            "name": "CC0-1.0",
            "title": "Creative Commons Zero v1.0 Universal",
            "path": "https://creativecommons.org/publicdomain/zero/1.0/"
        }
    },
    "_comment": {
        "metadata": "Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/oemetadata)",
        "dates": "Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",
        "units": "Use a space between numbers and units (100 m)",
        "languages": "Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",
        "licenses": "License name must follow the SPDX License List (https://spdx.org/licenses/)",
        "review": "Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/blob/master/data-review/manual/review_manual.md)",
        "Null": "If not applicable use: 'Null'",
        "todo": "If a value is not yet available, use: todo"
    }
}


def get_empty(schema, table):
    template = TEMPLATE_V1_5.copy()
    columns = actions.analyze_columns(schema, table)
    # TODO: check how the fields should
    template["resources"][0]["schema"]["fields"] = [
        {"name": col["id"], "description": "", "unit": ""}
        for col in columns
    ]
    return template