"""Every response this API sends, checked against the schema that describes it.

The drift guard in `api/tests/test_openapi_schema.py` keeps the committed
description equal to what the code produces. It cannot keep the description
equal to what the API *sends*: a response schema is built from
`oekg/read_serializers.py`, which nothing in the write path calls, so the
serializer and the artifact would go on agreeing with each other while both
drifted away from the body a client actually receives. Nobody would notice
until somebody read the document and believed it.

So this takes a real response from every scenario-bundle endpoint -- through
the API, against a real graph store -- and validates it against the schema the
committed artifact declares for exactly that operation and status code. It is
the seam that turns a response schema from a claim into a checked fact.

Two details of how it validates:

- **OpenAPI 3.0 is not quite JSON Schema.** Its `nullable: true` is its own,
  and a plain validator would reject every `null` this API legitimately sends.
  `_as_json_schema` translates that one keyword and leaves the rest alone,
  rather than adding a dependency for it.
- **A schema names what is always there, not everything there is.** `_meta`
  gains keys on request (`labels`) and on trouble (`history_recorded`), so
  these schemas are deliberately not closed and a response carrying more than
  was declared passes. What fails is a response missing something declared, or
  carrying a declared key with the wrong type -- which is what actually goes
  wrong when a body changes.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from api.tests.test_openapi_schema import ARTIFACT, REGENERATE
from oekg.tests.test_dataset_link_api import DatasetLinkTestCase
from oekg.tests.test_study_report_api import VALID_REPORT, StudyReportTestCase


def _document():
    return yaml.safe_load(ARTIFACT.read_text(encoding="utf-8"))


def _as_json_schema(node):
    """OpenAPI 3.0's `nullable`, rendered as the union it means.

    Nothing else is translated: `$ref`, `allOf`, `oneOf`, `required` and the
    type keywords mean the same thing in both dialects, and leaving them alone
    keeps this a translation rather than a reimplementation.
    """
    if isinstance(node, list):
        return [_as_json_schema(entry) for entry in node]
    if not isinstance(node, dict):
        return node
    translated = {
        key: _as_json_schema(value) for key, value in node.items() if key != "nullable"
    }
    if node.get("nullable"):
        if "type" in translated:
            translated["type"] = [translated["type"], "null"]
        elif "$ref" in translated or "allOf" in translated:
            # A nullable reference: the reference or nothing.
            translated = {"anyOf": [translated, {"type": "null"}]}
    return translated


def _where(error):
    """Where in the body the mismatch was, in a form a reader can follow."""
    return "/".join(str(part) for part in error.absolute_path) or "(root)"


class ResponseSchemaTestCase(DatasetLinkTestCase, StudyReportTestCase):
    """One bundle with one of everything on it, and a validator over it.

    Both fixture bases, because this is the one place that needs a bundle
    carrying every kind of thing at once -- which is also where a read and its
    schema come apart most easily.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        document = _document()
        cls.document = _as_json_schema(document)

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
        self.assertEqual(response.status_code, code, response.data)
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
                f"The schema comes from the serializers in "
                f"oekg/read_serializers.py; fix whichever of the two is wrong "
                f"and regenerate:\n    {REGENERATE}"
            )


class BundleResponseSchemaTest(ResponseSchemaTestCase):
    COLLECTION = "/api/v0/scenario-bundles/"
    DETAIL = "/api/v0/scenario-bundles/{uid}/"

    def test_a_create_sends_the_bundle_it_describes(self):
        response = self.create()

        self.assertMatchesSchema(response, self.COLLECTION, "post", 201)

    def test_a_listing_sends_the_page_it_describes(self):
        self.created()

        response = self.client.get(self.collection_url)

        self.assertMatchesSchema(response, self.COLLECTION, "get", 200)

    def test_a_read_sends_the_bundle_it_describes(self):
        uid, _ = self.created()

        response = self.client.get(self.detail_url(uid))

        self.assertMatchesSchema(response, self.DETAIL, "get", 200)

    def test_a_read_with_everything_on_it_still_matches(self):
        # The nested parts are where a read and its schema come apart most
        # easily: they carry their own `_meta`, unlike the write payload the
        # read serializer is built from.
        uid, sid, _did, _etag = self.with_one_link()
        self.add_report(uid, self.client.get(self.detail_url(uid))["ETag"])

        response = self.client.get(f"{self.detail_url(uid)}?expand=labels")

        self.assertMatchesSchema(response, self.DETAIL, "get", 200)
        self.assertTrue(response.data["scenarios"])
        self.assertTrue(response.data["study_reports"])

    def test_a_patch_sends_the_bundle_it_describes(self):
        uid, etag = self.created()

        response = self.patch(uid, {"label": "Renamed"}, if_match=etag)

        self.assertMatchesSchema(response, self.DETAIL, "patch", 200)

    def test_a_delete_sends_the_removal_it_describes(self):
        uid, etag = self.created()
        self.client.force_login(self.user)

        response = self.client.delete(
            f"{self.detail_url(uid)}?confirm=API-TEST", HTTP_IF_MATCH=etag
        )

        self.assertMatchesSchema(response, self.DETAIL, "delete", 200)

    def test_a_history_read_sends_the_page_it_describes(self):
        uid, etag = self.created()
        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        response = self.client.get(f"/api/v0/scenario-bundles/{uid}/history/")

        self.assertMatchesSchema(
            response, "/api/v0/scenario-bundles/{uid}/history/", "get", 200
        )

    def test_a_history_read_with_its_triples_still_matches(self):
        uid, _ = self.created()

        response = self.client.get(
            f"/api/v0/scenario-bundles/{uid}/history/?expand=triples"
        )

        self.assertMatchesSchema(
            response, "/api/v0/scenario-bundles/{uid}/history/", "get", 200
        )


