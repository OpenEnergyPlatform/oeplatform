"""A real response, checked against the schema the committed description
declares for it.

The drift guard in `api/tests/test_openapi_schema.py` keeps the committed
description equal to what the code produces. It cannot keep the description
equal to what the API *sends*: a response schema is built from serializers
that nothing in the write path calls, so the serializer and the artifact would
go on agreeing with each other while both drifted away from the body a client
actually receives. A test that takes a real response and validates it against
the schema the artifact declares for exactly that operation and status code is
the seam that turns a response schema from a claim into a checked fact.

Shared by the two halves of the API that do this: the OEKG scenario bundles
(`oekg/tests/test_response_schema.py`) and the datasets
(`api/tests/test_dataset_response_schema.py`).

Two details of how it validates:

- **OpenAPI 3.0 is not quite JSON Schema.** Its `nullable: true` is its own,
  and a plain validator would reject every `null` an API legitimately sends.
  `as_json_schema` translates that one keyword and leaves the rest alone,
  rather than adding a dependency for it.
- **A schema names what is always there, not everything there is.** Schemas
  are not closed, so a response carrying more than was declared passes. What
  fails is a response missing something declared, or carrying a declared key
  with the wrong type -- which is what actually goes wrong when a body
  changes.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import functools
import json

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from api.tests.test_openapi_schema import ARTIFACT, REGENERATE


def as_json_schema(node):
    """OpenAPI 3.0's `nullable`, rendered as the union it means.

    Nothing else is translated: `$ref`, `allOf`, `oneOf`, `required` and the
    type keywords mean the same thing in both dialects, and leaving them alone
    keeps this a translation rather than a reimplementation.
    """
    if isinstance(node, list):
        return [as_json_schema(entry) for entry in node]
    if not isinstance(node, dict):
        return node
    translated = {
        key: as_json_schema(value) for key, value in node.items() if key != "nullable"
    }
    if node.get("nullable"):
        if "type" in translated:
            translated["type"] = [translated["type"], "null"]
        elif "$ref" in translated or "allOf" in translated:
            # A nullable reference: the reference or nothing.
            translated = {"anyOf": [translated, {"type": "null"}]}
    return translated


@functools.cache
def described() -> dict:
    """The committed description, translated (``as_json_schema``). Read once
    per process; nothing may change what it returns."""
    return as_json_schema(yaml.safe_load(ARTIFACT.read_text(encoding="utf-8")))


def _where(error):
    """Where in the body the mismatch was, in a form a reader can follow."""
    return "/".join(str(part) for part in error.absolute_path) or "(root)"


class ResponseSchemaAssertions:
    """For a test case whose responses are checked against the committed
    description. ``SCHEMA_SOURCE`` names where the schemas are built from,
    so a failure says which of the two to fix."""

    SCHEMA_SOURCE = "the serializers"

    @property
    def document(self) -> dict:
        return described()

    def schema_for(self, path, method, code):
        """The schema the description declares for this exact answer."""
        operation = self.document["paths"][path][method]
        response = operation["responses"][str(code)]
        content = response.get("content", {})
        self.assertIn(
            "application/json",
            content,
            f"{method.upper()} {path} declares no JSON body for {code}. "
            f"If that changed, regenerate:\n    {REGENERATE}",
        )
        return content["application/json"]["schema"]

    def assertMatchesSchema(self, response, path, method, code):
        """The body this endpoint just sent is the body it says it sends."""
        self.assertEqual(response.status_code, code, response.content)
        schema = {
            **self.schema_for(path, method, code),
            "components": self.document["components"],
        }
        # Through JSON rather than on `response.data`: that still holds
        # `datetime` objects and DRF's own wrappers, and what a client receives
        # is what came out of the renderer.
        body = json.loads(response.content)
        error = best_match(Draft202012Validator(schema).iter_errors(body))
        if error is not None:
            self.fail(
                f"The body of {method.upper()} {path} is not what the "
                f"description says it is.\n"
                f"  at: {_where(error)}\n"
                f"  problem: {error.message}\n"
                f"The schema comes from {self.SCHEMA_SOURCE}; fix whichever "
                f"of the two is wrong and regenerate:\n    {REGENERATE}"
            )
