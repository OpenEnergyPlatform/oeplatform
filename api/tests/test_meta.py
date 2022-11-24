import json

from omi.dialects.oep.dialect import OEP_V_1_5_Dialect

from . import APITestCaseWithTable


class TestPut(APITestCaseWithTable):
    def metadata_roundtrip(self, meta):
        self.api_req("post", path="meta/", data=meta)
        omi_meta_return = self.api_req("get", path="meta/")

        d_15 = OEP_V_1_5_Dialect()
        omi_meta = json.loads(json.dumps((d_15.compile(d_15.parse(json.dumps(meta))))))

        # ignore diff in keywords (by setting resulting keywords == input keywords)
        # REASON: the test re-uses the same test table,
        # but does not delete the table tags in between
        # if we want to synchronize tagsand keywords, the roundtrip would otherwise fail
        omi_meta["keywords"] = omi_meta.get("keywords", [])
        omi_meta_return["keywords"] = omi_meta["keywords"]

        self.assertDictEqualKeywise(omi_meta_return, omi_meta)

    def test_nonexistent_key(self):
        meta = {"id": "id", "nonexistent_key": ""}
        # This should fail, but OMI does not warn about excess keys
        self.api_req("post", path="meta/", data=meta)

    def test_set_meta(self):
        meta = {"id": self.test_table}
        self.metadata_roundtrip(meta)

    def test_complete_metadata(self):
        null = None
        meta = {
            "name": "oep_metadata_table_example_v151",
            "title": "Example title for metadata example - Version 1.5.1",
            "id": "http://openenergyplatform.org/dataedit/view/model_draft/oep_metadata_table_example_v151",  # noqa
            "description": "This is an metadata example for example data. There is a corresponding table on the OEP for each metadata version.",  # noqa
            "language": ["en-GB", "en-US", "de-DE", "fr-FR"],
            "subject": [
                {
                    "name": "energy",
                    "path": "https://openenergy-platform.org/ontology/oeo/OEO_00000150",
                },
                {
                    "name": "test dataset",
                    "path": "https://openenergy-platform.org/ontology/oeo/OEO_00000408",
                },
            ],
            "keywords": ["energy", "example", "template", "test"],
            "publicationDate": "2022-02-15",
            "context": {
                "homepage": "https://reiner-lemoine-institut.de/lod-geoss/",
                "documentation": "https://openenergy-platform.org/tutorials/jupyter/OEMetadata/",  # noqa
                "sourceCode": "https://github.com/OpenEnergyPlatform/oemetadata/tree/master",  # noqa
                "contact": "https://github.com/Ludee",
                "grantNo": "03EI1005",
                "fundingAgency": "Bundesministerium für Wirtschaft und Klimaschutz",
                "fundingAgencyLogo": "https://commons.wikimedia.org/wiki/File:BMWi_Logo_2021.svg#/media/File:BMWi_Logo_2021.svg",  # noqa
                "publisherLogo": "https://reiner-lemoine-institut.de//wp-content/uploads/2015/09/rlilogo.png",  # noqa
            },
            "spatial": {"location": null, "extent": "europe", "resolution": "100 m"},
            "temporal": {
                "referenceDate": "2016-01-01",
                "timeseries": [
                    {
                        "start": "2017-01-01T00:00+01",
                        "end": "2017-12-31T23:00+01",
                        "resolution": "1 h",
                        "alignment": "left",
                        "aggregationType": "sum",
                    },
                    {
                        "start": "2018-01-01T00:00+01",
                        "end": "2019-06-01T23:00+01",
                        "resolution": "15 min",
                        "alignment": "right",
                        "aggregationType": "sum",
                    },
                ],
            },
            "sources": [
                {
                    "title": "OpenEnergyPlatform Metadata Example",
                    "description": "Metadata description",
                    "path": "https://github.com/OpenEnergyPlatform",
                    "licenses": [
                        {
                            "name": "CC0-1.0",
                            "title": "Creative Commons Zero v1.0 Universal",
                            "path": "https://creativecommons.org/publicdomain/zero/1.0/legalcode",  # noqa
                            "instruction": "You are free: To Share, To Create, To Adapt",  # noqa
                            "attribution": "© Reiner Lemoine Institut",
                        }
                    ],
                },
                {
                    "title": "OpenStreetMap",
                    "description": "A collaborative project to create a free editable map of the world",  # noqa
                    "path": "https://www.openstreetmap.org/",
                    "licenses": [
                        {
                            "name": "ODbL-1.0",
                            "title": "Open Data Commons Open Database License 1.0",
                            "path": "https://opendatacommons.org/licenses/odbl/1.0/index.html",  # noqa
                            "instruction": "You are free: To Share, To Create, To Adapt; As long as you: Attribute, Share-Alike, Keep open!",  # noqa
                            "attribution": "© OpenStreetMap contributors",
                        }
                    ],
                },
            ],
            "licenses": [
                {
                    "name": "ODbL-1.0",
                    "title": "Open Data Commons Open Database License 1.0",
                    "path": "https://opendatacommons.org/licenses/odbl/1.0/",
                    "instruction": "You are free: To Share, To Create, To Adapt; As long as you: Attribute, Share-Alike, Keep open!",  # noqa
                    "attribution": "© Reiner Lemoine Institut © OpenStreetMap contributors",  # noqa
                }
            ],
            "contributors": [
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2016-06-16",
                    "object": "metadata",
                    "comment": "Create metadata",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2016-11-22",
                    "object": "metadata",
                    "comment": "Update metadata",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2016-11-22",
                    "object": "metadata",
                    "comment": "Update header and license",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2017-03-16",
                    "object": "metadata",
                    "comment": "Add license to source",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2017-03-28",
                    "object": "metadata",
                    "comment": "Add copyright to source and license",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2017-05-30",
                    "object": "metadata",
                    "comment": "Release metadata version 1.3",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2017-06-26",
                    "object": "metadata",
                    "comment": "Move referenceDate into temporal and remove array",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2018-07-19",
                    "object": "metadata",
                    "comment": "Start metadata version 1.4",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2018-07-26",
                    "object": "data",
                    "comment": "Rename table and files",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2018-10-18",
                    "object": "metadata",
                    "comment": "Add contribution object",
                },
                {
                    "title": "christian-rli",
                    "email": null,
                    "date": "2018-10-18",
                    "object": "metadata",
                    "comment": "Add datapackage compatibility",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2018-11-02",
                    "object": "metadata",
                    "comment": "Release metadata version 1.4",
                },
                {
                    "title": "christian-rli",
                    "email": null,
                    "date": "2019-02-05",
                    "object": "metadata",
                    "comment": "Apply template structure to example",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2019-03-22",
                    "object": "metadata",
                    "comment": "Hotfix foreignKeys",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2019-07-09",
                    "object": "metadata",
                    "comment": "Release metadata version OEP-1.3.0",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2021-11-15",
                    "object": "metadata",
                    "comment": "Release metadata version OEP-1.5.0",
                },
                {
                    "title": "Ludee",
                    "email": null,
                    "date": "2022-02-15",
                    "object": "metadata",
                    "comment": "Release metadata version OEP-1.5.1",
                },
            ],
            "resources": [
                {
                    "profile": "tabular-data-resource",
                    "name": "model_draft.oep_metadata_table_example_v151",
                    "path": "http://openenergyplatform.org/dataedit/view/model_draft/oep_metadata_table_example_v151",  # noqa
                    "format": "PostgreSQL",
                    "encoding": "UTF-8",
                    "schema": {
                        "fields": [
                            {
                                "name": "id",
                                "description": "Unique identifier",
                                "type": "serial",
                                "unit": null,
                                "isAbout": [{"name": null, "path": null}],
                                "valueReference": [
                                    {"value": null, "name": null, "path": null}
                                ],
                            },
                            {
                                "name": "name",
                                "description": "Example name",
                                "type": "text",
                                "unit": null,
                                "isAbout": [
                                    {
                                        "name": "written name",
                                        "path": "https://openenergy-platform.org/ontology/oeo/IAO_0000590",  # noqa
                                    }
                                ],
                                "valueReference": [
                                    {"value": null, "name": null, "path": null}
                                ],
                            },
                            {
                                "name": "type",
                                "description": "Type of wind farm",
                                "type": "text",
                                "unit": null,
                                "isAbout": [
                                    {
                                        "name": "wind farm",
                                        "path": "https://openenergy-platform.org/ontology/oeo/OEO_00000447",  # noqa
                                    }
                                ],
                                "valueReference": [
                                    {
                                        "value": "onshore ",
                                        "name": "onshore wind farm",
                                        "path": "https://openenergy-platform.org/ontology/oeo/OEO_00000311",  # noqa
                                    },
                                    {
                                        "value": "offshore ",
                                        "name": "offshore wind farm",
                                        "path": "https://openenergy-platform.org/ontology/oeo/OEO_00000308",  # noqa
                                    },
                                ],
                            },
                            {
                                "name": "year",
                                "description": "Reference year",
                                "type": "integer",
                                "unit": null,
                                "isAbout": [
                                    {
                                        "name": "year",
                                        "path": "https://openenergy-platform.org/ontology/oeo/UO_0000036",  # noqa
                                    }
                                ],
                                "valueReference": [
                                    {"value": null, "name": null, "path": null}
                                ],
                            },
                            {
                                "name": "value",
                                "description": "Example value",
                                "type": "double precision",
                                "unit": "MW",
                                "isAbout": [
                                    {
                                        "name": "quantity value",
                                        "path": "https://openenergy-platform.org/ontology/oeo/OEO_00000350",  # noqa
                                    }
                                ],
                                "valueReference": [
                                    {"value": null, "name": null, "path": null}
                                ],
                            },
                            {
                                "name": "geom",
                                "description": "Geometry",
                                "type": "geometry(Point, 4326)",
                                "unit": null,
                                "isAbout": [
                                    {
                                        "name": "spatial region",
                                        "path": "https://openenergy-platform.org/ontology/oeo/BFO_0000006",  # noqa
                                    }
                                ],
                                "valueReference": [
                                    {"value": null, "name": null, "path": null}
                                ],
                            },
                        ],
                        "primaryKey": ["id"],
                        "foreignKeys": [
                            {
                                "fields": ["year"],
                                "reference": {
                                    "resource": "schema.table",
                                    "fields": ["year"],
                                },
                            }
                        ],
                    },
                    "dialect": {"delimiter": null, "decimalSeparator": "."},
                }
            ],
            "@id": "https://databus.dbpedia.org/kurzum/mastr/bnetza-mastr/01.04.00",
            "@context": "https://github.com/OpenEnergyPlatform/oemetadata/blob/master/metadata/latest/context.json",  # noqa
            "review": {
                "path": "https://github.com/OpenEnergyPlatform/data-preprocessing/issues",  # noqa
                "badge": "Platinum",
            },
            "metaMetadata": {
                "metadataVersion": "OEP-1.5.1",
                "metadataLicense": {
                    "name": "CC0-1.0",
                    "title": "Creative Commons Zero v1.0 Universal",
                    "path": "https://creativecommons.org/publicdomain/zero/1.0/",
                },
            },
            "_comment": {
                "metadata": "Metadata documentation and explanation (https://github.com/OpenEnergyPlatform/oemetadata)",  # noqa
                "dates": "Dates and time must follow the ISO8601 including time zone (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss±hh)",  # noqa
                "units": "Use a space between numbers and units (100 m)",
                "languages": "Languages must follow the IETF (BCP47) format (en-GB, en-US, de-DE)",  # noqa
                "licenses": "License name must follow the SPDX License List (https://spdx.org/licenses/)",  # noqa
                "review": "Following the OEP Data Review (https://github.com/OpenEnergyPlatform/data-preprocessing/blob/master/data-review/manual/review_manual.md)",  # noqa
                "null": "If not applicable use: null",
                "todo": "If a value is not yet available, use: todo",
            },
        }

        self.metadata_roundtrip(meta)
