"""Study reports: the publication a bundle is written up in, addressable.

A study report is a sub-resource for exactly the reason a scenario factsheet
is -- the shape gives it its own has-uuid -- so these tests are deliberately
the same shape as the scenario ones. What they add is what is particular to a
report:

- **its authors are shared nodes**, so a write may point at one and may never
  rename it;
- **its reference is the URL itself**, typed as a reference rather than minted
  as a node with a label, because nothing asks a reference for one;
- **its publication date is a real date**, refused here rather than by the
  store.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import SimpleTestCase
from django.urls import reverse
from rdflib.namespace import SH

from factsheet.models import OEKG_Modifications
from login.models import myuser
from oekg.bundles import (
    REFERENCE_CLASS,
    STUDY_REPORT_CLASS,
    STUDY_REPORT_FIELDS,
    bundle_iri,
)
from oekg.fields import HAS_UUID, OEO
from oekg.history import CREATE, UPDATE
from oekg.serializers import READ_ONLY_CONTAINER, StudyReportSerializer
from oekg.shape import shape_graph
from oekg.tests import RequiresShapeArtifactsMixin
from oekg.tests.bundle_fixtures import VALID_PAYLOAD, BundleApiTestCase

# What the shape requires of a study report: a label, at least one author, and
# exactly one publication date.
VALID_REPORT = {
    "label": "Energy scenarios for 2045",
    "authors": [{"label": "Ada Lovelace"}],
    "publication_date": "2024-03-01T00:00:00Z",
}


class StudyReportTestCase(BundleApiTestCase):
    def reports_url(self, uid):
        return reverse("api:scenario-bundle-study-reports", kwargs={"uid": uid})

    def report_url(self, uid, rid):
        return reverse(
            "api:scenario-bundle-study-report", kwargs={"uid": uid, "pid": rid}
        )

    def add_report(self, uid, etag, payload=None, as_user=None):
        self.client.force_login(as_user or self.user)
        return self.client.post(
            self.reports_url(uid),
            data=payload if payload is not None else VALID_REPORT,
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

    def patch_report(self, uid, rid, payload, etag, as_user=None):
        self.client.force_login(as_user or self.user)
        return self.client.patch(
            self.report_url(uid, rid),
            data=payload,
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

    def with_one_report(self, payload=None):
        """A bundle plus one study report. Returns uid, rid and the etag."""
        uid, etag = self.created()
        response = self.add_report(uid, etag, payload)
        self.assertEqual(response.status_code, 201, response.data)
        return uid, response.data[READ_ONLY_CONTAINER]["uid"], response["ETag"]


class StudyReportWriteTest(StudyReportTestCase):
    def test_a_report_is_added_to_a_bundle(self):
        uid, etag = self.created()

        response = self.add_report(uid, etag)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["label"], VALID_REPORT["label"])
        self.assertIn(response.data[READ_ONLY_CONTAINER]["uid"], response["Location"])

    def test_the_report_is_typed_and_carries_the_uuid_its_url_names(self):
        # Both are shape requirements: the type makes it a study report, the
        # uuid makes it addressable.
        _, rid, _ = self.with_one_report()

        self.assertTrue(
            self.store.ask(
                "ASK { ?node a %s ; %s %s }"
                % (STUDY_REPORT_CLASS.n3(), HAS_UUID.n3(), f'"{rid}"')
            )
        )

    def test_the_report_hangs_off_its_bundle(self):
        uid, _, _ = self.with_one_report()

        self.assertTrue(
            self.store.ask(
                "ASK { %s <http://purl.obolibrary.org/obo/BFO_0000051> ?node . "
                "?node a %s }" % (bundle_iri(uid).n3(), STUDY_REPORT_CLASS.n3())
            )
        )

    def test_the_server_mints_the_identifier(self):
        uid, etag = self.created()

        response = self.add_report(
            uid, etag, {**VALID_REPORT, "uid": "chosen-by-the-client"}
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("uid", response.data)

    def test_a_report_reads_back_what_was_written(self):
        uid, rid, _ = self.with_one_report(
            {**VALID_REPORT, "doi": "10.1000/xyz", "reference": "https://example.org/r"}
        )

        read = self.client.get(self.report_url(uid, rid)).data

        self.assertEqual(read["label"], VALID_REPORT["label"])
        self.assertEqual(read["doi"], "10.1000/xyz")
        self.assertEqual(read["reference"], "https://example.org/r")
        self.assertEqual(read["authors"][0]["label"], "Ada Lovelace")

    def test_the_publication_date_reads_back_in_a_form_a_write_accepts(self):
        # The round trip is the contract: a read is sendable straight back, and
        # the replace endpoint will depend on it.
        uid, rid, etag = self.with_one_report()
        read = self.client.get(self.report_url(uid, rid)).data

        again = self.patch_report(
            uid, rid, {"publication_date": read["publication_date"]}, etag
        )

        self.assertEqual(again.status_code, 200, again.data)
        self.assertEqual(again.data["publication_date"], read["publication_date"])

    def test_the_reference_is_the_url_itself_typed_as_a_reference(self):
        # Not a minted node carrying the URL as a literal: the thing cited IS
        # the document at that address, and the shape asks for its class.
        self.with_one_report({**VALID_REPORT, "reference": "https://example.org/r"})

        self.assertTrue(
            self.store.ask(
                "ASK { <https://example.org/r> a %s }" % REFERENCE_CLASS.n3()
            )
        )

    def test_a_publication_date_that_is_not_a_date_is_refused_here(self):
        uid, etag = self.created()

        response = self.add_report(
            uid, etag, {**VALID_REPORT, "publication_date": "sometime in spring"}
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("publication_date", response.data)

    def test_a_report_with_no_author_is_refused_by_the_shape(self):
        uid, etag = self.created()

        response = self.add_report(uid, etag, {**VALID_REPORT, "authors": []})

        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(response.data["violations"])

    def test_a_refused_report_writes_nothing(self):
        uid, etag = self.created()

        self.add_report(uid, etag, {**VALID_REPORT, "authors": []})

        self.assertFalse(self.store.ask("ASK { ?node a %s }" % STUDY_REPORT_CLASS.n3()))

    def test_an_unknown_key_is_refused(self):
        uid, etag = self.created()

        response = self.add_report(uid, etag, {**VALID_REPORT, "editor": "somebody"})

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("editor", response.data)


class StudyReportListTest(StudyReportTestCase):
    def test_the_collection_lists_the_bundles_reports(self):
        uid, etag = self.created()
        etag = self.add_report(uid, etag)["ETag"]
        self.add_report(uid, etag, {**VALID_REPORT, "label": "A second report"})

        listed = self.client.get(self.reports_url(uid)).data

        self.assertEqual(listed["count"], 2)
        self.assertEqual(
            [row["label"] for row in listed["results"]],
            ["A second report", "Energy scenarios for 2045"],
        )

    def test_the_listing_carries_the_bundles_entity_tag(self):
        uid, _, etag = self.with_one_report()

        response = self.client.get(self.reports_url(uid))

        self.assertEqual(response["ETag"], etag)

    def test_a_bundle_read_nests_its_study_reports(self):
        # What a read returns is what a create accepts back.
        uid, _, _ = self.with_one_report()

        read = self.client.get(self.detail_url(uid)).data

        self.assertEqual(len(read["study_reports"]), 1)
        self.assertEqual(read["study_reports"][0]["label"], VALID_REPORT["label"])

    def test_reading_a_report_that_is_not_there_says_so(self):
        uid, _ = self.created()

        response = self.client.get(self.report_url(uid, "no-such-report"))

        self.assertEqual(response.status_code, 404)
        self.assertIn("study report", response.data["detail"])


class StudyReportPatchTest(StudyReportTestCase):
    def test_a_patch_changes_only_the_field_it_names(self):
        uid, rid, etag = self.with_one_report()

        response = self.patch_report(uid, rid, {"doi": "10.1000/abc"}, etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["doi"], "10.1000/abc")
        self.assertEqual(response.data["label"], VALID_REPORT["label"])

    def test_a_patch_leaves_a_sibling_report_alone(self):
        uid, etag = self.created()
        first = self.add_report(uid, etag)
        second = self.add_report(
            uid, first["ETag"], {**VALID_REPORT, "label": "Another report"}
        )
        rid = first.data[READ_ONLY_CONTAINER]["uid"]

        self.patch_report(uid, rid, {"label": "Renamed"}, second["ETag"])

        other = second.data[READ_ONLY_CONTAINER]["uid"]
        self.assertEqual(
            self.client.get(self.report_url(uid, other)).data["label"],
            "Another report",
        )

    def test_a_patch_without_a_precondition_is_refused(self):
        uid, rid, _ = self.with_one_report()
        self.client.force_login(self.user)

        response = self.client.patch(
            self.report_url(uid, rid),
            data={"doi": "10.1000/abc"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 428, response.data)

    def test_a_stale_precondition_is_refused(self):
        uid, rid, etag = self.with_one_report()
        self.patch_report(uid, rid, {"doi": "10.1000/abc"}, etag)

        again = self.patch_report(uid, rid, {"doi": "10.1000/def"}, etag)

        self.assertEqual(again.status_code, 412, again.data)

    def test_a_stranger_cannot_change_a_report(self):
        uid, rid, etag = self.with_one_report()
        stranger = myuser.objects.create_user(
            name="stranger", email="stranger@example.org", affiliation=""
        )

        response = self.patch_report(
            uid, rid, {"doi": "10.1000/abc"}, etag, as_user=stranger
        )

        self.assertEqual(response.status_code, 403, response.data)

    def test_patching_a_report_that_is_not_there_says_so_before_the_precondition(self):
        uid, _ = self.created()
        self.client.force_login(self.user)

        response = self.client.patch(
            self.report_url(uid, "no-such-report"),
            data={"doi": "10.1000/abc"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404, response.data)


class StudyReportAuthorTest(StudyReportTestCase):
    """Authors are shared: referencing one is allowed, renaming it is not."""

    def existing_author(self):
        uid, rid, etag = self.with_one_report()
        read = self.client.get(self.report_url(uid, rid)).data
        return uid, etag, read["authors"][0]["iri"]

    def test_a_second_report_may_reference_an_existing_author(self):
        uid, etag, iri = self.existing_author()

        response = self.add_report(
            uid,
            etag,
            {
                **VALID_REPORT,
                "label": "A second report",
                "authors": [{"iri": iri, "label": "Ada Lovelace"}],
            },
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["authors"][0]["iri"], iri)

    def test_referencing_an_author_does_not_give_it_a_second_label(self):
        # Two labels on one node violates the shape for every bundle citing it,
        # not only for the one being written.
        uid, etag, iri = self.existing_author()

        self.add_report(
            uid,
            etag,
            {
                **VALID_REPORT,
                "label": "A second report",
                "authors": [{"iri": iri, "label": "Ada Lovelace"}],
            },
        )

        rows = self.store.select(
            "SELECT ?label WHERE { <%s> "
            "<http://www.w3.org/2000/01/rdf-schema#label> ?label }" % iri
        )
        self.assertEqual(len(rows), 1)

    def test_an_author_cannot_be_renamed_through_this_api(self):
        uid, etag, iri = self.existing_author()

        response = self.add_report(
            uid,
            etag,
            {
                **VALID_REPORT,
                "label": "A second report",
                "authors": [{"iri": iri, "label": "A. Lovelace"}],
            },
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data["conflicts"][0]["iri"], iri)


class NestedStudyReportTest(StudyReportTestCase):
    def test_a_bundle_is_created_with_its_study_reports_in_one_call(self):
        uid, _ = self.created({**VALID_PAYLOAD, "study_reports": [VALID_REPORT]})

        read = self.client.get(self.detail_url(uid)).data

        self.assertEqual(len(read["study_reports"]), 1)
        self.assertEqual(read["study_reports"][0]["label"], VALID_REPORT["label"])

    def test_two_nested_reports_get_different_identifiers(self):
        uid, _ = self.created(
            {
                **VALID_PAYLOAD,
                "study_reports": [
                    VALID_REPORT,
                    {**VALID_REPORT, "label": "A second report"},
                ],
            }
        )

        read = self.client.get(self.detail_url(uid)).data

        identifiers = {r[READ_ONLY_CONTAINER]["uid"] for r in read["study_reports"]}
        self.assertEqual(len(identifiers), 2)

    def test_a_bundle_patch_cannot_reach_a_study_report(self):
        # The asymmetry that stops a bundle-level edit dropping a part by
        # leaving it out: the patch serializer has no such key at all.
        uid, etag = self.created()

        response = self.patch(uid, {"study_reports": [VALID_REPORT]}, if_match=etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("study_reports", response.data)

    def test_a_nested_report_the_shape_rejects_writes_no_bundle(self):
        response = self.create(
            {**VALID_PAYLOAD, "study_reports": [{**VALID_REPORT, "authors": []}]}
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(self.store.ask("ASK { ?bundle a %s }" % OEO.OEO_00020227.n3()))


class StudyReportHistoryTest(StudyReportTestCase):
    def test_adding_a_report_records_a_create_naming_the_report(self):
        uid, rid, _ = self.with_one_report()

        entry = OEKG_Modifications.objects.filter(resource_uuid=rid).get()

        self.assertEqual(entry.verb, CREATE)
        self.assertEqual(entry.resource_type, str(STUDY_REPORT_CLASS))
        self.assertEqual(entry.bundle_id, uid)

    def test_patching_a_report_records_an_update(self):
        uid, rid, etag = self.with_one_report()

        self.patch_report(uid, rid, {"doi": "10.1000/abc"}, etag)

        verbs = list(
            OEKG_Modifications.objects.filter(resource_uuid=rid)
            .order_by("id")
            .values_list("verb", flat=True)
        )
        self.assertEqual(verbs, [CREATE, UPDATE])

    def test_the_history_names_the_field_that_changed(self):
        # In the study report's vocabulary, not the bundle's: the two tables
        # share `label` and agree about almost nothing else.
        uid, rid, etag = self.with_one_report()
        self.patch_report(uid, rid, {"doi": "10.1000/abc"}, etag)

        results = self.client.get(
            reverse("api:scenario-bundle-history", kwargs={"uid": uid})
        ).data["results"]

        self.assertEqual(
            [(c["field"], c["added"]) for c in results[0]["changes"]],
            [("doi", ["10.1000/abc"])],
        )

    def test_an_authors_own_label_is_not_read_as_the_reports_label(self):
        # The trap this rendering has to avoid: a minted author carries an
        # rdfs:label into the same diff, and `label` is a field of the report.
        # Attributing it would say the report was renamed when an author was
        # added.
        uid, rid, etag = self.with_one_report()
        self.patch_report(uid, rid, {"authors": [{"label": "Grace Hopper"}]}, etag)

        results = self.client.get(
            reverse("api:scenario-bundle-history", kwargs={"uid": uid})
        ).data["results"]

        named = {c["field"] for c in results[0]["changes"] if c["field"]}
        self.assertEqual(named, {"authors"})

    def test_the_history_reads_the_report_back(self):
        uid, rid, _ = self.with_one_report()

        results = self.client.get(
            reverse("api:scenario-bundle-history", kwargs={"uid": uid})
        ).data["results"]

        self.assertEqual(results[0]["resource"]["uid"], rid)
        self.assertEqual(results[0]["resource"]["type"], str(STUDY_REPORT_CLASS))


class StudyReportShapeConformanceTest(RequiresShapeArtifactsMixin, SimpleTestCase):
    """Every property the shape validates on a study report is accounted for.

    The anti-drift property a generator would have given, without the
    generator: if the shape gains a property, this fails rather than the API
    quietly ignoring it.
    """

    def test_every_study_report_property_in_the_shape_is_covered(self):
        shape = shape_graph()
        node = shape.value(predicate=SH.targetClass, object=STUDY_REPORT_CLASS)
        paths = {
            str(shape.value(constraint, SH.path))
            for constraint in shape.objects(node, SH.property)
            if shape.value(constraint, SH.path) is not None
        }

        covered = {str(field.predicate) for field in STUDY_REPORT_FIELDS}
        # The uuid is the server's to mint, so it is an identity rather than a
        # field -- covered by the builder, absent from the serializer.
        covered.add(str(HAS_UUID))

        self.assertTrue(paths, "the shape declares no study report properties")
        self.assertEqual(paths - covered, set())
        self.assertEqual(covered - paths, set())

    def test_the_serializer_and_the_builder_agree(self):
        self.assertEqual(
            set(StudyReportSerializer().fields),
            {field.name for field in STUDY_REPORT_FIELDS},
        )

    def test_a_client_cannot_supply_the_identifier(self):
        self.assertNotIn("uid", StudyReportSerializer().fields)
        self.assertNotIn("uuid", StudyReportSerializer().fields)
