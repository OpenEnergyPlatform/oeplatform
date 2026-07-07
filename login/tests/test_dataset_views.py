"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase
from django.urls import reverse

from dataedit.models import Dataset
from login.models import myuser


class DatasetDashboardTests(TestCase):
    """The user dashboard opens dataset-first with a switch to My Tables."""

    @classmethod
    def setUpTestData(cls):
        cls.user, _ = myuser.objects.get_or_create(
            name="DashboardUser",
            email="dashboard-user@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.other_user, _ = myuser.objects.get_or_create(
            name="OtherDashboardUser",
            email="other-dashboard-user@test.com",
            did_agree=True,
            is_mail_verified=True,
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.datasets_url = reverse("login:datasets", args=[self.user.id])

    def create_dataset(self, name, creator=None):
        return Dataset.objects.create(
            name=name,
            metadata={"name": name, "title": name, "description": ""},
            creator=creator or self.user,
        )

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.datasets_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_profile_opens_dataset_first(self):
        response = self.client.get(reverse("login:profile", args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create dataset")

    def test_lists_only_own_datasets(self):
        self.create_dataset("my_dataset")
        self.create_dataset("foreign_dataset", creator=self.other_user)

        response = self.client.get(self.datasets_url)
        self.assertContains(response, "my_dataset")
        self.assertNotContains(response, "foreign_dataset")

    def test_view_switch_links_to_tables_view(self):
        response = self.client.get(self.datasets_url)
        self.assertContains(response, reverse("login:tables", args=[self.user.id]))

    def test_create_dataset_via_post(self):
        response = self.client.post(
            self.datasets_url,
            {
                "name": "fresh_dataset",
                "title": "Fresh Dataset",
                "description": "Created from the dashboard",
            },
        )
        self.assertEqual(response.status_code, 200)
        dataset = Dataset.objects.get(name="fresh_dataset")
        self.assertEqual(dataset.creator, self.user)
        self.assertContains(response, "fresh_dataset")

    def test_create_returns_partial_not_full_page(self):
        response = self.client.post(
            self.datasets_url,
            {
                "name": "partial_dataset",
                "title": "Partial",
                "description": "HTMX swap target only",
            },
        )
        self.assertNotContains(response, "<html")

    def test_create_invalid_slug_shows_inline_error(self):
        response = self.client.post(
            self.datasets_url,
            {
                "name": "not a slug!",
                "title": "Bad",
                "description": "Should fail",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Dataset.objects.filter(metadata__title="Bad").exists())
        self.assertContains(response, "name")
        self.assertContains(response, "invalid-feedback")

    def test_create_duplicate_name_shows_inline_error(self):
        self.create_dataset("taken_name")
        response = self.client.post(
            self.datasets_url,
            {
                "name": "taken_name",
                "title": "Duplicate",
                "description": "Should fail",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Dataset.objects.filter(name="taken_name").count(), 1)
        self.assertContains(response, "invalid-feedback")

    def test_cannot_create_on_foreign_profile(self):
        response = self.client.post(
            reverse("login:datasets", args=[self.other_user.id]),
            {
                "name": "sneaky_dataset",
                "title": "Sneaky",
                "description": "Posting on someone else's dashboard",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Dataset.objects.filter(name="sneaky_dataset").exists())

    def test_tables_view_still_works(self):
        response = self.client.get(reverse("login:tables", args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "tables")
