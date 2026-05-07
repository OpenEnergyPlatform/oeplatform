"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from copy import deepcopy

from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from . import APITestCaseWithTable

# from omi.validation import validate_metadata


class TestPut(APITestCaseWithTable):
    def metadata_roundtrip(self, meta):
        self.api_req("post", path="meta/", data=meta)
        omi_meta_return = self.api_req("get", path="meta/")

        # Use deepcopy so we don't mutate the original example constant
        omi_meta = deepcopy(meta)

        # ignore diff in keywords (by setting resulting keywords == input keywords)
        # REASON: the test re-uses the same test table,
        # but does not delete the table tags in between
        # if we want to synchronize tags and keywords, the roundtrip would otherwise
        # fail
        omi_meta["resources"][0]["keywords"] = omi_meta["resources"][0].get(
            "keywords", []
        )
        omi_meta_return["resources"][0]["keywords"] = omi_meta["resources"][0][
            "keywords"
        ]

        # ignore diff in schema (by setting resulting schema == input schema)
        # REASON: The backend now actively synchronizes the metadata 'schema.fields'
        # with the physical database columns. Since the test table's physical columns
        # differ from the OEMETADATA_V20_EXAMPLE dummy columns, they will naturally
        # differ.
        if "schema" in omi_meta_return["resources"][0]:
            omi_meta["resources"][0]["schema"] = omi_meta_return["resources"][0][
                "schema"
            ]

        self.assertDictEqualKeywise(
            omi_meta_return["resources"][0], omi_meta["resources"][0]
        )

    def test_nonexistent_key(self):
        mete_copy = deepcopy(OEMETADATA_V20_EXAMPLE)
        mete_copy["nonexistent_key"] = ""
        meta = mete_copy
        # This should fail, OMI now fails on excess keys and warns on missing keys
        self.api_req("post", path="meta/", data=meta)

    def test_set_meta(self):
        meta = deepcopy(OEMETADATA_V20_EXAMPLE)
        self.metadata_roundtrip(meta)

    def test_complete_metadata(self):
        meta = deepcopy(OEMETADATA_V20_EXAMPLE)
        self.metadata_roundtrip(meta)

    def test_column_sync_preserves_annotations(self):
        """
        Verify that the backend sync function correctly enforces physical DB constraints
        while strictly preserving human-entered ontology annotations (isAbout, etc.).
        """
        meta = deepcopy(OEMETADATA_V20_EXAMPLE)

        # 1. Create custom column payload
        custom_columns = [
            {
                "name": "id",
                "type": "text",  # Intentionally wrong (should sync to bigint...)
                "nullable": True,  # Intentionally wrong (id should sync to False)
                "isAbout": [
                    {
                        "@id": "http://openenergy-platform.org/ontology/oeo/OEO_00000001",  # noqa: E501
                        "name": "test identifier",
                    }
                ],
                "valueReference": [
                    {"@id": "http://example.com/ref", "name": "ref", "value": "val"}
                ],
            },
            {
                "name": "fake_ghost_column",  # Does not exist in the physical test DB
                "type": "varchar",
                "isAbout": [
                    {
                        "@id": "http://openenergy-platform.org/ontology/oeo/OEO_00000002",  # noqa: E501
                        "name": "ghost",
                    }
                ],
            },
        ]

        meta["resources"][0]["schema"]["fields"] = custom_columns

        # 2. Perform the API POST request
        self.api_req("post", path="meta/", data=meta)

        # 3. Perform the API GET request to retrieve the synced metadata
        synced_meta = self.api_req("get", path="meta/")
        synced_fields = synced_meta["resources"][0]["schema"].get("fields", [])

        # 4. Assertions
        field_names = [f.get("name") for f in synced_fields]

        # Assertion A: The 'fake_ghost_column' should have been wiped out by the sync
        self.assertNotIn("fake_ghost_column", field_names)

        # Assertion B: The 'id' column must exist
        self.assertIn("id", field_names)

        # Extract the reconciled 'id' column
        id_field = next(f for f in synced_fields if f.get("name") == "id")

        # Assertion C: Physical constraints must be strictly enforced
        self.assertFalse(id_field.get("nullable"))  # Enforced to False by backend sync
        self.assertNotEqual(
            id_field.get("type"), "text"
        )  # Enforced to match actual DB type (e.g. bigint)

        # Assertion D: Human annotations must be perfectly preserved!
        self.assertEqual(len(id_field.get("isAbout", [])), 1)
        self.assertEqual(id_field["isAbout"][0]["name"], "test identifier")

        self.assertEqual(len(id_field.get("valueReference", [])), 1)
        self.assertEqual(id_field["valueReference"][0]["value"], "val")
