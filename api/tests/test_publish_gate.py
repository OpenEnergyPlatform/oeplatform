"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The stored Publish gate verdict through the API (#2560, spec #2551): the one
metadata write path recomputes ``Table.publishable`` with every write, table
creation included, and publishing validates live, never trusting the flag.
"""  # noqa: 501

from copy import deepcopy

from oemetadata.v2.v20.example import OEMETADATA_V20_EXAMPLE

from dataedit.models import Table
from oeplatform.settings import TOPIC_SCENARIO

from . import APITestCaseWithTable


def without_license(metadata):
    metadata = deepcopy(metadata)
    metadata["resources"][0]["licenses"] = []
    return metadata


class StoredPublishGateTests(APITestCaseWithTable):
    test_table = "test_table_publish_gate"

    def stored(self):
        return Table.objects.get(name=self.test_table).publishable

    def test_creating_a_table_stores_a_verdict(self):
        """Creation writes template metadata through the one path, so a new
        Table is never left without a verdict; the template has no license."""
        self.assertIs(self.stored(), False)

    def test_every_metadata_write_recomputes_it(self):
        self.api_req("post", path="meta/", data=deepcopy(OEMETADATA_V20_EXAMPLE))
        self.assertIs(self.stored(), True)
        self.api_req("post", path="meta/", data=without_license(OEMETADATA_V20_EXAMPLE))
        self.assertIs(self.stored(), False)

    def test_publishing_validates_live_and_ignores_a_stale_flag(self):
        # a write past the one path leaves the flag claiming a pass
        Table.objects.filter(name=self.test_table).update(publishable=True)
        self.api_req("post", path=f"move_publish/{TOPIC_SCENARIO}/", exp_code=400)
        self.assertFalse(Table.objects.get(name=self.test_table).is_publish)
