# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from copy import deepcopy

from oemetadata.latest.template import OEMETADATA_LATEST_TEMPLATE
from rest_framework import status
from rest_framework.test import APITestCase

from dataedit.models import Dataset, Table, Topic
from login.models import myuser


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
        Table.objects.create(name="t1", oemetadata=self.setUpResourceMetadata("t1"))
        Table.objects.create(name="t2", oemetadata=self.setUpResourceMetadata("t2"))
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
        self.assertEqual(len(dataset.metadata["resources"]), 2)

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
        dataset.update_resources_from_tables()

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
