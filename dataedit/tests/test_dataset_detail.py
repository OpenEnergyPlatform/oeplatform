"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest import mock

from django.test import TestCase
from django.urls import reverse

from dataedit.models import Dataset, Table, Topic
from login.models import myuser


class DatasetDetailTests(TestCase):
    """Public read view for one dataset at the flat datasets/<name> URL."""

    @classmethod
    def setUpTestData(cls):
        cls.creator, _ = myuser.objects.get_or_create(
            name="DetailCreator",
            email="detail-creator@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.visitor, _ = myuser.objects.get_or_create(
            name="DetailVisitor",
            email="detail-visitor@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.topic = Topic.objects.create(name="heat")

    def setUp(self):
        self.dataset = Dataset.objects.create(
            name="detailed_dataset",
            metadata={
                "name": "detailed_dataset",
                "title": "Detailed Dataset",
                "description": "Everything about heat",
            },
            creator=self.creator,
        )
        self.dataset.topics.add(self.topic)
        self.published = Table.objects.create(
            name="t_heat_published",
            is_publish=True,
            oemetadata={"resources": [{"name": "t_heat_published"}]},
        )
        self.draft = Table.objects.create(
            name="t_heat_draft",
            is_publish=False,
            oemetadata={"resources": [{"name": "t_heat_draft"}]},
        )
        self.dataset.tables.add(self.published, self.draft)
        self.detail_url = reverse(
            "dataedit:dataset-detail", kwargs={"dataset_name": "detailed_dataset"}
        )

    def test_renders_anonymously_with_header_and_description(self):
        sizes = [{"table_name": "t_heat_published", "total_bytes": 2048}]
        with mock.patch("dataedit.views.list_table_sizes", return_value=sizes):
            response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detailed Dataset")
        self.assertContains(response, "detailed_dataset")
        self.assertContains(response, "Everything about heat")
        self.assertContains(response, "heat")
        self.assertContains(response, "DetailCreator")
        self.assertContains(response, "2 resource")
        self.assertContains(response, "2.0")

    def test_unknown_dataset_is_404(self):
        response = self.client.get(
            reverse("dataedit:dataset-detail", kwargs={"dataset_name": "no_such"})
        )
        self.assertEqual(response.status_code, 404)

    def test_resources_link_to_table_pages_with_draft_badge(self):
        response = self.client.get(self.detail_url)
        self.assertContains(
            response, reverse("dataedit:view", kwargs={"table": "t_heat_published"})
        )
        self.assertContains(
            response, reverse("dataedit:view", kwargs={"table": "t_heat_draft"})
        )
        # exactly one badge: the draft table carries it, the published not
        self.assertContains(response, "Draft", count=1)

    def test_topic_badge_links_to_topic_dataset_list(self):
        response = self.client.get(self.detail_url)
        self.assertContains(
            response, reverse("dataedit:datasets-in-topic", kwargs={"topic": "heat"})
        )

    def test_metadata_viewer_and_raw_json_link(self):
        response = self.client.get(self.detail_url)
        metadata_url = reverse(
            "dataedit:dataset-metadata", kwargs={"dataset_name": "detailed_dataset"}
        )
        self.assertContains(response, 'id="metadata-viewer"')
        # the viewer script (bundled by the compressor) reads window.meta_api
        self.assertContains(response, f'window.meta_api = "{metadata_url}"')
        self.assertContains(response, metadata_url)

    def test_metadata_json_serves_document_with_live_resources(self):
        response = self.client.get(
            reverse(
                "dataedit:dataset-metadata",
                kwargs={"dataset_name": "detailed_dataset"},
            )
        )
        self.assertEqual(response.status_code, 200)
        document = response.json()
        self.assertEqual(document["title"], "Detailed Dataset")
        self.assertEqual(
            [resource["name"] for resource in document["resources"]],
            ["t_heat_published", "t_heat_draft"],
        )

    def test_created_dataset_document_conforms_to_oemetadata_spec(self):
        # end to end: dashboard create -> metadata endpoint -> omi
        # validation (license check off: datasets carry no own license yet,
        # licenses live on the resources)
        from omi.validation import validate_metadata

        self.client.force_login(self.creator)
        self.client.post(
            reverse("login:datasets", args=[self.creator.id]),
            {
                "name": "spec_valid_ds",
                "title": "Spec Valid Dataset",
                "description": "Checked against the oemetadata v2 spec",
            },
        )

        response = self.client.get(
            reverse(
                "dataedit:dataset-metadata",
                kwargs={"dataset_name": "spec_valid_ds"},
            )
        )
        self.assertEqual(response.status_code, 200)
        validate_metadata(response.json(), check_license=False)  # must not raise

    def test_creator_sees_dashboard_shortcut(self):
        self.client.force_login(self.creator)
        response = self.client.get(self.detail_url)
        self.assertContains(response, reverse("login:datasets", args=[self.creator.id]))

    def test_visitor_gets_no_dashboard_shortcut(self):
        self.client.force_login(self.visitor)
        response = self.client.get(self.detail_url)
        self.assertNotContains(
            response, reverse("login:datasets", args=[self.creator.id])
        )

    def test_public_card_list_links_to_detail_in_new_tab(self):
        response = self.client.get(
            reverse("dataedit:datasets-in-topic", kwargs={"topic": "heat"})
        )
        self.assertContains(response, self.detail_url)
        self.assertContains(response, 'target="_blank"')
