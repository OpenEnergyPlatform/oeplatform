"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest import mock

from django.test import TestCase
from django.urls import reverse

from dataedit.models import Dataset, Table, Tag, Topic
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

    def test_draft_pseudo_topic_shows_placeholder_instead_of_datasets(self):
        # the page must not 404 (the toggle links here from the draft
        # table list) but never lists datasets either
        self.make_dataset("never_a_draft_listing", topic=None)

        response = self.client.get(
            reverse("dataedit:datasets-in-topic", kwargs={"topic": PSEUDO_TOPIC_DRAFT})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Datasets are not listed under the draft topic")
        self.assertNotContains(response, "never_a_draft_listing")

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


class DatasetListFilterTests(TestCase):
    """Search and tag filter on the topic dataset list: text matches name,
    title and description; a dataset carries a tag when any member table
    does, several tags AND together (mirroring the table filter)."""

    @classmethod
    def setUpTestData(cls):
        cls.user, _ = myuser.objects.get_or_create(
            name="FilterUser",
            email="filter-user@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.topic = Topic.objects.create(name="power")
        cls.list_url = reverse("dataedit:datasets-in-topic", kwargs={"topic": "power"})
        cls.tag_hourly = Tag.objects.create(name="hourly")
        cls.tag_open = Tag.objects.create(name="open")

    def make_dataset(self, name, title=None, description=None, tags_by_table=()):
        dataset = Dataset.objects.create(
            name=name,
            metadata={
                "name": name,
                "title": title or f"Title of {name}",
                "description": description or f"Description of {name}",
            },
            creator=self.user,
        )
        dataset.topics.add(self.topic)
        for index, tags in enumerate(tags_by_table):
            table = Table.objects.create(
                name=f"{name}_t{index}",
                is_publish=True,
                oemetadata={"resources": [{"name": f"{name}_t{index}"}]},
            )
            table.tags.add(*tags)
            dataset.tables.add(table)
        return dataset

    def test_query_matches_dataset_name(self):
        self.make_dataset("wind_power_ds")
        self.make_dataset("solar_ds")

        response = self.client.get(self.list_url, {"query": "wind"})
        self.assertContains(response, "wind_power_ds")
        self.assertNotContains(response, "solar_ds")

    def test_query_matches_title_and_description_case_insensitively(self):
        self.make_dataset("first_ds", title="Grid Expansion Study")
        self.make_dataset("second_ds", description="Contains grid measurements")
        self.make_dataset("third_ds")

        response = self.client.get(self.list_url, {"query": "GRID"})
        self.assertContains(response, "first_ds")
        self.assertContains(response, "second_ds")
        self.assertNotContains(response, "third_ds")

    def test_tag_matches_via_any_member_table(self):
        self.make_dataset("tagged_ds", tags_by_table=[[self.tag_hourly]])
        self.make_dataset("untagged_ds", tags_by_table=[[]])

        response = self.client.get(self.list_url, {"tags": [self.tag_hourly.pk]})
        self.assertContains(response, "tagged_ds")
        self.assertNotContains(response, "untagged_ds")

    def test_multiple_tags_and_together_across_member_tables(self):
        # the two tags sit on different member tables of the same dataset
        self.make_dataset(
            "both_tags_ds", tags_by_table=[[self.tag_hourly], [self.tag_open]]
        )
        self.make_dataset("one_tag_ds", tags_by_table=[[self.tag_hourly]])

        response = self.client.get(
            self.list_url, {"tags": [self.tag_hourly.pk, self.tag_open.pk]}
        )
        self.assertContains(response, "both_tags_ds")
        self.assertNotContains(response, "one_tag_ds")

    def test_query_and_tags_combine(self):
        self.make_dataset("wind_tagged_ds", tags_by_table=[[self.tag_hourly]])
        self.make_dataset("wind_untagged_ds", tags_by_table=[[]])
        self.make_dataset("solar_tagged_ds", tags_by_table=[[self.tag_hourly]])

        response = self.client.get(
            self.list_url, {"query": "wind", "tags": [self.tag_hourly.pk]}
        )
        self.assertContains(response, "wind_tagged_ds")
        self.assertNotContains(response, "wind_untagged_ds")
        self.assertNotContains(response, "solar_tagged_ds")

    def test_form_keeps_query_state(self):
        self.make_dataset("stateful_ds")
        response = self.client.get(self.list_url, {"query": "stateful"})
        self.assertContains(response, 'value="stateful"')

    def test_pagination_preserves_query(self):
        for index in range(ITEMS_PER_PAGE + 1):
            self.make_dataset(f"windy_{index:03d}")

        response = self.client.get(self.list_url, {"query": "windy"})
        self.assertContains(response, "query=windy")
        second_page = self.client.get(self.list_url, {"query": "windy", "page": 2})
        self.assertContains(second_page, "windy_000")
