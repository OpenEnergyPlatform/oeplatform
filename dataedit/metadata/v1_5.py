from omi.dialects.oep.dialect import OEP_V_1_5_Dialect
from api import actions

TEMPLATE_V1_5 = {
    "name": None,
    "title": None,
    "id": None,
    "description": None,
    "language": None,
    "subject": 
        {
            "name": None,
            "path": None
        },
    "keywords": None,
    "publicationDate": None,
    "context": {
        "homepage": None,
        "documentation": None,
        "sourceCode": None,
        "contact": None,
        "grantNo": None,
        "fundingAgency": None,
        "fundingAgencyLogo": None,
        "publisherLogo": None
    },
    "spatial": {
        "location": None,
        "extent": None,
        "resolution": None
    },
    "temporal": {
        "referenceDate": None,
        "timeseries": 
            {
                "start": None,
                "end": None,
                "resolution": None,
                "alignment": None,
                "aggregationType": None
            }
    },
    "sources": 
        {
            "title": None,
            "description": None,
            "path": None,
            "licenses": [
                {
                    "name": None,
                    "title": None,
                    "path": None,
                    "instruction": None,
                    "attribution": None
                }
            ]
        },
    "licenses": 
        {
            "name": None,
            "title": None,
            "path": None,
            "instruction": None,
            "attribution": None
        },
    "contributors":
        {
            "title": None,
            "email": None,
            "date": None,
            "object": None,
            "comment": None
        },
    "resources": [
        {
            "profile": None,
            "name": None,
            "path": None,
            "format": None,
            "encoding": None,
            "schema": {
                "fields": [
                    {
                        "name": None,
                        "description": None,
                        "type": None,
                        "unit": None,
                        "isAbout": [
                            {
                                "name": None,
                                "path": None
                            }
                        ],
                        "valueReference": [
                            {
                                "value": None,
                                "name": None,
                                "path": None
                            }
                        ]
                    },
                    {
                        "name": None,
                        "description": None,
                        "type": None,
                        "unit": None,
                        "isAbout": [
                            {
                                "name": None,
                                "path": None
                            }
                        ],
                        "valueReference": [
                            {
                                "value": None,
                                "name": None,
                                "path": None
                            }
                        ]
                    }
                ],
                "primaryKey": [
                    None
                ],
                "foreignKeys": [
                    {
                        "fields": [
                            None
                        ],
                        "reference": {
                            "resource": None,
                            "fields": [
                                None
                            ]
                        }
                    }
                ]
            },
            "dialect": {
                "delimiter": None,
                "decimalSeparator": "."
            }
        }
    ],
    "@id": None,
    "@context": None,
    "review": {
        "path": None,
        "badge": None
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
        "Null": "If not applicable use: Null",
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