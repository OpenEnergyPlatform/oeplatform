"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The Dataset lifecycle rule (#2618, spec #2613) and the public readers that
follow it: the topic list, the detail page and its metadata JSON.

Each reader is asked by the creator, another user, an anonymous visitor and a
platform admin, because the rule has no admin exemption and that is the case
most likely to be added back by accident.
"""  # noqa: 501

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dataedit.models import Dataset, Topic
from login.models import myuser


def make_user(name, **extra):
    user, _ = myuser.objects.get_or_create(
        name=name,
        email=f"{name.lower()}@test.com",
        did_agree=True,
        is_mail_verified=True,
        **extra,
    )
    return user


class LifecycleFixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.creator = make_user("LifecycleCreator")
        cls.other = make_user("LifecycleOther")
        cls.admin = make_user("LifecycleAdmin", is_admin=True)
        cls.topic = Topic.objects.create(name="lifecycle_topic")

    def setUp(self):
        self.draft = self.make("own_draft", self.creator)
        self.published = self.make("own_published", self.creator, published=True)
        self.ownerless_draft = self.make("ownerless_draft", None)
        self.ownerless_published = self.make(
            "ownerless_published", None, published=True
        )

    def make(self, name, creator, published=False):
        dataset = Dataset.objects.create(
            name=name,
            metadata={"name": name, "title": f"Title of {name}", "description": ""},
            creator=creator,
            published_at=timezone.now() if published else None,
        )
        dataset.topics.add(self.topic)
        return dataset

    def readers(self):
        return {
            "creator": self.creator,
            "other": self.other,
            "anonymous": AnonymousUser(),
            "admin": self.admin,
        }

    def login(self, who):
        user = self.readers()[who]
        if user.is_authenticated:
            self.client.force_login(user)
        else:
            self.client.logout()


class TheRuleTests(LifecycleFixture):
    def names(self, queryset):
        return set(queryset.values_list("name", flat=True))

    def test_a_bare_create_is_a_draft(self):
        dataset = Dataset.objects.create(name="bare")
        self.assertIsNone(dataset.published_at)
        self.assertIsNone(dataset.modified_at)
        self.assertFalse(dataset.is_published)

    def test_published_is_the_same_for_everyone(self):
        self.assertEqual(
            self.names(Dataset.objects.published()),
            {"own_published", "ownerless_published"},
        )

    def test_visible_to_adds_only_the_users_own_drafts(self):
        expected = {
            "creator": {"own_draft", "own_published", "ownerless_published"},
            "other": {"own_published", "ownerless_published"},
            "anonymous": {"own_published", "ownerless_published"},
            "admin": {"own_published", "ownerless_published"},
        }
        for who, user in self.readers().items():
            with self.subTest(who):
                self.assertEqual(
                    self.names(Dataset.objects.visible_to(user)), expected[who]
                )

    def test_readable_by_agrees_with_visible_to(self):
        for who, user in self.readers().items():
            for dataset in Dataset.objects.all():
                with self.subTest(who=who, dataset=dataset.name):
                    self.assertEqual(
                        dataset.readable_by(user),
                        Dataset.objects.visible_to(user).filter(pk=dataset.pk).exists(),
                    )


class TopicListTests(LifecycleFixture):
    def test_lists_published_datasets_only_for_everyone_even_the_creator(self):
        url = reverse("dataedit:datasets-in-topic", kwargs={"topic": self.topic.name})
        for who in self.readers():
            with self.subTest(who):
                self.login(who)
                response = self.client.get(url)
                names = {
                    dataset.name for dataset in response.context["datasets_paginated"]
                }
                self.assertEqual(names, {"own_published", "ownerless_published"})


class SingleReadTests(LifecycleFixture):
    """The detail page and its metadata JSON: the creator reads their draft,
    everyone else gets what an unknown name gets."""

    ROUTES = ("dataedit:dataset-detail", "dataedit:dataset-metadata")

    def get(self, route, name):
        return self.client.get(reverse(route, kwargs={"dataset_name": name}))

    def test_the_creator_reads_their_draft(self):
        self.login("creator")
        for route in self.ROUTES:
            with self.subTest(route):
                self.assertEqual(self.get(route, "own_draft").status_code, 200)

    def test_a_foreign_draft_reads_as_an_unknown_name(self):
        for who in ("other", "anonymous", "admin"):
            for route in self.ROUTES:
                with self.subTest(who=who, route=route):
                    self.login(who)
                    draft = self.get(route, "own_draft")
                    unknown = self.get(route, "no_such_dataset")
                    self.assertEqual(draft.status_code, 404)
                    self.assertEqual(draft.content, unknown.content)

    def test_an_ownerless_draft_is_read_by_nobody(self):
        for who in self.readers():
            with self.subTest(who):
                self.login(who)
                response = self.get("dataedit:dataset-detail", "ownerless_draft")
                self.assertEqual(response.status_code, 404)

    def test_a_published_dataset_is_read_by_everyone(self):
        for who in self.readers():
            for route in self.ROUTES:
                with self.subTest(who=who, route=route):
                    self.login(who)
                    self.assertEqual(self.get(route, "own_published").status_code, 200)

    def test_the_creator_sees_a_draft_banner_on_their_draft_only(self):
        self.login("creator")
        draft = self.get("dataedit:dataset-detail", "own_draft")
        published = self.get("dataedit:dataset-detail", "own_published")
        self.assertContains(draft, 'id="dataset-draft-banner"')
        self.assertNotContains(published, 'id="dataset-draft-banner"')
