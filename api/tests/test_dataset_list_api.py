# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Dataset API's two lists: filters, pages and summaries (#2621, spec
#2613, WF-08 decisions 4 and 5).

`GET /datasets/` narrows what the caller may see with `?mine=` and
`?published=`, pages it, and lists summaries: the read body without the
assembled `metadata.resources`, plus `resource_count`. `GET
/datasets/<name>/resources/` pages a Dataset's members. Both cost the same
number of queries whatever a page holds and however many members a Dataset
has.
"""

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.serializers import DatasetReadSerializer
from dataedit.models import Dataset, Table, Topic
from login.models import myuser

LIST = "/api/v0/datasets/"


def make_user(name):
    return myuser.objects.get_or_create(
        name=name,
        email=f"{name.lower()}@test.com",
        did_agree=True,
        is_mail_verified=True,
    )[0]


def make_dataset(name, creator=None, published=False):
    return Dataset.objects.create(
        name=name,
        metadata={"name": name, "title": name.title(), "description": "Listed."},
        creator=creator,
        published_at=timezone.now() if published else None,
    )


def make_members(dataset, count, prefix):
    tables = Table.objects.bulk_create(
        Table(
            name=f"{prefix}_{index:05d}",
            oemetadata={"resources": [{"name": f"{prefix}_{index:05d}"}]},
        )
        for index in range(count)
    )
    dataset.tables.add(*tables)
    return tables


class DatasetListTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.creator = make_user("ListCreator")
        cls.other = make_user("ListOther")
        make_dataset("mine_draft", cls.creator)
        make_dataset("mine_published", cls.creator, published=True)
        make_dataset("their_draft", cls.other)
        make_dataset("their_published", cls.other, published=True)

    def as_(self, user):
        self.client.force_authenticate(user=user)

    def names(self, query=""):
        response = self.client.get(LIST + query)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return {item["name"] for item in response.data["results"]}


class ListFilterTests(DatasetListTestCase):
    def test_mine_lists_the_callers_drafts_and_published_and_nobody_elses(self):
        self.as_(self.creator)
        self.assertEqual(self.names("?mine=true"), {"mine_draft", "mine_published"})

    def test_mine_false_is_no_narrowing(self):
        self.as_(self.creator)
        self.assertEqual(
            self.names("?mine=false"),
            {"mine_draft", "mine_published", "their_published"},
        )

    def test_mine_true_asked_anonymously_is_401(self):
        response = self.client.get(LIST + "?mine=true")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_published_false_lists_only_the_callers_own_drafts(self):
        self.as_(self.creator)
        self.assertEqual(self.names("?published=false"), {"mine_draft"})

    def test_published_true_lists_only_published_datasets(self):
        self.as_(self.creator)
        self.assertEqual(
            self.names("?published=true"), {"mine_published", "their_published"}
        )

    def test_my_drafts_are_mine_and_not_published(self):
        self.as_(self.creator)
        self.assertEqual(self.names("?mine=true&published=false"), {"mine_draft"})
        self.assertEqual(self.names("?mine=true&published=true"), {"mine_published"})

    def test_published_false_asked_anonymously_is_an_honest_empty_page(self):
        response = self.client.get(LIST + "?published=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_an_unknown_value_is_a_400_naming_the_parameter(self):
        self.as_(self.creator)
        for parameter in ("mine", "published"):
            for value in ("maybe", "1", "True"):
                with self.subTest(parameter=parameter, value=value):
                    response = self.client.get(f"{LIST}?{parameter}={value}")
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertEqual(list(response.data), [parameter])

    def test_an_empty_value_is_as_if_the_filter_were_not_sent(self):
        # DRF's reading of an optional field in a query string
        self.as_(self.creator)
        self.assertEqual(self.names("?mine=&published="), self.names())

    def test_an_unknown_value_is_refused_before_the_login_is_asked_for(self):
        # a request that could not be answered with any login is told so
        response = self.client.get(LIST + "?mine=maybe")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data), ["mine"])


class ListPagingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        for index in range(25):
            make_dataset(f"paged_{index:02d}", published=True)

    def test_a_page_holds_20_by_default_in_drfs_envelope(self):
        response = self.client.get(LIST)
        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNone(response.data["previous"])
        self.assertIn("page=2", response.data["next"])

    def test_page_and_page_size_choose_the_window_in_name_order(self):
        response = self.client.get(LIST + "?page=2&page_size=10")
        self.assertEqual(
            [item["name"] for item in response.data["results"]],
            [f"paged_{index:02d}" for index in range(10, 20)],
        )

    def test_page_size_stops_at_100(self):
        for index in range(25, 110):
            make_dataset(f"paged_{index:03d}", published=True)
        response = self.client.get(LIST + "?page_size=500")
        self.assertEqual(response.data["count"], 110)
        self.assertEqual(len(response.data["results"]), 100)

    def test_a_page_past_the_last_is_404(self):
        response = self.client.get(LIST + "?page=3")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)


class SummaryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dataset = make_dataset("summarised", published=True)
        cls.dataset.topics.add(Topic.objects.get_or_create(name="summary_topic")[0])
        make_members(cls.dataset, 3, "summarised_member")
        # a member without resource metadata still counts: it is a member,
        # and /resources/ lists it
        cls.dataset.tables.add(Table.objects.create(name="summarised_bare"))

    def summary(self):
        (item,) = self.client.get(LIST).data["results"]
        return item

    def test_a_summary_carries_resource_count_and_no_resources(self):
        item = self.summary()
        self.assertEqual(item["resource_count"], 4)
        self.assertNotIn("resources", item["metadata"])
        self.assertEqual(item["metadata"]["title"], "Summarised")

    def test_a_summary_is_the_read_body_plus_resource_count(self):
        detail = self.client.get(LIST + "summarised/").data
        item = self.summary()
        self.assertEqual(
            set(item), set(DatasetReadSerializer.Meta.fields) | {"resource_count"}
        )
        self.assertEqual(set(item), set(detail) | {"resource_count"})
        for key in set(detail) - {"metadata"}:
            with self.subTest(key):
                self.assertEqual(item[key], detail[key])
        detail["metadata"].pop("resources")
        self.assertEqual(item["metadata"], detail["metadata"])

    def test_the_detail_read_keeps_its_resources(self):
        detail = self.client.get(LIST + "summarised/").data
        self.assertEqual(
            [entry["name"] for entry in detail["metadata"]["resources"]],
            [f"summarised_member_{index:05d}" for index in range(3)],
        )


class ResourcesPagingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dataset = make_dataset("membered", published=True)
        make_members(cls.dataset, 25, "membered_member")

    def test_resources_page_20_by_default_in_drfs_envelope(self):
        response = self.client.get(LIST + "membered/resources/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(
            [item["name"] for item in response.data["results"]],
            [f"membered_member_{index:05d}" for index in range(20)],
        )

    def test_resources_take_page_and_page_size(self):
        response = self.client.get(LIST + "membered/resources/?page=3&page_size=10")
        self.assertEqual(
            [item["name"] for item in response.data["results"]],
            [f"membered_member_{index:05d}" for index in range(20, 25)],
        )
        self.assertIsNone(response.data["next"])

    def test_resources_page_size_stops_at_100(self):
        make_members(self.dataset, 100, "membered_more")
        response = self.client.get(LIST + "membered/resources/?page_size=1000")
        self.assertEqual(len(response.data["results"]), 100)


class QueryCountTests(APITestCase):
    """Constant per page: the list and the members page cost the same number
    of queries for 3 Datasets, for 30, and beside one of 2,500 members."""

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("ListCounter")
        topic = Topic.objects.get_or_create(name="counted_topic")[0]
        for index in range(3):
            dataset = make_dataset(f"counted_{index:02d}", cls.user, published=True)
            dataset.topics.add(topic)
            make_members(dataset, 2, f"counted_{index:02d}_member")

    def setUp(self):
        self.client.force_authenticate(user=self.user)
        # the current Site is cached after the first request in a process
        self.client.get(LIST)

    def queries(self, path):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return len(captured)

    def grow_to_30(self):
        topic = Topic.objects.get(name="counted_topic")
        for index in range(3, 30):
            dataset = make_dataset(f"counted_{index:02d}", self.user, published=True)
            dataset.topics.add(topic)
            make_members(dataset, 2, f"counted_{index:02d}_member")

    def test_the_list_is_constant_per_page(self):
        # count, page, Topics
        with self.assertNumQueries(3):
            self.client.get(LIST)
        self.grow_to_30()
        with self.assertNumQueries(3):
            self.client.get(LIST + "?page_size=30")
        make_members(Dataset.objects.get(name="counted_00"), 2500, "counted_big")
        with self.assertNumQueries(3):
            self.client.get(LIST + "?page_size=30")

    def test_the_list_with_its_filters_costs_the_same(self):
        self.assertEqual(self.queries(LIST + "?mine=true&published=true"), 3)

    def test_the_members_page_is_constant(self):
        # the Dataset, count, page
        path = LIST + "counted_00/resources/"
        with self.assertNumQueries(3):
            self.client.get(path)
        make_members(Dataset.objects.get(name="counted_00"), 2500, "counted_big")
        with self.assertNumQueries(3):
            self.client.get(path)
        with self.assertNumQueries(3):
            self.client.get(path + "?page_size=100")
