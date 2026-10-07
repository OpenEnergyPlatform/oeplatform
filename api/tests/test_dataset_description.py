# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later
"""What the committed description says about the Dataset API in words
(#2620, spec #2613).

Read off the artifact rather than the annotations, as
``test_scenario_bundle_description`` does: an assertion about
``extend_schema`` would pass while the generator dropped the operation it
decorated.

Two facts every Dataset operation states in prose, because Swagger's padlock
reads the opposite of what it seems (closed on a public read, open on a write
that needs a login):

- its auth expectation, **cross-checked against its own ``security``
  block**, so the words and the padlock are two renderings of one fact;
- the draft rule: a draft is visible only to its creator.
"""

from django.test import SimpleTestCase

from api.api_tags import DATASETS, TAGS
from api.tests.response_schema import described
from api.tests.test_openapi_schema import REGENERATE


def _is_public(operation):
    """An empty requirement in ``security`` is OpenAPI's "no authentication is
    also acceptable", the entry Swagger reads for its padlock."""
    return {} in operation.get("security", [])


class DatasetDescriptionTest(SimpleTestCase):
    def operations(self):
        for path, operations in described()["paths"].items():
            for method, operation in operations.items():
                if isinstance(operation, dict) and DATASETS in operation.get(
                    "tags", []
                ):
                    yield f"{method.upper()} {path}", operation

    def test_there_are_dataset_operations(self):
        self.assertGreaterEqual(len(list(self.operations())), 10)

    def test_every_description_states_its_auth_expectation(self):
        for name, operation in self.operations():
            with self.subTest(name):
                description = operation.get("description", "")
                public = _is_public(operation)
                expected = "Public" if public else "Requires authentication"
                unexpected = "Requires authentication" if public else "Public"
                self.assertIn(
                    expected,
                    description,
                    f"{name} says nothing of {expected.lower()!r}, which its "
                    f"security block means. Regenerate after fixing:\n"
                    f"    {REGENERATE}",
                )
                self.assertNotIn(unexpected, description)

    def test_every_description_states_the_draft_rule(self):
        for name, operation in self.operations():
            with self.subTest(name):
                self.assertIn(
                    "visible only to its creator", operation.get("description", "")
                )

    def test_the_tag_states_the_lifecycle_and_no_longer_says_all_is_public(self):
        tag = next(tag for tag in TAGS if tag["name"] == DATASETS)
        self.assertIn("draft", tag["description"])
        self.assertIn("publish", tag["description"])
        for name, operation in self.operations():
            with self.subTest(name):
                self.assertNotIn(
                    "Every dataset on the platform", operation.get("description", "")
                )
