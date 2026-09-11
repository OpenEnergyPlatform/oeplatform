"""Scenario factsheets: addressable, but still part of their bundle.

The shape decides which parts of a bundle get URLs -- a scenario carries its
own has-uuid, a framework does not -- so the rule is checkable rather than
negotiated per class.

Two asymmetries carry this slice and both are easy to lose:

- **Nested on create, addressable on update.** A bundle `POST` builds its
  scenarios with it; a bundle `PATCH` cannot reach one. That is what lets a
  pipeline create a whole bundle in one call without giving any call the power
  to drop its parts by omitting them.
- **The bundle owns the version, the ownership and the entity tag.** A scenario
  has no independent existence to guard, and every constraint in the shape is
  bundle-local, so a scenario alone is not a unit the shape could judge.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import SimpleTestCase
from django.urls import reverse
from rdflib.namespace import SH

from factsheet.models import OEKG_Modifications, ScenarioBundleAccessControl
from login.models import myuser
from oekg.bundles import HAS_UUID, OEO, SCENARIO_CLASS, SCENARIO_FIELDS, bundle_iri
from oekg.history import CREATE, UPDATE
from oekg.serializers import READ_ONLY_CONTAINER, ScenarioSerializer
from oekg.shape import shape_graph
from oekg.tests import RequiresShapeArtifactsMixin
from oekg.tests.bundle_fixtures import VALID_PAYLOAD, BundleApiTestCase

# The three the scenario shape requires, and a real pick from its sh:in list.
VALID_SCENARIO = {
    "label": "A high renewables scenario",
    "acronym": "HIGH-RE",
    "scenario_types": [str(OEO.OEO_00000364)],
}


class ScenarioTestCase(BundleApiTestCase):
    def scenarios_url(self, uid):
        return reverse("api:scenario-bundle-scenarios", kwargs={"uid": uid})

    def scenario_url(self, uid, sid):
        return reverse("api:scenario-bundle-scenario", kwargs={"uid": uid, "sid": sid})

    def add_scenario(self, uid, etag, payload=None, as_user=None):
        self.client.force_login(as_user or self.user)
        return self.client.post(
            self.scenarios_url(uid),
            data=payload if payload is not None else VALID_SCENARIO,
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

    def patch_scenario(self, uid, sid, payload, etag, as_user=None):
        self.client.force_login(as_user or self.user)
        return self.client.patch(
            self.scenario_url(uid, sid),
            data=payload,
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

    def with_one_scenario(self):
        """A bundle plus one scenario. Returns uid, sid and the current etag."""
        uid, etag = self.created()
        response = self.add_scenario(uid, etag)
        self.assertEqual(response.status_code, 201, response.data)
        return uid, response.data[READ_ONLY_CONTAINER]["uid"], response["ETag"]


class NestedCreateTest(ScenarioTestCase):
    def test_a_bundle_is_created_with_its_scenarios_in_one_call(self):
        # The modelling pipeline's batch case: one request, whole bundle.
        uid, _ = self.created({**VALID_PAYLOAD, "scenarios": [VALID_SCENARIO]})

        read = self.client.get(self.detail_url(uid)).data

        self.assertEqual(len(read["scenarios"]), 1)
        self.assertEqual(read["scenarios"][0]["acronym"], VALID_SCENARIO["acronym"])

    def test_two_nested_scenarios_get_different_identifiers(self):
        uid, _ = self.created(
            {
                **VALID_PAYLOAD,
                "scenarios": [
                    VALID_SCENARIO,
                    {**VALID_SCENARIO, "acronym": "LOW-RE"},
                ],
            }
        )

        read = self.client.get(self.detail_url(uid)).data

        identifiers = {s[READ_ONLY_CONTAINER]["uid"] for s in read["scenarios"]}
        self.assertEqual(len(identifiers), 2)

    def test_a_nested_scenario_is_typed_and_carries_its_uuid(self):
        # Both are shape requirements: the type makes it a scenario, the uuid
        # makes it addressable.
        uid, _ = self.created({**VALID_PAYLOAD, "scenarios": [VALID_SCENARIO]})
        sid = self.client.get(self.detail_url(uid)).data["scenarios"][0][
            READ_ONLY_CONTAINER
        ]["uid"]

        self.assertTrue(
            self.store.ask(
                "ASK { ?node a %s ; %s %s }"
                % (SCENARIO_CLASS.n3(), HAS_UUID.n3(), f'"{sid}"')
            )
        )

    def test_a_nested_scenario_the_shape_rejects_writes_nothing(self):
        # No scenario type: the shape requires at least one.
        broken = {
            key: v for key, v in VALID_SCENARIO.items() if key != "scenario_types"
        }

        response = self.create({**VALID_PAYLOAD, "scenarios": [broken]})

        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(self.store.ask("ASK { ?s ?p ?o }"))

    def test_the_whole_bundle_with_its_scenarios_is_one_write(self):
        from unittest.mock import patch

        from oekg.graph_store import GraphStore

        real_update, updates = GraphStore.update, []

        def counting(store, *operations):
            updates.append(operations)
            return real_update(store, *operations)

        with patch.object(GraphStore, "update", counting):
            response = self.create({**VALID_PAYLOAD, "scenarios": [VALID_SCENARIO]})

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(updates), 1, updates)

    def test_a_read_with_scenarios_can_be_sent_back_to_create_a_copy(self):
        # The round trip the replace endpoint will depend on: what a read
        # returns is what a write accepts, sub-resources included.
        uid, _ = self.created({**VALID_PAYLOAD, "scenarios": [VALID_SCENARIO]})
        read = self.client.get(self.detail_url(uid)).data

        copy = self.client.post(
            self.collection_url,
            data={**read, "acronym": "API-TEST-COPY"},
            content_type="application/json",
        )

        self.assertEqual(copy.status_code, 201, copy.data)
        self.assertEqual(len(copy.data["scenarios"]), 1)

    def test_a_bundle_patch_still_cannot_reach_a_scenario(self):
        # The asymmetry: nesting on create does not open a door on update.
        uid, etag = self.created()

        response = self.patch(uid, {"scenarios": [VALID_SCENARIO]}, if_match=etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("scenarios", response.data)


class ScenarioCollectionTest(ScenarioTestCase):
    def test_a_scenario_is_added_to_an_existing_bundle(self):
        uid, etag = self.created()

        response = self.add_scenario(uid, etag)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["acronym"], VALID_SCENARIO["acronym"])

    def test_the_response_names_where_the_scenario_now_lives(self):
        uid, etag = self.created()

        response = self.add_scenario(uid, etag)

        sid = response.data[READ_ONLY_CONTAINER]["uid"]
        self.assertEqual(response["Location"], self.scenario_url(uid, sid))

    def test_the_collection_lists_what_the_bundle_has(self):
        uid, _, _ = self.with_one_scenario()

        listing = self.client.get(self.scenarios_url(uid))

        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["count"], 1)

    def test_the_collection_is_public(self):
        uid, _, _ = self.with_one_scenario()
        self.client.logout()

        self.assertEqual(self.client.get(self.scenarios_url(uid)).status_code, 200)

    def test_it_lists_only_this_bundle_s_scenarios(self):
        first, _, _ = self.with_one_scenario()
        second, second_etag = self.created({**VALID_PAYLOAD, "acronym": "OTHER"})
        self.add_scenario(second, second_etag, {**VALID_SCENARIO, "acronym": "OTHER-S"})

        acronyms = [
            entry["acronym"]
            for entry in self.client.get(self.scenarios_url(first)).data["results"]
        ]

        self.assertEqual(acronyms, [VALID_SCENARIO["acronym"]])

    def test_adding_to_an_unknown_bundle_is_a_404(self):
        response = self.add_scenario("11111111-2222-3333-4444-555555555555", '"1"')

        self.assertEqual(response.status_code, 404, response.data)


class ScenarioItemTest(ScenarioTestCase):
    def test_a_scenario_reads_back(self):
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(self.scenario_url(uid, sid))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["label"], VALID_SCENARIO["label"])
        self.assertEqual(response.data[READ_ONLY_CONTAINER]["uid"], sid)

    def test_a_read_needs_no_authentication(self):
        uid, sid, _ = self.with_one_scenario()
        self.client.logout()

        self.assertEqual(self.client.get(self.scenario_url(uid, sid)).status_code, 200)

    def test_an_unknown_scenario_is_a_404(self):
        uid, _ = self.created()

        response = self.client.get(self.scenario_url(uid, "no-such-scenario"))

        self.assertEqual(response.status_code, 404)

    def test_patching_one_field_leaves_the_others_intact(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.patch_scenario(uid, sid, {"label": "Renamed"}, etag)

        self.assertEqual(response.status_code, 200, response.data)
        read = self.client.get(self.scenario_url(uid, sid)).data
        self.assertEqual(read["label"], "Renamed")
        self.assertEqual(read["acronym"], VALID_SCENARIO["acronym"])
        self.assertEqual(read["scenario_types"], VALID_SCENARIO["scenario_types"])

    def test_patching_one_scenario_leaves_its_siblings_alone(self):
        uid, first, etag = self.with_one_scenario()
        added = self.add_scenario(uid, etag, {**VALID_SCENARIO, "acronym": "SECOND"})
        second = added.data[READ_ONLY_CONTAINER]["uid"]

        self.patch_scenario(uid, first, {"label": "Only the first"}, added["ETag"])

        sibling = self.client.get(self.scenario_url(uid, second)).data
        self.assertEqual(sibling["label"], VALID_SCENARIO["label"])
        self.assertEqual(sibling["acronym"], "SECOND")

    def test_a_patch_that_breaks_the_shape_writes_nothing(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.patch_scenario(uid, sid, {"scenario_types": []}, etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(
            self.client.get(self.scenario_url(uid, sid)).data["scenario_types"],
            VALID_SCENARIO["scenario_types"],
        )

    def test_a_region_is_written_as_a_typed_node(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.patch_scenario(
            uid, sid, {"study_regions": [{"label": "Germany"}]}, etag
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(self.store.ask("ASK { ?node a %s }" % OEO.OEO_00020032.n3()))
        read = self.client.get(self.scenario_url(uid, sid)).data
        self.assertEqual(read["study_regions"][0]["label"], "Germany")

    def test_a_scenario_year_round_trips(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.patch_scenario(
            uid, sid, {"years": ["2030-01-01T00:00:00+00:00"]}, etag
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["years"]), 1)

    def test_an_unknown_key_is_refused(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.patch_scenario(uid, sid, {"labelz": "typo"}, etag)

        self.assertEqual(response.status_code, 400, response.data)

    def test_no_identifier_is_accepted_from_a_client(self):
        uid, etag = self.created()

        response = self.add_scenario(uid, etag, {**VALID_SCENARIO, "uid": "chosen"})

        self.assertEqual(response.status_code, 400, response.data)


class ScenarioGuardTest(ScenarioTestCase):
    """The bundle's version and the bundle's owner guard its parts."""

    def test_a_write_advances_the_bundle_version(self):
        uid, etag = self.created()

        response = self.add_scenario(uid, etag)

        self.assertEqual(response["ETag"], '"2"')
        self.assertEqual(self.client.get(self.detail_url(uid))["ETag"], '"2"')

    def test_a_read_carries_the_bundle_entity_tag(self):
        uid, sid, etag = self.with_one_scenario()

        read = self.client.get(self.scenario_url(uid, sid))

        self.assertEqual(read["ETag"], etag)

    def test_a_missing_precondition_is_refused(self):
        uid, _ = self.created()
        self.client.force_login(self.user)

        response = self.client.post(
            self.scenarios_url(uid),
            data=VALID_SCENARIO,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 428, response.data)

    def test_a_stale_precondition_is_refused(self):
        uid, etag = self.created()
        self.add_scenario(uid, etag)

        response = self.add_scenario(uid, etag, {**VALID_SCENARIO, "acronym": "TWO"})

        self.assertEqual(response.status_code, 412, response.data)
        self.assertEqual(self.client.get(self.scenarios_url(uid)).data["count"], 1)

    def test_a_stale_precondition_on_a_patch_is_refused(self):
        uid, sid, etag = self.with_one_scenario()
        self.patch_scenario(uid, sid, {"label": "First"}, etag)

        response = self.patch_scenario(uid, sid, {"label": "Second"}, etag)

        self.assertEqual(response.status_code, 412, response.data)
        self.assertEqual(
            self.client.get(self.scenario_url(uid, sid)).data["label"], "First"
        )

    def test_a_non_owner_is_refused(self):
        uid, etag = self.created()
        stranger = myuser.objects.create_user(
            name="someone-else", email="else@example.org", affiliation=""
        )

        response = self.add_scenario(uid, etag, as_user=stranger)

        self.assertEqual(response.status_code, 403, response.data)

    def test_an_ownerless_bundle_is_refused(self):
        uid, etag = self.created()
        ScenarioBundleAccessControl.objects.filter(bundle_id=uid).delete()

        response = self.add_scenario(uid, etag)

        self.assertEqual(response.status_code, 403, response.data)

    def test_an_unauthenticated_write_is_refused(self):
        uid, etag = self.created()
        self.client.logout()

        response = self.client.post(
            self.scenarios_url(uid),
            data=VALID_SCENARIO,
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

        self.assertIn(response.status_code, (401, 403))


class ScenarioHistoryTest(ScenarioTestCase):
    def entries(self, uid):
        return list(OEKG_Modifications.objects.filter(bundle_id=uid).order_by("id"))

    def test_adding_a_scenario_records_which_resource_it_was(self):
        uid, sid, _ = self.with_one_scenario()

        entry = self.entries(uid)[-1]

        self.assertEqual(entry.verb, CREATE)
        self.assertEqual(entry.resource_type, str(SCENARIO_CLASS))
        self.assertEqual(entry.resource_uuid, sid)

    def test_patching_a_scenario_records_it_too(self):
        uid, sid, etag = self.with_one_scenario()

        self.patch_scenario(uid, sid, {"label": "Renamed"}, etag)

        entry = self.entries(uid)[-1]
        self.assertEqual(entry.verb, UPDATE)
        self.assertEqual(entry.resource_uuid, sid)
        self.assertEqual((entry.version_before, entry.version_after), (2, 3))

    def test_a_nested_create_is_one_entry_for_the_bundle(self):
        # One request, one entry: the diff already carries the scenarios, and
        # an entry per nested part would multiply rows for a single write.
        uid, _ = self.created({**VALID_PAYLOAD, "scenarios": [VALID_SCENARIO]})

        entries = self.entries(uid)

        self.assertEqual(len(entries), 1)
        self.assertIsNone(entries[0].resource_uuid)

    def test_the_history_shows_the_scenario_write(self):
        uid, sid, _ = self.with_one_scenario()

        results = self.client.get(
            reverse("api:scenario-bundle-history", kwargs={"uid": uid})
        ).data["results"]

        self.assertEqual(results[0]["resource"]["uid"], sid)
        self.assertEqual(results[0]["resource"]["type"], str(SCENARIO_CLASS))


class ScenarioShapeTest(ScenarioTestCase):
    def test_the_bundle_and_its_scenarios_validate_as_one_post_state(self):
        # A scenario alone is not a unit the shape can judge -- every
        # constraint in it is bundle-local.
        uid, etag = self.created()

        response = self.add_scenario(uid, etag)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(
            self.store.ask(
                "ASK { %s <%s> ?node . ?node a %s }"
                % (
                    bundle_iri(uid).n3(),
                    "http://purl.obolibrary.org/obo/BFO_0000051",
                    SCENARIO_CLASS.n3(),
                )
            )
        )

    def test_a_pick_outside_the_shapes_list_is_refused(self):
        uid, etag = self.created()

        response = self.add_scenario(
            uid, etag, {**VALID_SCENARIO, "scenario_types": [str(OEO.OEO_99999999)]}
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("scenario_types", response.data)


class ScenarioShapeConformanceTest(RequiresShapeArtifactsMixin, SimpleTestCase):
    """Every property the shape validates on a scenario is accounted for.

    The anti-drift property a generator would have given, without the
    generator: if the shape gains a property, this fails rather than the API
    quietly ignoring it.
    """

    # Two predicates the shape validates that this slice deliberately does not
    # build: dataset links are the next slice's resource, with their own URLs.
    # Named here rather than silently passed over, so that slice deletes this
    # list instead of discovering the gap.
    DEFERRED = {
        str(OEO.OEO_00020437),  # has information input -> input dataset
        str(OEO.OEO_00020436),  # has information output -> output dataset
    }

    def test_every_scenario_property_in_the_shape_is_covered(self):
        shape = shape_graph()
        node = shape.value(predicate=SH.targetClass, object=SCENARIO_CLASS)
        paths = {
            str(shape.value(constraint, SH.path))
            for constraint in shape.objects(node, SH.property)
            if shape.value(constraint, SH.path) is not None
        }

        covered = {str(field.predicate) for field in SCENARIO_FIELDS}
        # The uuid is the server's to mint, so it is an identity rather than a
        # field -- covered by the builder, absent from the serializer.
        covered.add(str(HAS_UUID))

        self.assertTrue(paths, "the shape declares no scenario properties")
        self.assertEqual(paths - covered - self.DEFERRED, set())
        self.assertEqual(covered - paths, set())

    def test_the_serializer_and_the_builder_agree(self):
        serializer_fields = set(ScenarioSerializer().fields)
        builder_fields = {field.name for field in SCENARIO_FIELDS}

        self.assertEqual(serializer_fields, builder_fields)

    def test_a_client_cannot_supply_the_identifier(self):
        # The uuid is in the shape and therefore in the builder, but it must
        # never be in the serializer: no client supplies an identifier here.
        self.assertNotIn("uid", ScenarioSerializer().fields)
        self.assertNotIn("uuid", ScenarioSerializer().fields)
