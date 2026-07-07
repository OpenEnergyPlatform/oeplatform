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
from oeplatform.settings import PSEUDO_TOPIC_DRAFT


class PublicDatasetListTests(TestCase):
    """Public, paginated card list of the datasets in one topic."""

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
        cls.topic = Topic.objects.create(name="energy")
        cls.list_url = reverse("dataedit:datasets-in-topic", kwargs={"topic": "energy"})

    def make_dataset(self, name, creator=None, table_names=(), topic=...):
        dataset = Dataset.objects.create(
            name=name,
            metadata={
                "name": name,
                "title": f"Title of {name}",
                "description": f"Description of {name}",
            },
            creator=creator or self.user,
        )
        if topic is ...:
            topic = self.topic
        if topic is not None:
            dataset.topics.add(topic)
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

    def test_lists_only_datasets_of_the_topic(self):
        other_topic = Topic.objects.create(name="mobility")
        self.make_dataset("in_topic")
        self.make_dataset("other_topic_ds", topic=other_topic)
        self.make_dataset("untopiced_ds", topic=None)

        response = self.client.get(self.list_url)
        self.assertContains(response, "in_topic")
        self.assertNotContains(response, "other_topic_ds")
        self.assertNotContains(response, "untopiced_ds")

    def test_unknown_topic_is_404(self):
        response = self.client.get(
            reverse("dataedit:datasets-in-topic", kwargs={"topic": "no_such"})
        )
        self.assertEqual(response.status_code, 404)

    def test_draft_pseudo_topic_has_no_dataset_list(self):
        Topic.objects.get_or_create(name=PSEUDO_TOPIC_DRAFT)
        response = self.client.get(
            reverse("dataedit:datasets-in-topic", kwargs={"topic": PSEUDO_TOPIC_DRAFT})
        )
        self.assertEqual(response.status_code, 404)

    def test_pagination(self):
        for index in range(ITEMS_PER_PAGE + 1):
            self.make_dataset(f"ds_{index:03d}")

        first_page = self.client.get(self.list_url)
        second_page = self.client.get(self.list_url, {"page": 2})
        self.assertContains(first_page, "page=2")
        # newest first: the oldest dataset lands on page 2
        self.assertContains(second_page, "ds_000")

    def test_table_list_toggle_links_to_datasets_in_same_topic(self):
        response = self.client.get(
            reverse("dataedit:tables-in-topic", kwargs={"topic": "energy"})
        )
        self.assertContains(response, self.list_url)
        self.assertNotContains(response, "coming soon")

    def test_dataset_list_toggle_links_to_tables_in_same_topic(self):
        response = self.client.get(self.list_url)
        self.assertContains(
            response,
            reverse("dataedit:tables-in-topic", kwargs={"topic": "energy"}),
        )

    def test_global_dataset_url_redirects_to_topic_overview(self):
        response = self.client.get(reverse("dataedit:dataset-list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dataedit:topic-list"))
