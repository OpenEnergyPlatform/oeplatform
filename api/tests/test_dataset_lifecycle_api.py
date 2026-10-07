# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Dataset API under the lifecycle (#2618, spec #2613).

A draft is visible to its creator only: the list leaves it out for everyone
else, and the single reads answer 404 with the body an unknown name gets.
Writes never tell more than a read: they resolve the Dataset through the read
rule first, so a foreign draft is 404 and a foreign published Dataset 403.
No platform-admin exemption anywhere.
"""

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from dataedit.models import Dataset, Table
from login.models import myuser

WRITES = {
    "patch": lambda client, name: client.patch(
        f"/api/v0/datasets/{name}/",
        {"title": "Changed", "description": "Changed"},
        format="json",
    ),
    "publish": lambda client, name: client.post(f"/api/v0/datasets/{name}/publish/"),
    "unpublish": lambda client, name: client.post(
        f"/api/v0/datasets/{name}/unpublish/"
    ),
    "delete": lambda client, name: client.delete(f"/api/v0/datasets/{name}/"),
    "assign": lambda client, name: client.post(
        f"/api/v0/datasets/{name}/assign-tables/",
        {"tables": [{"name": "lifecycle_member"}]},
        format="json",
    ),
    "unassign": lambda client, name: client.post(
        f"/api/v0/datasets/{name}/unassign-tables/",
        {"tables": [{"name": "lifecycle_member"}]},
        format="json",
    ),
}


def make_user(name, **extra):
    user, _ = myuser.objects.get_or_create(
        name=name,
        email=f"{name.lower()}@test.com",
        did_agree=True,
        is_mail_verified=True,
        **extra,
    )
    return user


class DatasetLifecycleAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.creator = make_user("ApiLifecycleCreator")
        cls.other = make_user("ApiLifecycleOther")
        cls.admin = make_user("ApiLifecycleAdmin", is_admin=True)

    def setUp(self):
        self.member = Table.objects.create(
            name="lifecycle_member",
            is_publish=True,
            oemetadata={"resources": [{"name": "lifecycle_member"}]},
        )
        self.draft = self.make("api_draft", published=False)
        self.published = self.make("api_published", published=True)

    def make(self, name, published):
        dataset = Dataset.objects.create(
            name=name,
            metadata={"name": name, "title": name, "description": ""},
            creator=self.creator,
            published_at=timezone.now() if published else None,
        )
        dataset.tables.add(self.member)
        return dataset

    def as_(self, who):
        user = {"creator": self.creator, "other": self.other, "admin": self.admin}
        self.client.force_authenticate(user=user.get(who))

    def test_the_list_holds_published_datasets_plus_the_callers_own_drafts(self):
        expected = {
            "creator": {"api_draft", "api_published"},
            "other": {"api_published"},
            "admin": {"api_published"},
            "anonymous": {"api_published"},
        }
        for who, names in expected.items():
            with self.subTest(who):
                self.as_(who)
                response = self.client.get("/api/v0/datasets/")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual({item["name"] for item in response.data}, names)

    def test_the_creator_reads_their_draft(self):
        self.as_("creator")
        for path in (
            "/api/v0/datasets/api_draft/",
            "/api/v0/datasets/api_draft/resources/",
        ):
            with self.subTest(path):
                self.assertEqual(self.client.get(path).status_code, status.HTTP_200_OK)

    def test_a_foreign_draft_reads_word_for_word_as_an_unknown_name(self):
        for who in ("other", "admin", "anonymous"):
            for suffix in ("", "resources/"):
                with self.subTest(who=who, suffix=suffix):
                    self.as_(who)
                    draft = self.client.get(f"/api/v0/datasets/api_draft/{suffix}")
                    unknown = self.client.get(f"/api/v0/datasets/no_such/{suffix}")
                    self.assertEqual(draft.status_code, status.HTTP_404_NOT_FOUND)
                    self.assertEqual(draft.content, unknown.content)

    def test_a_published_dataset_is_read_by_everyone(self):
        for who in ("creator", "other", "admin", "anonymous"):
            for suffix in ("", "resources/"):
                with self.subTest(who=who, suffix=suffix):
                    self.as_(who)
                    response = self.client.get(
                        f"/api/v0/datasets/api_published/{suffix}"
                    )
                    self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_a_write_on_a_foreign_draft_is_the_404_of_an_unknown_name(self):
        for who in ("other", "admin"):
            for write, call in WRITES.items():
                with self.subTest(who=who, write=write):
                    self.as_(who)
                    draft = call(self.client, "api_draft")
                    unknown = call(self.client, "no_such")
                    self.assertEqual(draft.status_code, status.HTTP_404_NOT_FOUND)
                    self.assertEqual(draft.content, unknown.content)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.metadata["title"], "api_draft")
        self.assertEqual(list(self.draft.tables.all()), [self.member])

    def test_an_anonymous_write_is_refused_before_the_dataset_is_looked_up(self):
        # 401 for a draft, a published Dataset and an unknown name alike
        self.as_("anonymous")
        for write, call in WRITES.items():
            for name in ("api_draft", "api_published", "no_such"):
                with self.subTest(write=write, name=name):
                    response = call(self.client, name)
                    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_write_on_a_foreign_published_dataset_is_403(self):
        for who in ("other", "admin"):
            for write, call in WRITES.items():
                with self.subTest(who=who, write=write):
                    self.as_(who)
                    response = call(self.client, "api_published")
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Dataset.objects.filter(name="api_published").exists())

    def test_the_creator_writes_to_their_draft(self):
        self.as_("creator")
        # publish is left out: a draft with no topics fails the gate (409)
        for write in ("patch", "unpublish", "unassign", "assign", "delete"):
            with self.subTest(write):
                response = WRITES[write](self.client, "api_draft")
                self.assertLess(response.status_code, 300)
        self.assertFalse(Dataset.objects.filter(name="api_draft").exists())

    def test_the_resources_view_declares_its_permission_classes(self):
        from api.views import DatasetsListResources

        self.assertIn("permission_classes", vars(DatasetsListResources))
