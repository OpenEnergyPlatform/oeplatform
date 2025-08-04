# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from copy import deepcopy

from oemetadata.latest.template import OEMETADATA_LATEST_TEMPLATE
from rest_framework import status
from rest_framework.test import APITestCase

from dataedit.models import Dataset, Schema, Table


class DatasetAPITests(APITestCase):
    def setUpDatasetMetadata(self, dataset_name: str):
        self.metadata = deepcopy(OEMETADATA_LATEST_TEMPLATE)

        self.metadata["name"] = dataset_name
        self.metadata["resources"] = []

    def setUpResourceMetadata(self, table_name: str):
        self.metadata = deepcopy(OEMETADATA_LATEST_TEMPLATE)

        self.metadata["resources"][0]["name"] = table_name

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
        schema = Schema.objects.create(name="test_schema")
        Table.objects.create(
            name="t1", schema=schema, oemetadata=self.setUpResourceMetadata("t1")
        )
        Table.objects.create(
            name="t2", schema=schema, oemetadata=self.setUpResourceMetadata("t2")
        )
        dataset = Dataset.objects.create(
            name="test_dataset", metadata={"name": "test_dataset"}
        )

        payload = {
            "dataset_name": "test_dataset",
            "tables": [
                {"schema": "test_schema", "name": "t1"},
                {"schema": "test_schema", "name": "t2"},
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
        schema = Schema.objects.create(name="test_schema")
        table = Table.objects.create(
            name="t1", schema=schema, oemetadata=self.setUpResourceMetadata("t1")
        )
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
            name="ds_missing", metadata=self.setUpDatasetMetadata("ds_missing")
        )

        payload = {
            "dataset_name": "ds_missing",
            "tables": [{"schema": "nonexistent", "name": "missing"}],
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
    def setUp(self):
        self.dataset = Dataset.objects.create(
            name="test_dataset",
            metadata={
                "name": "test_dataset",
                "title": "Test Title",
                "description": "Test Description",
                "resources": [],
            },
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
