# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

from copy import deepcopy

from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from . import APITestCaseWithTable

# from omi.validation import validate_metadata


class TestPut(APITestCaseWithTable):
    def metadata_roundtrip(self, meta):
        self.api_req("post", path="meta/", data=meta)
        omi_meta_return = self.api_req("get", path="meta/")

        omi_meta = meta

        # ignore diff in keywords (by setting resulting keywords == input keywords)
        # REASON: the test re-uses the same test table,
        # but does not delete the table tags in between
        # if we want to synchronize tagsand keywords, the roundtrip would otherwise fail
        omi_meta["resources"][0]["keywords"] = omi_meta["resources"][0].get(
            "keywords", []
        )
        omi_meta_return["resources"][0]["keywords"] = omi_meta["resources"][0][
            "keywords"
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
        meta = OEMETADATA_V20_EXAMPLE
        self.metadata_roundtrip(meta)

    def test_complete_metadata(self):
        meta = OEMETADATA_V20_EXAMPLE

        self.metadata_roundtrip(meta)
