# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from copy import deepcopy
from datetime import timedelta

from django.utils import timezone
from oemetadata.latest.template import OEMETADATA_LATEST_TEMPLATE
from rest_framework import status
from rest_framework.test import APITestCase

from dataedit.models import Dataset, Embargo, Table, Topic
from login.models import WRITE_PERM, UserPermission, myuser


class DatasetOwnershipTests(APITestCase):
    """Datasets are creator-owned: writes require login and ownership."""

    @classmethod
    def setUpTestData(cls):
        cls.creator, _ = myuser.objects.get_or_create(
            name="DatasetCreator",
            email="dataset-creator@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.other_user, _ = myuser.objects.get_or_create(
            name="NotTheCreator",
            email="not-the-creator@test.com",
            did_agree=True,
            is_mail_verified=True,
        )

    def create_owned_dataset(self, name="owned_dataset"):
        return Dataset.objects.create(
            name=name,
            metadata={"name": name, "resources": []},
            creator=self.creator,
        )

    def test_anonymous_cannot_create_dataset(self):
        payload = {
            "name": "anon_dataset",
            "title": "Anon",
            "description": "Should be rejected",
        }
        response = self.client.post("/api/v0/datasets/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Dataset.objects.filter(name="anon_dataset").exists())

    def test_anonymous_cannot_update_dataset(self):
        self.create_owned_dataset()
        payload = {
            "name": "owned_dataset",
            "title": "Changed",
            "description": "Changed",
        }
        response = self.client.put(
            "/api/v0/datasets/owned_dataset/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_cannot_delete_dataset(self):
        self.create_owned_dataset()
        response = self.client.delete("/api/v0/datasets/owned_dataset/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Dataset.objects.filter(name="owned_dataset").exists())

    def test_anonymous_cannot_assign_tables(self):
        self.create_owned_dataset()
        response = self.client.post(
            "/api/v0/datasets/owned_dataset/assign-tables/",
            {"tables": [{"name": "t1"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_records_creator(self):
        self.client.force_authenticate(user=self.creator)
        payload = {
            "name": "created_dataset",
            "title": "Created",
            "description": "Created by a logged-in user",
        }
        response = self.client.post("/api/v0/datasets/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dataset = Dataset.objects.get(name="created_dataset")
        self.assertEqual(dataset.creator, self.creator)

    def test_non_creator_cannot_update_dataset(self):
        self.create_owned_dataset()
        self.client.force_authenticate(user=self.other_user)
        payload = {
            "name": "owned_dataset",
            "title": "Hijacked",
            "description": "Should be rejected",
        }
        response = self.client.put(
            "/api/v0/datasets/owned_dataset/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_creator_cannot_delete_dataset(self):
        self.create_owned_dataset()
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete("/api/v0/datasets/owned_dataset/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Dataset.objects.filter(name="owned_dataset").exists())

    def test_non_creator_cannot_assign_tables(self):
        self.create_owned_dataset()
        Table.objects.create(name="t1", oemetadata={"resources": [{"name": "t1"}]})
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            "/api/v0/datasets/owned_dataset/assign-tables/",
            {"tables": [{"name": "t1"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_endpoints_stay_public(self):
        dataset = self.create_owned_dataset()
        table = Table.objects.create(
            name="t_public", oemetadata={"resources": [{"name": "t_public"}]}
        )
        dataset.tables.add(table)

        list_response = self.client.get("/api/v0/datasets/")
        detail_response = self.client.get("/api/v0/datasets/owned_dataset/")
        resources_response = self.client.get(
            "/api/v0/datasets/owned_dataset/resources/"
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(resources_response.status_code, status.HTTP_200_OK)

    def test_delete_dataset_leaves_tables_untouched(self):
        dataset = self.create_owned_dataset()
        table = Table.objects.create(
            name="t_keep", oemetadata={"resources": [{"name": "t_keep"}]}
        )
        dataset.tables.add(table)
        self.client.force_authenticate(user=self.creator)

        response = self.client.delete("/api/v0/datasets/owned_dataset/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dataset.objects.filter(name="owned_dataset").exists())
        self.assertTrue(Table.objects.filter(name="t_keep").exists())


class DatasetCurationRulesTests(APITestCase):
    """Assign follows the curation model; unassign completes membership."""

    @classmethod
    def setUpTestData(cls):
        cls.curator, _ = myuser.objects.get_or_create(
            name="Curator",
            email="curator@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.table_owner, _ = myuser.objects.get_or_create(
            name="TableOwner",
            email="table-owner@test.com",
            did_agree=True,
            is_mail_verified=True,
        )

    def setUp(self):
        self.dataset = Dataset.objects.create(
            name="curated_dataset",
            metadata={"name": "curated_dataset", "resources": []},
            creator=self.curator,
        )
        self.client.force_authenticate(user=self.curator)

    def make_table(self, name, published=True, owner=None):
        table = Table.objects.create(
            name=name,
            is_publish=published,
            oemetadata={"resources": [{"name": name}]},
        )
        if owner is not None:
            UserPermission.objects.create(holder=owner, table=table, level=WRITE_PERM)
        return table

    def assign(self, table_name):
        return self.client.post(
            "/api/v0/datasets/curated_dataset/assign-tables/",
            {"tables": [{"name": table_name}]},
            format="json",
        )

    def unassign(self, table_name):
        return self.client.post(
            "/api/v0/datasets/curated_dataset/unassign-tables/",
            {"tables": [{"name": table_name}]},
            format="json",
        )

    def test_assign_seeds_dataset_topics_additively(self):
        from dataedit.models import Topic
        from oeplatform.settings import PSEUDO_TOPIC_DRAFT

        wind, _ = Topic.objects.get_or_create(name="wind")
        draft, _ = Topic.objects.get_or_create(name=PSEUDO_TOPIC_DRAFT)
        table = self.make_table("t_tagged")
        table.topics.add(wind, draft)

        response = self.assign("t_tagged")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # the table's topics seed the dataset, the draft pseudo-topic never
        self.assertEqual(
            set(self.dataset.topics.values_list("name", flat=True)), {"wind"}
        )

    def test_unassign_keeps_dataset_topics(self):
        from dataedit.models import Topic

        wind, _ = Topic.objects.get_or_create(name="wind")
        table = self.make_table("t_tagged_member")
        table.topics.add(wind)
        self.assign("t_tagged_member")

        response = self.unassign("t_tagged_member")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(self.dataset.topics.values_list("name", flat=True)), {"wind"}
        )

    def test_creator_can_unassign_table(self):
        table = self.make_table("t_member")
        self.dataset.tables.add(table)

        response = self.unassign("t_member")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.dataset.tables.count(), 0)
        self.assertTrue(Table.objects.filter(name="t_member").exists())

    def test_unassign_requires_dataset_ownership(self):
        table = self.make_table("t_member")
        self.dataset.tables.add(table)
        self.client.force_authenticate(user=self.table_owner)

        response = self.unassign("t_member")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.dataset.tables.count(), 1)

    def test_unassign_anonymous_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.unassign("t_member")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_can_assign_published_table_without_table_permission(self):
        self.make_table("t_published", published=True, owner=self.table_owner)

        response = self.assign("t_published")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.dataset.tables.count(), 1)

    def test_cannot_assign_draft_table_without_write_permission(self):
        self.make_table("t_draft", published=False, owner=self.table_owner)

        response = self.assign("t_draft")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.dataset.tables.count(), 0)

    def test_can_assign_own_draft_table(self):
        self.make_table("t_own_draft", published=False, owner=self.curator)

        response = self.assign("t_own_draft")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.dataset.tables.count(), 1)

    def test_cannot_assign_embargoed_table_without_write_permission(self):
        table = self.make_table("t_embargoed", published=True, owner=self.table_owner)
        Embargo.objects.create(
            table=table,
            date_ended=timezone.now() + timedelta(days=30),
            duration="6_months",
        )

        response = self.assign("t_embargoed")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.dataset.tables.count(), 0)

    def test_can_assign_own_embargoed_table(self):
        table = self.make_table("t_own_embargoed", published=True, owner=self.curator)
        Embargo.objects.create(
            table=table,
            date_ended=timezone.now() + timedelta(days=30),
            duration="6_months",
        )

        response = self.assign("t_own_embargoed")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.dataset.tables.count(), 1)

    def test_assign_mix_of_known_and_unknown_tables(self):
        self.make_table("t_known", published=True)

        response = self.client.post(
            "/api/v0/datasets/curated_dataset/assign-tables/",
            {"tables": [{"name": "t_known"}, {"name": "t_unknown"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["added"], ["t_known"])
        self.assertEqual(response.data["missing"], [{"name": "t_unknown"}])
        self.assertEqual(self.dataset.tables.count(), 1)

    def test_expired_embargo_does_not_block_assignment(self):
        table = self.make_table("t_released", published=True, owner=self.table_owner)
        embargo = Embargo.objects.create(
            table=table,
            date_ended=timezone.now(),
            duration="6_months",
        )
        # Embargo.save() derives date_ended from duration, so expire it
        # behind save()'s back to simulate an embargo that has run out.
        Embargo.objects.filter(pk=embargo.pk).update(
            date_ended=timezone.now() - timedelta(days=1)
        )

        response = self.assign("t_released")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.dataset.tables.count(), 1)


class DatasetDerivedResourcesTests(APITestCase):
    """Resources are assembled live from member tables on every read."""

    @classmethod
    def setUpTestData(cls):
        cls.creator, _ = myuser.objects.get_or_create(
            name="ResourceReader",
            email="resource-reader@test.com",
            did_agree=True,
            is_mail_verified=True,
        )

    def setUp(self):
        self.client.force_authenticate(user=self.creator)
        self.dataset = Dataset.objects.create(
            name="derived_dataset",
            metadata={
                "name": "derived_dataset",
                "title": "Derived",
                "description": "Dataset with derived resources",
            },
            creator=self.creator,
        )
        self.table = Table.objects.create(
            name="t_source",
            is_publish=True,
            oemetadata={"resources": [{"name": "t_source", "title": "Original"}]},
        )
        self.dataset.tables.add(self.table)

    def read_resources(self):
        response = self.client.get("/api/v0/datasets/derived_dataset/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["metadata"]["resources"]

    def test_detail_read_assembles_resources_from_tables(self):
        resources = self.read_resources()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["name"], "t_source")

    def test_table_metadata_edits_are_reflected_without_reassign(self):
        self.table.oemetadata = {
            "resources": [{"name": "t_source", "title": "Corrected"}]
        }
        self.table.save()

        resources = self.read_resources()
        self.assertEqual(resources[0]["title"], "Corrected")

    def test_dataset_update_does_not_change_resources(self):
        payload = {
            "name": "derived_dataset",
            "title": "New Title",
            "description": "New description",
        }
        response = self.client.put(
            "/api/v0/datasets/derived_dataset/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        resources = self.read_resources()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["name"], "t_source")

    def test_rename_on_update_is_rejected(self):
        payload = {
            "name": "renamed_dataset",
            "title": "New Title",
            "description": "New description",
        }
        response = self.client.put(
            "/api/v0/datasets/derived_dataset/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Dataset.objects.filter(name="derived_dataset").exists())
        self.assertFalse(Dataset.objects.filter(name="renamed_dataset").exists())

    def test_create_rejects_non_slug_name(self):
        payload = {
            "name": "not a valid name!",
            "title": "Bad Name",
            "description": "Should be rejected",
        }
        response = self.client.post("/api/v0/datasets/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Dataset.objects.filter(metadata__title="Bad Name").exists())

    def test_create_rejects_duplicate_name(self):
        payload = {
            "name": "derived_dataset",
            "title": "Duplicate",
            "description": "Name is already taken",
        }
        response = self.client.post("/api/v0/datasets/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Dataset.objects.filter(name="derived_dataset").count(), 1)

    def test_no_resource_copy_is_persisted(self):
        self.client.post(
            "/api/v0/datasets/derived_dataset/assign-tables/",
            {"tables": [{"name": "t_source"}]},
            format="json",
        )
        self.dataset.refresh_from_db()
        self.assertNotIn("resources", self.dataset.metadata)


class DatasetAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user, _ = myuser.objects.get_or_create(
            name="DatasetUser",
            email="dataset-user@test.com",
            did_agree=True,
            is_mail_verified=True,
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def setUpDatasetMetadata(self, dataset_name: str):
        metadata = deepcopy(OEMETADATA_LATEST_TEMPLATE)

        metadata["name"] = dataset_name
        metadata["resources"] = []

        return metadata

    def setUpResourceMetadata(self, table_name: str):
        metadata = deepcopy(OEMETADATA_LATEST_TEMPLATE)

        metadata["resources"][0]["name"] = table_name

        return metadata

    def test_create_dataset(self):
        payload = {
            "name": "test_dataset",
            "title": "Test Dataset",
            "description": "This is a test dataset",
        }
        response = self.client.post(
            "/api/v0/datasets/", payload, format="json"
        )  # fixed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("metadata", response.data)
        self.assertIn("resources", response.data["metadata"])
        self.assertEqual(response.data["metadata"]["name"], "test_dataset")

    def test_list_datasets(self):
        Dataset.objects.create(name="ds1", metadata=self.setUpDatasetMetadata("ds1"))
        Dataset.objects.create(name="ds2", metadata=self.setUpDatasetMetadata("ds2"))
        response = self.client.get("/api/v0/datasets/")  # fixed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_assign_tables_to_dataset(self):
        # schema = Topic.objects.create(name="test_schema")
        Table.objects.create(
            name="t1", is_publish=True, oemetadata=self.setUpResourceMetadata("t1")
        )
        Table.objects.create(
            name="t2", is_publish=True, oemetadata=self.setUpResourceMetadata("t2")
        )
        dataset = Dataset.objects.create(
            name="test_dataset", metadata={"name": "test_dataset"}, creator=self.user
        )

        payload = {
            "dataset_name": "test_dataset",
            "tables": [
                {"name": "t1"},
                {"name": "t2"},
            ],
        }

        response = self.client.post(
            "/api/v0/datasets/test_dataset/assign-tables/", payload, format="json"
        )
        self.assertEqual(response.status_code, 200)
        dataset.refresh_from_db()
        self.assertEqual(len(dataset.tables.all()), 2)

        detail = self.client.get("/api/v0/datasets/test_dataset/")
        self.assertEqual(len(detail.data["metadata"]["resources"]), 2)

    def test_list_resources_for_dataset(self):
        schema = Topic.objects.create(name="test_schema")
        table = Table.objects.create(
            name="t1", oemetadata=self.setUpResourceMetadata("t1")
        )
        table.topics.add(schema)
        dataset = Dataset.objects.create(
            name="test_dataset", metadata=self.setUpDatasetMetadata("test_dataset")
        )
        dataset.tables.add(table)

        response = self.client.get(
            f"/api/v0/datasets/{dataset.name}/resources/"
        )  # fixed
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "t1")

    def test_assign_missing_table(self):
        Dataset.objects.create(
            name="ds_missing",
            metadata=self.setUpDatasetMetadata("ds_missing"),
            creator=self.user,
        )

        payload = {
            "dataset_name": "ds_missing",
            "tables": [{"name": "missing"}],
        }

        response = self.client.post(
            "/api/v0/datasets/ds_missing/assign-tables/", payload, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("missing", response.data)
        self.assertEqual(len(response.data["missing"]), 1)

    def test_list_resources_dataset_not_found(self):
        response = self.client.get("/api/v0/datasets/nonexistent/resources/")  # fixed
        self.assertEqual(response.status_code, 404)


class DatasetManagerAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user, _ = myuser.objects.get_or_create(
            name="DatasetManagerUser",
            email="dataset-manager@test.com",
            did_agree=True,
            is_mail_verified=True,
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)
        self.dataset = Dataset.objects.create(
            name="test_dataset",
            metadata={
                "name": "test_dataset",
                "title": "Test Title",
                "description": "Test Description",
                "resources": [],
            },
            creator=self.user,
        )
        self.detail_url = f"/api/v0/datasets/{self.dataset.name}/"

    def test_get_dataset(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "test_dataset")

    def test_update_dataset(self):
        updated_data = {
            "name": "test_dataset",  # must match existing name
            "title": "Updated Title",
            "description": "Updated Description",
            "at_id": "https://example.org/dataset/test_dataset",
        }

        response = self.client.put(self.detail_url, updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.metadata["title"], "Updated Title")
        self.assertEqual(self.dataset.metadata["description"], "Updated Description")
        self.assertEqual(
            self.dataset.metadata["@id"], "https://example.org/dataset/test_dataset"
        )

    def test_delete_dataset(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dataset.objects.filter(name="test_dataset").exists())

    def test_get_nonexistent_dataset(self):
        response = self.client.get("/api/v0/datasets/nonexistent_dataset/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_nonexistent_dataset(self):
        payload = {
            "name": "nonexistent_dataset",
            "title": "Does Not Exist",
            "description": "Should return 404",
        }
        response = self.client.put(
            "/api/v0/datasets/nonexistent_dataset/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_dataset(self):
        response = self.client.delete("/api/v0/datasets/nonexistent_dataset/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
