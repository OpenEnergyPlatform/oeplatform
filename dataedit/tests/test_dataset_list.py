"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest import mock

from django.test import TestCase
from django.urls import reverse

from dataedit.models import Dataset, Table, Topic
from dataedit.views import ITEMS_PER_PAGE
from login.models import myuser


class PublicDatasetListTests(TestCase):
    """Public, paginated card list of all datasets in the dataedit app."""

    @classmethod
    def setUpTestData(cls):
        cls.user, _ = myuser.objects.get_or_create(
            name="PublicListUser",
            email="public-list-user@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.other_user, _ = myuser.objects.get_or_create(
            name="OtherPublicListUser",
            email="other-public-list-user@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.list_url = reverse("dataedit:dataset-list")

    def make_dataset(self, name, creator=None, table_names=()):
        dataset = Dataset.objects.create(
            name=name,
            metadata={
                "name": name,
                "title": f"Title of {name}",
                "description": f"Description of {name}",
            },
            creator=creator or self.user,
        )
        for table_name in table_names:
            table = Table.objects.create(
                name=table_name,
                is_publish=True,
                oemetadata={"resources": [{"name": table_name}]},
            )
            dataset.tables.add(table)
        return dataset

    def test_accessible_without_login(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_cards_show_name_description_count_and_size(self):
        self.make_dataset("public_ds", table_names=["t_a", "t_b"])

        sizes = [
            {"table_name": "t_a", "total_bytes": 1024},
            {"table_name": "t_b", "total_bytes": 2048},
            {"table_name": "t_unrelated", "total_bytes": 4096},
        ]
        with mock.patch("dataedit.views.list_table_sizes", return_value=sizes):
            response = self.client.get(self.list_url)

        self.assertContains(response, "public_ds")
        self.assertContains(response, "Description of public_ds")
        self.assertContains(response, "2 resource")
        # 1024 + 2048 bytes, unrelated tables excluded
        self.assertContains(response, "3.0")
        self.assertContains(response, "Total size")

    def test_lists_datasets_from_all_creators(self):
        self.make_dataset("mine")
        self.make_dataset("theirs", creator=self.other_user)

        response = self.client.get(self.list_url)
        self.assertContains(response, "mine")
        self.assertContains(response, "theirs")

    def test_pagination(self):
        for index in range(ITEMS_PER_PAGE + 1):
            self.make_dataset(f"ds_{index:03d}")

        first_page = self.client.get(self.list_url)
        second_page = self.client.get(self.list_url, {"page": 2})
        self.assertContains(first_page, "page=2")
        # newest first: the oldest dataset lands on page 2
        self.assertContains(second_page, "ds_000")

    def test_table_list_toggle_is_enabled_and_links_here(self):
        Topic.objects.create(name="toggle_topic")
        response = self.client.get(
            reverse("dataedit:tables-in-topic", kwargs={"topic": "toggle_topic"})
        )
        self.assertContains(response, self.list_url)
        self.assertNotContains(response, "coming soon")

    def test_dataset_list_links_back_to_table_list(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, reverse("dataedit:topic-list"))
