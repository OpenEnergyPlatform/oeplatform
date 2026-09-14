"""A write is judged by what it adds, not by what it inherited.

Every scenario bundle in the live graph fails shape validation, and about a
third of those failures are **missing content** -- which sector a study covers,
who wrote a publication -- that no repair script can infer. Those are exactly
the fields a person would supply *by patching*. So a rule of "the post-state
must conform" makes the defect unfixable through the API: you would need a
patch to add the missing sector, and the patch is refused because the sector is
missing.

The promise that matters survives: **nothing invalid is written by this API.**
What is given up is holding a client responsible for damage that predates it.

A create is the deliberate exception and is tested here too -- it has no
pre-state, so everything it produces is new, and a bundle cannot be *created*
broken.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from rdflib import Graph

from factsheet.models import ScenarioBundleAccessControl
from oekg.bundles import OEO, build_bundle_graph
from oekg.tests.bundle_fixtures import VALID_PAYLOAD, BundleApiTestCase

# The shape requires at least one technology. A bundle without one is exactly
# the kind of thing the browser has written for years.
INHERITED_DEFECT = {k: v for k, v in VALID_PAYLOAD.items() if k != "technologies"}


class InheritedViolationTest(BundleApiTestCase):
    def existing_bundle(self, payload=None, uid=None):
        """A bundle put straight into the store, as another writer would."""
        uid = uid or "11111111-2222-3333-4444-555555555555"
        self.store.insert(build_bundle_graph(uid, payload or INHERITED_DEFECT))
        ScenarioBundleAccessControl.objects.create(owner_user=self.user, bundle_id=uid)
        return uid

    def test_a_bundle_that_already_violates_the_shape_can_be_patched(self):
        # The whole point: a defect the caller did not cause does not stand
        # between them and a change to an unrelated field.
        uid = self.existing_bundle()

        response = self.patch(uid, {"label": "Renamed"}, if_match='"0"')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(self.detail_url(uid)).data["label"], "Renamed")

    def test_the_inherited_violation_is_still_there_afterwards(self):
        # Accepted, not repaired. The API does not quietly fix what it did not
        # break, and the bundle stays as non-conforming as it was.
        uid = self.existing_bundle()

        self.patch(uid, {"label": "Renamed"}, if_match='"0"')

        self.assertEqual(self.client.get(self.detail_url(uid)).data["technologies"], [])

    def test_a_patch_that_introduces_a_violation_is_still_refused(self):
        uid = self.existing_bundle()

        response = self.patch(uid, {"sectors": []}, if_match='"0"')

        self.assertEqual(response.status_code, 400, response.data)
        messages = [v["message"] for v in response.data["violations"]]
        self.assertIn("Study target: This should cover at least one sector.", messages)

    def test_the_refusal_names_only_what_the_write_added(self):
        # The inherited one must not appear in the list, or a client cannot
        # tell which of them is its own doing.
        uid = self.existing_bundle()

        response = self.patch(uid, {"sectors": []}, if_match='"0"')

        messages = [v["message"] for v in response.data["violations"]]
        self.assertNotIn(
            "Study target: This should cover at least one technology.", messages
        )

    def test_the_refusal_says_how_many_were_inherited(self):
        # Named rather than hidden: the bundle is not clean, and a client that
        # succeeds should still be able to learn that.
        uid = self.existing_bundle()

        response = self.patch(uid, {"sectors": []}, if_match='"0"')

        self.assertGreaterEqual(response.data["pre_existing_violations"], 1)

    def test_the_refusal_keeps_its_types(self):
        # The framework rewrites every scalar in an error body it renders
        # itself, so `None` would come back as the string "None" and a count as
        # a string. Refusals carry their own response for exactly this reason.
        uid = self.existing_bundle()

        response = self.patch(uid, {"sectors": []}, if_match='"0"')

        self.assertIsInstance(response.data["pre_existing_violations"], int)
        nullable = [v["path"] for v in response.data["violations"]]
        self.assertTrue(
            any(p is None for p in nullable)
            or all(isinstance(p, str) for p in nullable),
            nullable,
        )
        for violation in response.data["violations"]:
            self.assertNotEqual(violation["value"], "None", violation)

    def test_a_patch_that_repairs_the_bundle_is_accepted(self):
        uid = self.existing_bundle()

        response = self.patch(
            uid, {"technologies": [str(OEO.OEO_00000407)]}, if_match='"0"'
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            self.client.get(self.detail_url(uid)).data["technologies"],
            [str(OEO.OEO_00000407)],
        )

    def test_a_second_copy_of_an_inherited_violation_is_refused(self):
        # Compared as a multiset, not as a set: a bundle that already misses
        # one required field may not come out missing two.
        uid = self.existing_bundle()

        response = self.patch(
            uid, {"sector_divisions": [], "sectors": []}, if_match='"0"'
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(len(response.data["violations"]), 2, response.data)

    def test_nothing_is_written_when_a_new_violation_is_refused(self):
        uid = self.existing_bundle()

        self.patch(uid, {"sectors": [], "label": "Should not land"}, if_match='"0"')

        read = self.client.get(self.detail_url(uid)).data
        self.assertEqual(read["label"], VALID_PAYLOAD["label"])
        self.assertEqual(read["sectors"], VALID_PAYLOAD["sectors"])


class CreateStillHasToConformTest(BundleApiTestCase):
    """The deliberate exception: a bundle cannot be created broken."""

    def test_a_create_missing_a_required_field_is_refused(self):
        response = self.create(INHERITED_DEFECT)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(self.store.ask("ASK { ?s ?p ?o }"))

    def test_a_create_reports_every_violation_it_has(self):
        # No pre-state to subtract, so nothing is forgiven.
        response = self.create(
            {k: v for k, v in INHERITED_DEFECT.items() if k != "sectors"}
        )

        messages = {v["message"] for v in response.data["violations"]}
        self.assertIn("Study target: This should cover at least one sector.", messages)
        self.assertIn(
            "Study target: This should cover at least one technology.", messages
        )


class IntroducedViolationsUnitTest(BundleApiTestCase):
    """The comparison itself."""

    def test_an_unchanged_graph_introduces_nothing(self):
        from oekg.validation import introduced_violations

        graph = build_bundle_graph("u1", INHERITED_DEFECT)

        new, inherited = introduced_violations(graph, graph)

        self.assertEqual(new, [])
        self.assertGreaterEqual(inherited, 1)

    def test_an_empty_before_forgives_nothing(self):
        from oekg.validation import introduced_violations

        after = build_bundle_graph("u1", INHERITED_DEFECT)

        new, inherited = introduced_violations(Graph(), after)

        self.assertEqual(inherited, 0)
        self.assertGreaterEqual(len(new), 1)
