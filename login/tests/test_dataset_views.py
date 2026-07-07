"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase
from django.urls import reverse

from dataedit.models import Dataset, Embargo, Table
from login.models import WRITE_PERM, UserPermission, myuser


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


class DatasetQuickActionsTests(TestCase):
    """Edit and delete quick actions on the dashboard dataset cards."""

    @classmethod
    def setUpTestData(cls):
        cls.user, _ = myuser.objects.get_or_create(
            name="QuickActionUser",
            email="quick-action-user@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.other_user, _ = myuser.objects.get_or_create(
            name="OtherQuickActionUser",
            email="other-quick-action-user@test.com",
            did_agree=True,
            is_mail_verified=True,
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.dataset = Dataset.objects.create(
            name="quick_dataset",
            metadata={
                "name": "quick_dataset",
                "title": "Quick Dataset",
                "description": "A dataset with quick actions",
            },
            creator=self.user,
        )
        self.edit_url = reverse(
            "login:dataset-edit", args=[self.user.id, "quick_dataset"]
        )
        self.delete_url = reverse(
            "login:dataset-delete", args=[self.user.id, "quick_dataset"]
        )

    def test_edit_form_keeps_name_readonly(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "quick_dataset")
        self.assertContains(response, 'name="title"')
        self.assertNotContains(response, 'name="name"')

    def test_edit_updates_title_and_description(self):
        response = self.client.post(
            self.edit_url,
            {"title": "New Title", "description": "New description"},
        )
        self.assertEqual(response.status_code, 200)
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.metadata["title"], "New Title")
        self.assertEqual(self.dataset.metadata["description"], "New description")
        self.assertEqual(self.dataset.name, "quick_dataset")
        self.assertContains(response, "New Title")

    def test_edit_validation_error_is_shown_inline(self):
        response = self.client.post(
            self.edit_url, {"title": "", "description": "Still here"}
        )
        self.assertEqual(response.status_code, 200)
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.metadata["title"], "Quick Dataset")
        self.assertContains(response, "invalid-feedback")

    def test_edit_forbidden_for_non_creator(self):
        self.client.force_login(self.other_user)
        response = self.client.post(
            self.edit_url,
            {"title": "Hijacked", "description": "Should fail"},
        )
        self.assertEqual(response.status_code, 403)
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.metadata["title"], "Quick Dataset")

    def test_delete_removes_only_the_dataset(self):
        table = Table.objects.create(
            name="t_survives",
            oemetadata={"resources": [{"name": "t_survives"}]},
        )
        self.dataset.tables.add(table)

        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Dataset.objects.filter(name="quick_dataset").exists())
        self.assertTrue(Table.objects.filter(name="t_survives").exists())
        self.assertNotContains(response, "quick_dataset")

    def test_delete_forbidden_for_non_creator(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Dataset.objects.filter(name="quick_dataset").exists())

    def test_delete_confirm_copy_mentions_tables_survive(self):
        response = self.client.get(reverse("login:datasets", args=[self.user.id]))
        self.assertContains(response, "hx-confirm")
        self.assertContains(response, "not deleted")

    def test_actions_not_rendered_for_other_users(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("login:datasets", args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "quick_dataset")
        self.assertNotContains(response, "hx-confirm")


class DatasetResourceManagementTests(TestCase):
    """Assign and unassign tables from the dataset manage panel."""

    @classmethod
    def setUpTestData(cls):
        cls.user, _ = myuser.objects.get_or_create(
            name="ResourceManager",
            email="resource-manager@test.com",
            did_agree=True,
            is_mail_verified=True,
        )
        cls.other_user, _ = myuser.objects.get_or_create(
            name="OtherResourceManager",
            email="other-resource-manager@test.com",
            did_agree=True,
            is_mail_verified=True,
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.dataset = Dataset.objects.create(
            name="managed_dataset",
            metadata={
                "name": "managed_dataset",
                "title": "Managed Dataset",
                "description": "",
            },
            creator=self.user,
        )
        self.manage_url = reverse(
            "login:dataset-manage", args=[self.user.id, "managed_dataset"]
        )
        self.search_url = reverse(
            "login:dataset-table-search", args=[self.user.id, "managed_dataset"]
        )
        self.assign_url = reverse(
            "login:dataset-assign", args=[self.user.id, "managed_dataset"]
        )
        self.unassign_url = reverse(
            "login:dataset-unassign", args=[self.user.id, "managed_dataset"]
        )

    def make_table(self, name, published=True, writable_by=None):
        table = Table.objects.create(
            name=name,
            is_publish=published,
            oemetadata={"resources": [{"name": name}]},
        )
        if writable_by is not None:
            UserPermission.objects.create(
                holder=writable_by, table=table, level=WRITE_PERM
            )
        return table

    def test_manage_view_creator_only(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, 403)

    def test_manage_lists_resources_with_links_and_draft_badge(self):
        published = self.make_table("t_pub_resource", published=True)
        draft = self.make_table(
            "t_draft_resource", published=False, writable_by=self.user
        )
        self.dataset.tables.add(published, draft)

        response = self.client.get(self.manage_url)
        self.assertContains(response, "t_pub_resource")
        self.assertContains(response, "t_draft_resource")
        self.assertContains(response, "Draft")
        self.assertContains(
            response, reverse("dataedit:view", kwargs={"table": "t_pub_resource"})
        )

    def test_picker_offers_only_assignable_tables(self):
        self.make_table("t_free", published=True)
        self.make_table("t_foreign_draft", published=False, writable_by=self.other_user)
        self.make_table("t_own_draft", published=False, writable_by=self.user)
        embargoed = self.make_table("t_embargoed_foreign", published=True)
        Embargo.objects.create(table=embargoed, date_ended=None, duration="6_months")
        assigned = self.make_table("t_already_in", published=True)
        self.dataset.tables.add(assigned)

        response = self.client.get(self.search_url)
        self.assertContains(response, "t_free")
        self.assertContains(response, "t_own_draft")
        self.assertNotContains(response, "t_foreign_draft")
        self.assertNotContains(response, "t_embargoed_foreign")
        self.assertNotContains(response, "t_already_in")

    def test_picker_search_filters_by_name(self):
        self.make_table("solar_capacity", published=True)
        self.make_table("wind_capacity", published=True)

        response = self.client.get(self.search_url, {"q": "solar"})
        self.assertContains(response, "solar_capacity")
        self.assertNotContains(response, "wind_capacity")

    def test_assign_adds_table(self):
        self.make_table("t_pickable", published=True)

        response = self.client.post(self.assign_url, {"table": "t_pickable"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.dataset.tables.filter(name="t_pickable").exists())
        self.assertContains(response, "t_pickable")

    def test_assign_foreign_draft_forbidden(self):
        self.make_table("t_locked", published=False, writable_by=self.other_user)

        response = self.client.post(self.assign_url, {"table": "t_locked"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.dataset.tables.filter(name="t_locked").exists())

    def test_assign_forbidden_for_non_creator(self):
        self.make_table("t_free_for_all", published=True)
        self.client.force_login(self.other_user)

        response = self.client.post(self.assign_url, {"table": "t_free_for_all"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.dataset.tables.filter(name="t_free_for_all").exists())

    def test_unassign_removes_table_but_keeps_it(self):
        table = self.make_table("t_removable", published=True)
        self.dataset.tables.add(table)

        response = self.client.post(self.unassign_url, {"table": "t_removable"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.dataset.tables.filter(name="t_removable").exists())
        self.assertTrue(Table.objects.filter(name="t_removable").exists())
