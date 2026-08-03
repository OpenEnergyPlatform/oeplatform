"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from base.tests import TestViewsTestCase
from dataedit.models import Dataset, Table


class TableSidebarDatasetsTests(TestViewsTestCase):
    """The table detail sidebar lists the datasets a table belongs to:
    first three as links opening in a new tab, the rest behind a
    Show all expander."""

    table_name = "test_sidebar_table"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.table = Table.create_with_oedb_table(
            is_sandbox=True,  # IMPORTANT for test
            name=cls.table_name,
            user=cls.user,
            column_definitions=[],
            constraints_definitions=[],
        )

    @classmethod
    def tearDownClass(cls):
        cls.table.delete()
        super().tearDownClass()

    def setUp(self):
        self.view_url = reverse("dataedit:view", kwargs={"table": self.table_name})

    def make_dataset(self, name):
        dataset = Dataset.objects.create(
            name=name,
            metadata={"name": name, "title": f"Title of {name}", "description": ""},
            creator=self.user,
        )
        dataset.tables.add(self.table)
        return dataset

    def test_no_section_without_dataset_membership(self):
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "sidebar-datasets")

    def test_few_datasets_list_without_expander(self):
        self.make_dataset("sidebar_ds_a")
        self.make_dataset("sidebar_ds_b")

        response = self.client.get(self.view_url)
        self.assertContains(response, "sidebar-datasets")
        self.assertContains(
            response,
            reverse("dataedit:dataset-detail", kwargs={"dataset_name": "sidebar_ds_a"}),
        )
        self.assertContains(
            response,
            reverse("dataedit:dataset-detail", kwargs={"dataset_name": "sidebar_ds_b"}),
        )
        self.assertNotContains(response, "Show all")

    def test_many_datasets_collapse_behind_expander(self):
        for index in range(5):
            self.make_dataset(f"sidebar_ds_{index}")

        response = self.client.get(self.view_url)
        # all five are links on the page (two of them inside the collapse)
        for index in range(5):
            self.assertContains(
                response,
                reverse(
                    "dataedit:dataset-detail",
                    kwargs={"dataset_name": f"sidebar_ds_{index}"},
                ),
            )
        self.assertContains(response, "Show all (5)")
        self.assertContains(response, 'id="sidebar-datasets-all"')