class PartResponseSchemaTest(ResponseSchemaTestCase):
    """The two addressable parts, whose schemas the subclasses supply."""

    SCENARIOS = "/api/v0/scenario-bundles/{uid}/scenarios/"
    SCENARIO = "/api/v0/scenario-bundles/{uid}/scenarios/{pid}/"
    REPORTS = "/api/v0/scenario-bundles/{uid}/study-reports/"
    REPORT = "/api/v0/scenario-bundles/{uid}/study-reports/{pid}/"

    def test_a_scenario_create_sends_what_it_describes(self):
        uid, etag = self.created()

        response = self.add_scenario(uid, etag)

        self.assertMatchesSchema(response, self.SCENARIOS, "post", 201)

    def test_a_scenario_listing_sends_the_page_it_describes(self):
        uid, _sid, _etag = self.with_one_scenario()

        response = self.client.get(self.scenarios_url(uid))

        self.assertMatchesSchema(response, self.SCENARIOS, "get", 200)

    def test_a_scenario_read_sends_what_it_describes(self):
        uid, sid, _etag = self.with_one_scenario()

        response = self.client.get(f"{self.scenario_url(uid, sid)}?expand=labels")

        self.assertMatchesSchema(response, self.SCENARIO, "get", 200)

    def test_a_scenario_patch_sends_what_it_describes(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.patch_scenario(uid, sid, {"label": "Renamed"}, etag)

        self.assertMatchesSchema(response, self.SCENARIO, "patch", 200)

    def test_a_scenario_delete_sends_the_removal_it_describes(self):
        uid, sid, etag = self.with_one_scenario()
        self.client.force_login(self.user)

        response = self.client.delete(self.scenario_url(uid, sid), HTTP_IF_MATCH=etag)

        self.assertMatchesSchema(response, self.SCENARIO, "delete", 200)

    def test_a_study_report_create_sends_what_it_describes(self):
        uid, etag = self.created()

        response = self.add_report(uid, etag)

        self.assertMatchesSchema(response, self.REPORTS, "post", 201)

    def test_a_study_report_listing_sends_the_page_it_describes(self):
        uid, _rid, _etag = self.with_one_report()

        response = self.client.get(self.reports_url(uid))

        self.assertMatchesSchema(response, self.REPORTS, "get", 200)

    def test_a_study_report_read_sends_what_it_describes(self):
        uid, rid, _etag = self.with_one_report(
            {**VALID_REPORT, "doi": "10.1000/x", "reference": "https://example.org/p"}
        )

        response = self.client.get(self.report_url(uid, rid))

        self.assertMatchesSchema(response, self.REPORT, "get", 200)

    def test_a_study_report_patch_sends_what_it_describes(self):
        uid, rid, etag = self.with_one_report()

        response = self.patch_report(uid, rid, {"label": "Renamed"}, etag)

        self.assertMatchesSchema(response, self.REPORT, "patch", 200)

    def test_a_study_report_delete_sends_the_removal_it_describes(self):
        uid, rid, etag = self.with_one_report()
        self.client.force_login(self.user)

        response = self.client.delete(self.report_url(uid, rid), HTTP_IF_MATCH=etag)

        self.assertMatchesSchema(response, self.REPORT, "delete", 200)


class DatasetLinkResponseSchemaTest(ResponseSchemaTestCase):
    """The link bodies, whose `_meta` says what the citation means today."""

    LINKS = "/api/v0/scenario-bundles/{uid}/scenarios/{sid}/datasets/"
    LINK = "/api/v0/scenario-bundles/{uid}/scenarios/{sid}/datasets/{did}/"

    def test_a_link_create_sends_what_it_describes(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.add_link(uid, sid, etag)

        self.assertMatchesSchema(response, self.LINKS, "post", 201)

    def test_a_link_listing_sends_the_page_it_describes(self):
        uid, sid, _did, _etag = self.with_one_link()

        response = self.client.get(self.links_url(uid, sid))

        self.assertMatchesSchema(response, self.LINKS, "get", 200)

    def test_a_link_read_sends_what_it_describes(self):
        uid, sid, did, _etag = self.with_one_link()

        response = self.client.get(f"{self.link_url(uid, sid, did)}?expand=labels")

        self.assertMatchesSchema(response, self.LINK, "get", 200)

    def test_a_link_read_still_matches_when_it_resolves_to_nothing(self):
        # `resolvable` and `tables` are the two keys whose nulls carry meaning,
        # and a schema that forgot to allow them would only fail here.
        uid, sid, did, _etag = self.with_one_link(
            {"type": "input", "ref": "table", "name": "no_such_table_anywhere"}
        )

        response = self.client.get(self.link_url(uid, sid, did))

        self.assertMatchesSchema(response, self.LINK, "get", 200)
        self.assertFalse(response.data["_meta"]["resolvable"])

    def test_a_link_delete_sends_the_removal_it_describes(self):
        uid, sid, did, etag = self.with_one_link()
        self.client.force_login(self.user)

        response = self.client.delete(self.link_url(uid, sid, did), HTTP_IF_MATCH=etag)

        self.assertMatchesSchema(response, self.LINK, "delete", 200)
