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

How it validates -- `nullable` translated, schemas deliberately open -- is
shared with the dataset half of the API and lives in
`api/tests/response_schema.py`. Open matters here in particular: `_meta`
gains keys on request (`labels`) and on trouble (`history_recorded`).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api.tests.response_schema import ResponseSchemaAssertions
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.test_bundle_replace import ReplaceTestCase
from oekg.tests.test_dataset_link_api import DatasetLinkTestCase
from oekg.tests.test_study_report_api import VALID_REPORT, StudyReportTestCase


class ResponseSchemaTestCase(
    ResponseSchemaAssertions, DatasetLinkTestCase, StudyReportTestCase
):
    """One bundle with one of everything on it, and a validator over it.

    Both fixture bases, because this is the one place that needs a bundle
    carrying every kind of thing at once -- which is also where a read and its
    schema come apart most easily.
    """

    SCHEMA_SOURCE = "the serializers in oekg/read_serializers.py"


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


class ReplaceResponseSchemaTest(ResponseSchemaTestCase, ReplaceTestCase):
    """The one body that is a bundle *and* a removal report."""

    REPLACE = "/api/v0/scenario-bundles/{uid}/replace/"

    def test_a_replace_sends_the_bundle_and_the_report_it_describes(self):
        uid, sid, _did, _etag = self.with_one_link()
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body, label="Declared"), etag)

        self.assertMatchesSchema(response, self.REPLACE, "post", 200)

    def test_a_replace_that_removed_something_still_matches(self):
        # `_meta.deleted` and `_meta.unlinked` are empty on the happy path, so
        # a schema that got their entries wrong would only fail here.
        uid, sid, _did, _etag = self.with_one_link()
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body, scenarios=[]), etag)

        self.assertTrue(response.data[READ_ONLY_CONTAINER]["deleted"])
        self.assertMatchesSchema(response, self.REPLACE, "post", 200)


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
