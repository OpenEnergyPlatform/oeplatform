"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

from django.test import TestCase
from django.urls import reverse

from factsheet.models import ScenarioBundleAccessControl
from login.models import myuser as User


class CheckOwnershipViewTests(TestCase):
    bundle_id = "6157d6d6-7a7b-a61e-21d3-a8f936b19056"

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            name="owner", email="owner@test.test", affiliation="test"
        )
        cls.other_user = User.objects.create_user(
            name="other", email="other@test.test", affiliation="test"
        )
        cls.admin = User.objects.create_user(
            name="admin", email="admin@test.test", affiliation="test", is_admin=True
        )
        ScenarioBundleAccessControl.objects.create(
            owner_user=cls.owner, bundle_id=cls.bundle_id
        )

    def _check(self, user, bundle_id=None):
        self.client.force_login(user)
        url = reverse(
            "factsheet:check_ownership",
            kwargs={"bundle_id": bundle_id or self.bundle_id},
        )
        return self.client.get(url)

    def test_new_bundle_is_owner_and_can_edit(self):
        response = self._check(self.other_user, bundle_id="new")
        data = json.loads(response.content)
        self.assertTrue(data["isOwner"])
        self.assertTrue(data["canEdit"])

    def test_owner_can_edit_and_delete(self):
        response = self._check(self.owner)
        data = json.loads(response.content)
        self.assertTrue(data["isOwner"])
        self.assertTrue(data["canEdit"])

    def test_non_owner_cannot_edit_or_delete(self):
        response = self._check(self.other_user)
        data = json.loads(response.content)
        self.assertFalse(data["isOwner"])
        self.assertFalse(data["canEdit"])

    def test_admin_can_edit_but_not_delete(self):
        response = self._check(self.admin)
        data = json.loads(response.content)
        self.assertFalse(data["isOwner"])
        self.assertTrue(data["canEdit"])

    def test_unauthenticated_user_gets_401(self):
        url = reverse(
            "factsheet:check_ownership", kwargs={"bundle_id": self.bundle_id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data["isOwner"])
        self.assertFalse(data["canEdit"])
