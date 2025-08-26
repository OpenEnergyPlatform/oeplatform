# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.  # noqa: E501
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut  # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import reverse

from api.tests import APITestCase


class Test_issue_832_tag_filter_with_missing_tag(APITestCase):
    def test_issue_832_tag_filter_with_missing_tag(self):
        # index without filter
        res = self.client.post(reverse("dataedit:index"))
        self.assertEqual(res.status_code, 200)

        # index with tag filter with non existent tag_id
        res = self.client.post(reverse("dataedit:index") + "?tags=-1")
        self.assertEqual(res.status_code, 200)

        # index with tag filter with invalid tag_id
        res = self.client.post(reverse("dataedit:index") + "?tags=xxx")
        self.assertEqual(res.status_code, 404)
