"""Shared fixtures for the scenario-bundle API tests.

The base class and the one valid payload live here rather than in a test
module, so the create tests and the patch tests use the same bundle and cannot
drift into testing two different things. `oekg/tests/__init__.py` holds the
graph seam; this holds what a bundle looks like.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from login.models import myuser
from oekg.bundles import OEO
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests import OekgGraphAPITestCase

# Real picks from the shape's own sh:in lists -- the four the shape requires.
VALID_PAYLOAD = {
    "label": "A scenario bundle written by the API",
    "acronym": "API-TEST",
    "abstract": "Created by the test suite.",
    "descriptors": [str(OEO.OEO_00000143)],
    "sector_divisions": [str(OEO.OEO_00000368)],
    "sectors": [str(OEO.OEO_00000367)],
    "technologies": [str(OEO.OEO_00000407)],
}


class BundleApiTestCase(OekgGraphAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = myuser.objects.create_user(
            name="bundle-author", email="author@example.org", affiliation=""
        )
        self.collection_url = reverse("api:scenario-bundles")

    def create(self, payload=None, authenticate=True):
        if authenticate:
            self.client.force_login(self.user)
        return self.client.post(
            self.collection_url,
            data=payload if payload is not None else VALID_PAYLOAD,
            content_type="application/json",
        )

    def detail_url(self, uid):
        return reverse("api:scenario-bundle", kwargs={"uid": uid})

    def created(self, payload=None):
        """Create a bundle and return its identifier and its entity tag."""
        response = self.create(payload)
        self.assertEqual(response.status_code, 201, response.data)
        return response.data[READ_ONLY_CONTAINER]["uid"], response["ETag"]

    def patch(self, uid, payload, if_match=None, authenticate=True):
        if authenticate:
            self.client.force_login(self.user)
        headers = {} if if_match is None else {"HTTP_IF_MATCH": if_match}
        return self.client.patch(
            self.detail_url(uid),
            data=payload,
            content_type="application/json",
            **headers,
        )
