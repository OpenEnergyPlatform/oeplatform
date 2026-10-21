# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Every answer the Dataset API declares, checked against what it sends
(#2620, spec #2613).

One real response of every Dataset operation, its success and each refusal
it declares, validated against the schema the committed ``openapi.yaml``
declares for exactly that operation and code (``api/tests/response_schema``,
shared with the OEKG half). The cases are checked against the artifact in
both directions: a declared answer with no case here fails, and so does a
case for an answer nobody declared, so the description cannot promise a
refusal no test has seen nor leave one out.

And the one shape no Dataset refusal may have any more: ``{"error": …}``.
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from api.api_tags import DATASETS
from api.tests.response_schema import ResponseSchemaAssertions
from dataedit.models import Dataset, Table, Topic
from login.models import myuser

ROOT = "/api/v0/datasets/"
DETAIL = ROOT + "{dataset_name}/"
PUBLISH = DETAIL + "publish/"
UNPUBLISH = DETAIL + "unpublish/"
RESOURCES = DETAIL + "resources/"
ASSIGN = DETAIL + "assign-tables/"
UNASSIGN = DETAIL + "unassign-tables/"

MEMBER = {"tables": [{"name": "rs_member"}]}

# (path, method, code) -> (who asks, the request). Who is "creator",
# "stranger" or None (anonymous); the request takes the client.
CASES = {
    (ROOT, "get", 200): ("creator", lambda c: c.get(ROOT)),
    (ROOT, "get", 400): ("creator", lambda c: c.get(ROOT + "?published=maybe")),
    (ROOT, "get", 401): (None, lambda c: c.get(ROOT + "?mine=true")),
    (ROOT, "get", 404): (None, lambda c: c.get(ROOT + "?page=9")),
    (ROOT, "post", 201): (
        "creator",
        lambda c: c.post(
            ROOT,
            {
                "name": "rs_new",
                "title": "New",
                "description": "New.",
                "topics": ["rs_topic"],
            },
            format="json",
        ),
    ),
    (ROOT, "post", 400): (
        "creator",
        lambda c: c.post(
            ROOT,
            {"name": "rs_new", "title": "N", "description": "N", "topics": ["nope"]},
            format="json",
        ),
    ),
    (ROOT, "post", 401): (
        None,
        lambda c: c.post(
            ROOT, {"name": "rs_new", "title": "N", "description": "N"}, format="json"
        ),
    ),
    (DETAIL, "get", 200): (None, lambda c: c.get(ROOT + "rs_theirs/")),
    (DETAIL, "get", 404): ("stranger", lambda c: c.get(ROOT + "rs_ready/")),
    (DETAIL, "patch", 200): (
        "creator",
        lambda c: c.patch(
            ROOT + "rs_ready/", {"title": "Changed", "topics": []}, format="json"
        ),
    ),
    (DETAIL, "patch", 400): (
        "creator",
        lambda c: c.patch(ROOT + "rs_ready/", {"name": "rs_ready"}, format="json"),
    ),
    (DETAIL, "patch", 401): (
        None,
        lambda c: c.patch(ROOT + "rs_ready/", {"title": "T"}, format="json"),
    ),
    (DETAIL, "patch", 403): (
        "creator",
        lambda c: c.patch(ROOT + "rs_theirs/", {"title": "T"}, format="json"),
    ),
    (DETAIL, "patch", 404): (
        "creator",
        lambda c: c.patch(ROOT + "rs_no_such/", {"title": "T"}, format="json"),
    ),
    (DETAIL, "delete", 204): ("creator", lambda c: c.delete(ROOT + "rs_ready/")),
    (DETAIL, "delete", 401): (None, lambda c: c.delete(ROOT + "rs_ready/")),
    (DETAIL, "delete", 403): ("creator", lambda c: c.delete(ROOT + "rs_theirs/")),
    (DETAIL, "delete", 404): ("stranger", lambda c: c.delete(ROOT + "rs_ready/")),
    (PUBLISH, "post", 200): ("creator", lambda c: c.post(ROOT + "rs_ready/publish/")),
    (PUBLISH, "post", 401): (None, lambda c: c.post(ROOT + "rs_ready/publish/")),
    (PUBLISH, "post", 403): (
        "creator",
        lambda c: c.post(ROOT + "rs_theirs/publish/"),
    ),
    (PUBLISH, "post", 404): (
        "stranger",
        lambda c: c.post(ROOT + "rs_ready/publish/"),
    ),
    (PUBLISH, "post", 409): ("creator", lambda c: c.post(ROOT + "rs_bare/publish/")),
    (UNPUBLISH, "post", 200): (
        "stranger",
        lambda c: c.post(ROOT + "rs_theirs/unpublish/"),
    ),
    (UNPUBLISH, "post", 401): (None, lambda c: c.post(ROOT + "rs_ready/unpublish/")),
    (UNPUBLISH, "post", 403): (
        "creator",
        lambda c: c.post(ROOT + "rs_theirs/unpublish/"),
    ),
    (UNPUBLISH, "post", 404): (
        "stranger",
        lambda c: c.post(ROOT + "rs_ready/unpublish/"),
    ),
    (RESOURCES, "get", 200): ("creator", lambda c: c.get(ROOT + "rs_ready/resources/")),
    (RESOURCES, "get", 404): (None, lambda c: c.get(ROOT + "rs_ready/resources/")),
    (ASSIGN, "post", 200): (
        "creator",
        lambda c: c.post(ROOT + "rs_bare/assign-tables/", MEMBER, format="json"),
    ),
    (ASSIGN, "post", 400): (
        "creator",
        lambda c: c.post(
            ROOT + "rs_bare/assign-tables/", {"tables": []}, format="json"
        ),
    ),
    (ASSIGN, "post", 401): (
        None,
        lambda c: c.post(ROOT + "rs_bare/assign-tables/", MEMBER, format="json"),
    ),
    (ASSIGN, "post", 403): (
        "creator",
        lambda c: c.post(
            ROOT + "rs_bare/assign-tables/",
            {"tables": [{"name": "rs_their_draft_table"}]},
            format="json",
        ),
    ),
    (ASSIGN, "post", 404): (
        "stranger",
        lambda c: c.post(ROOT + "rs_bare/assign-tables/", MEMBER, format="json"),
    ),
    (UNASSIGN, "post", 200): (
        "creator",
        lambda c: c.post(ROOT + "rs_ready/unassign-tables/", MEMBER, format="json"),
    ),
    (UNASSIGN, "post", 400): (
        "creator",
        lambda c: c.post(ROOT + "rs_ready/unassign-tables/", {}, format="json"),
    ),
    (UNASSIGN, "post", 401): (
        None,
        lambda c: c.post(ROOT + "rs_ready/unassign-tables/", MEMBER, format="json"),
    ),
    (UNASSIGN, "post", 403): (
        "creator",
        lambda c: c.post(ROOT + "rs_theirs/unassign-tables/", MEMBER, format="json"),
    ),
    (UNASSIGN, "post", 404): (
        "stranger",
        lambda c: c.post(ROOT + "rs_ready/unassign-tables/", MEMBER, format="json"),
    ),
}


def make_user(name):
    return myuser.objects.get_or_create(
        name=name,
        email=f"{name.lower()}@test.com",
        did_agree=True,
        is_mail_verified=True,
    )[0]


class DatasetResponseSchemaTest(ResponseSchemaAssertions, APITestCase):
    SCHEMA_SOURCE = (
        "the dataset serializers in api/serializers.py and api/api_description.py"
    )

    @classmethod
    def setUpTestData(cls):
        cls.users = {
            "creator": make_user("SchemaCreator"),
            "stranger": make_user("SchemaStranger"),
        }
        topic = Topic.objects.get_or_create(name="rs_topic")[0]
        member = Table.objects.create(
            name="rs_member",
            is_publish=True,
            oemetadata={"resources": [{"name": "rs_member"}]},
        )
        Table.objects.create(name="rs_their_draft_table", is_publish=False)
        # the creator's draft that passes the publish gate
        ready = cls.dataset("rs_ready", "creator")
        ready.tables.add(member)
        ready.topics.add(topic)
        # the creator's draft that fails it on both checks
        cls.dataset("rs_bare", "creator")
        # someone else's published Dataset
        theirs = cls.dataset("rs_theirs", "stranger", published=True)
        theirs.tables.add(member)
        theirs.topics.add(topic)

    @classmethod
    def dataset(cls, name, who, published=False):
        return Dataset.objects.create(
            name=name,
            metadata={"name": name, "title": name, "description": "Schema."},
            creator=cls.users[who],
            published_at=timezone.now() if published else None,
        )

    def declared(self):
        """Every (path, method, code) the artifact declares for a Dataset
        operation."""
        answers = set()
        for path, operations in self.document["paths"].items():
            for method, operation in operations.items():
                if not isinstance(operation, dict):
                    continue
                if DATASETS not in operation.get("tags", []):
                    continue
                for code in operation["responses"]:
                    answers.add((path, method, int(code)))
        return answers

    def answer(self, key):
        """The response to the case ``key``, with whatever it wrote rolled
        back, so every case meets the same fixtures."""
        who, request = CASES[key]
        self.client.force_authenticate(user=self.users.get(who))
        with transaction.atomic():
            response = request(self.client)
            transaction.set_rollback(True)
        return response

    def test_every_declared_answer_has_a_case_and_no_case_is_undeclared(self):
        declared = self.declared()
        self.assertEqual(
            sorted(declared - set(CASES)), [], "declared, but no case sends it"
        )
        self.assertEqual(
            sorted(set(CASES) - declared), [], "a case, but nobody declared it"
        )

    def test_every_answer_is_the_body_it_is_declared_to_be(self):
        for key in sorted(CASES):
            path, method, code = key
            with self.subTest(f"{method.upper()} {path} {code}"):
                response = self.answer(key)
                if code == 204:
                    self.assertEqual(response.status_code, 204)
                    self.assertEqual(response.content, b"")
                    self.assertNotIn(
                        "content",
                        self.document["paths"][path][method]["responses"]["204"],
                    )
                    continue
                self.assertMatchesSchema(response, path, method, code)

    def test_no_refusal_speaks_error(self):
        for key in sorted(CASES):
            if key[2] < 400:
                continue
            with self.subTest(key):
                body = self.answer(key).json()
                self.assertNotIn("error", body)
                if key[2] != 400:
                    self.assertIn("detail", body)
