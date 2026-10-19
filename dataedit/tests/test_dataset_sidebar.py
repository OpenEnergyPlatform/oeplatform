"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse
from django.utils import timezone

from base.tests import TestViewsTestCase
from dataedit.models import Dataset, Table
from login.models import myuser


class SidebarFixture(TestViewsTestCase):
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

    def make_dataset(self, name, published=True, creator=...):
        dataset = Dataset.objects.create(
            name=name,
            metadata={"name": name, "title": f"Title of {name}", "description": ""},
            creator=self.user if creator is ... else creator,
            published_at=timezone.now() if published else None,
        )
        dataset.tables.add(self.table)
        return dataset


class TableSidebarDatasetsTests(SidebarFixture):
    """The table detail sidebar lists the datasets a table belongs to:
    first three as links opening in a new tab, the rest behind a
    Show all expander."""

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


class TableSidebarDraftDatasetsTests(SidebarFixture):
    """The sidebar lists the published Datasets holding the Table plus the
    viewer's own drafts, marked as drafts (spec #2613): never another
    user's draft, and no platform-admin exemption."""

    def setUp(self):
        super().setUp()
        self.make_dataset("sidebar_published")
        self.make_dataset("sidebar_own_draft", published=False)
        self.other = myuser.objects.create_user(
            name="sidebar_other", email="sidebar_other@test.test", affiliation="x"
        )
        self.admin = myuser.objects.create_user(
            name="sidebar_admin", email="sidebar_admin@test.test", affiliation="x"
        )
        self.admin.is_admin = True
        self.admin.save()

    def detail(self, name):
        return reverse("dataedit:dataset-detail", kwargs={"dataset_name": name})

    def test_the_creator_sees_their_draft_marked(self):
        self.client.force_login(self.user)
        response = self.client.get(self.view_url)
        self.assertContains(response, self.detail("sidebar_own_draft"))
        self.assertContains(response, self.detail("sidebar_published"))
        self.assertContains(response, 'data-dataset-state="draft"', count=1)

    def test_nobody_else_sees_the_draft(self):
        for who in (self.other, self.admin, None):
            with self.subTest(who=who and who.name):
                if who is None:
                    self.client.logout()
                else:
                    self.client.force_login(who)
                response = self.client.get(self.view_url)
                self.assertContains(response, self.detail("sidebar_published"))
                self.assertNotContains(response, "sidebar_own_draft")

    def test_a_table_held_only_by_a_foreign_draft_shows_no_section(self):
        Dataset.objects.filter(name="sidebar_published").delete()
        self.client.force_login(self.other)
        response = self.client.get(self.view_url)
        self.assertNotContains(response, "sidebar-datasets")
