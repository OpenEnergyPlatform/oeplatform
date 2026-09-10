"""Changing one field of a scenario bundle, guarded by version.

The three refusals are three different statuses on purpose, because they mean
three different things to the client:

- **428** you did not say which version you were editing;
- **412** you said a version, and it is not the current one;
- **409** the server's own guard fired -- the bundle moved between the read the
  validation needed and the write. Re-read, re-apply, retry.

The 409 window cannot be opened from a test client alone, so the tests that
exercise it interleave a competing write inside the transport itself. That is
the only way to reach the race the guard exists for.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest.mock import patch

from django.test import SimpleTestCase
from rdflib import RDF, Literal

from factsheet.models import ScenarioBundleAccessControl
from login.models import myuser
from oekg.bundles import (
    BUNDLE_CLASS,
    DC,
    HAS_PART,
    OEO,
    build_bundle_graph,
    bundle_field,
    bundle_iri,
    field_triples,
    linked_field_triples,
)
from oekg.graph_store import GraphStore
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.bundle_fixtures import VALID_PAYLOAD, BundleApiTestCase
from oekg.versioning import (
    UNVERSIONED,
    VERSION,
    VERSION_OF,
    guarded_operation,
    mint_write_token,
    read_version,
    version_iri,
    version_triples,
)


class VersionTest(BundleApiTestCase):
    def test_a_created_bundle_is_at_version_one(self):
        response = self.create()

        self.assertEqual(response["ETag"], '"1"')
        self.assertEqual(response.data[READ_ONLY_CONTAINER]["version"], 1)

    def test_a_read_carries_the_version_as_an_entity_tag(self):
        uid, etag = self.created()

        read = self.client.get(self.detail_url(uid))

        self.assertEqual(read["ETag"], etag)
        self.assertEqual(read.data[READ_ONLY_CONTAINER]["version"], 1)

    def test_a_patch_advances_the_version(self):
        uid, etag = self.created()

        response = self.patch(uid, {"label": "Renamed"}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response["ETag"], '"2"')
        self.assertEqual(self.client.get(self.detail_url(uid))["ETag"], '"2"')

    def test_the_version_triple_points_at_the_bundle(self):
        # The bundle shape is sh:closed, so a version hung off the bundle would
        # make every bundle this API writes invalid. The direction is what makes
        # the guard expressible without editing the shape.
        uid, _ = self.created()

        self.assertTrue(
            self.store.ask(
                "ASK { %s %s %s }"
                % (version_iri(uid).n3(), VERSION_OF.n3(), bundle_iri(uid).n3())
            )
        )

    def test_the_bundle_carries_no_version_property_of_its_own(self):
        uid, _ = self.created()

        self.assertFalse(
            self.store.ask(
                "ASK { %s ?p ?o . FILTER(?p IN (%s, %s)) }"
                % (bundle_iri(uid).n3(), VERSION.n3(), VERSION_OF.n3())
            )
        )

    def test_a_read_does_not_return_the_version_triples_as_fields(self):
        # The read walks outward from the bundle and the version node points
        # inward, so the bookkeeping stays out of the payload for free.
        uid, _ = self.created()

        read = self.client.get(self.detail_url(uid)).data

        self.assertNotIn(str(VERSION), read)
        self.assertNotIn("version", set(read) - {READ_ONLY_CONTAINER})


class UnversionedBundleTest(BundleApiTestCase):
    """Bundles written before this API exists carry no version node."""

    def existing_bundle_without_a_version(self):
        uid = "11111111-2222-3333-4444-555555555555"
        self.store.insert(build_bundle_graph(uid, VALID_PAYLOAD))
        ScenarioBundleAccessControl.objects.create(owner_user=self.user, bundle_id=uid)
        return uid

    def test_it_reads_as_version_zero(self):
        uid = self.existing_bundle_without_a_version()

        read = self.client.get(self.detail_url(uid))

        self.assertEqual(read["ETag"], '"0"')
        self.assertEqual(read.data[READ_ONLY_CONTAINER]["version"], UNVERSIONED)

    def test_the_first_write_creates_the_version_node(self):
        uid = self.existing_bundle_without_a_version()

        response = self.patch(uid, {"label": "Renamed"}, if_match='"0"')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response["ETag"], '"1"')
        self.assertEqual(read_version(self.store, uid).number, 1)

    def test_a_stale_precondition_on_an_unversioned_bundle_is_refused(self):
        uid = self.existing_bundle_without_a_version()

        response = self.patch(uid, {"label": "Renamed"}, if_match='"1"')

        self.assertEqual(response.status_code, 412, response.data)


class PatchOneFieldTest(BundleApiTestCase):
    def test_patching_one_field_leaves_the_others_intact(self):
        uid, etag = self.created()

        response = self.patch(uid, {"label": "Renamed"}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)
        read = self.client.get(self.detail_url(uid)).data
        self.assertEqual(read["label"], "Renamed")
        self.assertEqual(read["acronym"], VALID_PAYLOAD["acronym"])
        self.assertEqual(read["abstract"], VALID_PAYLOAD["abstract"])
        self.assertEqual(read["technologies"], VALID_PAYLOAD["technologies"])

    def test_the_response_is_the_bundle_as_it_now_stands(self):
        uid, etag = self.created()

        response = self.patch(uid, {"label": "Renamed"}, if_match=etag)

        self.assertEqual(response.data["label"], "Renamed")
        self.assertEqual(response.data, self.client.get(self.detail_url(uid)).data)

    def test_a_set_valued_field_is_replaced_completely(self):
        uid, etag = self.created()
        replacement = [str(OEO.OEO_00010423)]

        response = self.patch(uid, {"technologies": replacement}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            self.client.get(self.detail_url(uid)).data["technologies"], replacement
        )

    def test_an_empty_list_on_a_required_field_is_a_validation_failure(self):
        # Never a silent wipe: the shape requires at least one technology, so
        # emptying the set is a rejection rather than an accepted deletion.
        uid, etag = self.created()

        response = self.patch(uid, {"technologies": []}, if_match=etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(
            self.client.get(self.detail_url(uid)).data["technologies"],
            VALID_PAYLOAD["technologies"],
        )

    def test_an_optional_literal_can_be_cleared(self):
        uid, etag = self.created()

        response = self.patch(uid, {"abstract": None}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNone(self.client.get(self.detail_url(uid)).data["abstract"])

    def test_an_unknown_key_is_refused(self):
        uid, etag = self.created()

        response = self.patch(uid, {"labelz": "typo"}, if_match=etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("labelz", response.data)

    def test_a_patch_cannot_reach_into_a_sub_resource(self):
        # Sub-resources have their own URLs. A bundle patch that could carry
        # them would be able to drop them by omission, which is exactly the
        # power this API withholds from every verb but replace.
        uid, etag = self.created()

        response = self.patch(uid, {"scenarios": []}, if_match=etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("scenarios", response.data)

    def test_an_empty_patch_is_refused(self):
        uid, etag = self.created()

        response = self.patch(uid, {}, if_match=etag)

        self.assertEqual(response.status_code, 400, response.data)

    def test_a_patch_that_names_only_the_read_only_container_is_refused(self):
        uid, etag = self.created()

        response = self.patch(uid, {READ_ONLY_CONTAINER: {"uid": uid}}, if_match=etag)

        self.assertEqual(response.status_code, 400, response.data)

    def test_a_patch_does_not_re_mint_the_parts_it_did_not_name(self):
        # Rebuilding the whole bundle from a read would mint fresh nodes for
        # every framework and model, so an unrelated patch would churn every
        # identifier in the bundle and fill a later history with false deletes.
        uid, etag = self.created(
            {**VALID_PAYLOAD, "frameworks": [{"label": "A framework"}]}
        )
        before = self.part_nodes(uid)

        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        self.assertEqual(self.part_nodes(uid), before)
        self.assertEqual(len(before), 1)

    def test_replacing_a_part_set_unlinks_the_old_node(self):
        uid, etag = self.created(
            {**VALID_PAYLOAD, "frameworks": [{"label": "A framework"}]}
        )

        self.patch(uid, {"frameworks": [{"label": "Another"}]}, if_match=etag)

        read = self.client.get(self.detail_url(uid)).data
        self.assertEqual([f["label"] for f in read["frameworks"]], ["Another"])

    def test_patching_frameworks_leaves_models_alone(self):
        # They share the has-part predicate; only their type tells them apart,
        # so a predicate-scoped delete would take both.
        uid, etag = self.created(
            {
                **VALID_PAYLOAD,
                "frameworks": [{"label": "A framework"}],
                "models": [{"label": "A model"}],
            }
        )

        self.patch(uid, {"frameworks": [{"label": "Another"}]}, if_match=etag)

        read = self.client.get(self.detail_url(uid)).data
        self.assertEqual([m["label"] for m in read["models"]], ["A model"])
        self.assertEqual([f["label"] for f in read["frameworks"]], ["Another"])

    def test_the_patched_bundle_still_round_trips(self):
        uid, etag = self.created()
        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        read = self.client.get(self.detail_url(uid)).data
        sent_back = self.client.post(
            self.collection_url,
            data={**read, "acronym": "API-TEST-COPY"},
            content_type="application/json",
        )

        self.assertEqual(sent_back.status_code, 201, sent_back.data)

    def test_renaming_a_shared_node_through_a_patch_is_refused(self):
        first, etag = self.created({**VALID_PAYLOAD, "contacts": [{"label": "A name"}]})
        iri = self.client.get(self.detail_url(first)).data["contacts"][0]["iri"]

        response = self.patch(
            first,
            {"contacts": [{"iri": iri, "label": "A different name"}]},
            if_match='"1"',
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data["conflicts"][0]["iri"], iri)

    def test_a_patch_is_one_request_to_the_store(self):
        uid, etag = self.created()
        real_update = GraphStore.update
        updates = []

        def counting_update(store, *operations):
            updates.append(operations)
            return real_update(store, *operations)

        with patch.object(GraphStore, "update", counting_update):
            response = self.patch(uid, {"label": "Renamed"}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(updates), 1, updates)

    def part_nodes(self, uid):
        return {
            row["node"]
            for row in self.store.select(
                "SELECT ?node WHERE { %s %s ?node }"
                % (bundle_iri(uid).n3(), HAS_PART.n3())
            )
        }


class PatchAcronymTest(BundleApiTestCase):
    """What a patch does to an acronym -- including what it does NOT do.

    Uniqueness is enforced on a create and not thereafter, deliberately: the
    read side is where the acronym becomes load-bearing, because that is where
    a pipeline looks a bundle up by it, so the check belongs with the endpoint
    that makes the promise rather than being scattered across every write.

    The gap is pinned down here rather than left to be discovered. When the
    read side closes it, `test_renaming_onto_a_taken_acronym_is_currently_allowed`
    is the test that has to be turned around, and it says so.
    """

    def test_an_acronym_can_be_changed(self):
        uid, etag = self.created()

        response = self.patch(uid, {"acronym": "RENAMED"}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            self.client.get(self.detail_url(uid)).data["acronym"], "RENAMED"
        )

    def test_renaming_onto_a_taken_acronym_is_currently_allowed(self):
        # CHARACTERISATION, not an endorsement: two bundles can end up sharing
        # an acronym, and a lookup by acronym then has two answers. Deferred to
        # the read-side slice, which is the one that promises the lookup.
        # Turning this around is what closing the gap looks like.
        uid, etag = self.created()
        self.create({**VALID_PAYLOAD, "acronym": "TAKEN"})

        response = self.patch(uid, {"acronym": "TAKEN"}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            len(self.bundles_with_acronym("TAKEN")),
            2,
            "the acronym is now ambiguous -- this is the deferred gap",
        )

    def test_sending_the_acronym_back_unchanged_is_accepted(self):
        # The round trip a client and, later, replace both rely on: a bundle's
        # own acronym must not read as taken by somebody else.
        uid, etag = self.created()

        response = self.patch(uid, {"acronym": VALID_PAYLOAD["acronym"]}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)

    def test_a_create_still_refuses_a_duplicate_acronym(self):
        # The create-side guarantee is untouched by the patch-side gap, and it
        # is bound inside the write rather than checked in front of it.
        self.created()

        response = self.create({**VALID_PAYLOAD, "acronym": VALID_PAYLOAD["acronym"]})

        self.assertEqual(response.status_code, 409, response.data)

    def bundles_with_acronym(self, acronym):
        return self.store.select(
            "SELECT ?bundle WHERE { ?bundle a %s ; %s %s }"
            % (BUNDLE_CLASS.n3(), DC.acronym.n3(), Literal(acronym).n3())
        )


class PreconditionTest(BundleApiTestCase):
    def test_a_missing_precondition_is_refused(self):
        uid, _ = self.created()

        response = self.patch(uid, {"label": "Renamed"})

        self.assertEqual(response.status_code, 428, response.data)

    def test_a_stale_precondition_is_refused(self):
        uid, etag = self.created()
        self.patch(uid, {"label": "First"}, if_match=etag)

        response = self.patch(uid, {"label": "Second"}, if_match=etag)

        self.assertEqual(response.status_code, 412, response.data)
        self.assertEqual(self.client.get(self.detail_url(uid)).data["label"], "First")

    def test_a_wildcard_precondition_is_refused(self):
        # `*` would let a client satisfy the header without saying which
        # version it read, which is the whole point of requiring it.
        uid, _ = self.created()

        response = self.patch(uid, {"label": "Renamed"}, if_match="*")

        self.assertEqual(response.status_code, 428, response.data)

    def test_a_precondition_that_is_not_a_version_is_refused(self):
        uid, _ = self.created()

        for value in ['"abc"', "abc", '""', 'W/"nope"']:
            with self.subTest(if_match=value):
                response = self.patch(uid, {"label": "Renamed"}, if_match=value)
                self.assertEqual(response.status_code, 412, response.data)

    def test_an_unquoted_precondition_is_accepted(self):
        uid, _ = self.created()

        response = self.patch(uid, {"label": "Renamed"}, if_match="1")

        self.assertEqual(response.status_code, 200, response.data)

    def test_a_precondition_may_name_several_versions(self):
        uid, _ = self.created()

        response = self.patch(uid, {"label": "Renamed"}, if_match='"9", "1"')

        self.assertEqual(response.status_code, 200, response.data)

    def test_a_refused_precondition_writes_nothing(self):
        uid, etag = self.created()
        before = self.triples()

        self.patch(uid, {"label": "Renamed"}, if_match='"99"')

        self.assertEqual(self.triples(), before)

    def triples(self):
        return len(self.store.construct("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"))


class InterleavedWriteTest(BundleApiTestCase):
    """The window between the read validation needs and the guarded write."""

    def interleave(self, competitor):
        """Run ``competitor`` once, just before the view's own update lands."""
        real_update = GraphStore.update
        done = []

        def update_after_a_competitor(store, *operations):
            if not done:
                done.append(True)
                competitor(real_update)
            return real_update(store, *operations)

        return patch.object(GraphStore, "update", update_after_a_competitor)

    def someone_else_patches(self, uid, label="Theirs"):
        """A competitor that relabels the bundle, using the API's own guard."""

        def competitor(real_update):
            other = GraphStore.from_settings(graph=self.graph_name)
            real_update(other, guarded_bump(other, uid, label))

        return competitor

    def test_two_writes_against_the_same_version_cannot_both_succeed(self):
        uid, etag = self.created()

        with self.interleave(self.someone_else_patches(uid)):
            response = self.patch(uid, {"label": "Mine"}, if_match=etag)

        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(self.client.get(self.detail_url(uid)).data["label"], "Theirs")

    def test_the_losing_write_leaves_the_version_where_the_winner_put_it(self):
        uid, etag = self.created()

        with self.interleave(self.someone_else_patches(uid)):
            self.patch(uid, {"label": "Mine"}, if_match=etag)

        self.assertEqual(read_version(self.store, uid).number, 2)

    def test_a_bundle_that_vanished_mid_write_is_not_recreated(self):
        uid, etag = self.created()

        def someone_else_deletes_everything(real_update):
            other = GraphStore.from_settings(graph=self.graph_name)
            # Scoped by hand: `update` sends what it is given, so an
            # unscoped DELETE here would empty the store's default graph --
            # in production, the graph the platform serves.
            real_update(
                other,
                f"WITH <{self.graph_name}> DELETE {{ ?s ?p ?o }} " "WHERE { ?s ?p ?o }",
            )

        with self.interleave(someone_else_deletes_everything):
            response = self.patch(uid, {"label": "Mine"}, if_match=etag)

        self.assertEqual(response.status_code, 409, response.data)
        self.assertFalse(self.store.ask("ASK { ?s ?p ?o }"))

    def test_a_bundle_deleted_the_way_the_interface_deletes_is_not_resurrected(
        self,
    ):
        # The version node points AT the bundle, so the user interface's delete
        # -- `oekg.remove((bundle, None, None))`, outgoing triples only --
        # leaves it behind. On the version alone the guard would match a bundle
        # that is gone and write its fields back as untyped orphans.
        uid, etag = self.created()

        def someone_else_deletes_the_bundle(real_update):
            other = GraphStore.from_settings(graph=self.graph_name)
            real_update(
                other,
                f"WITH <{self.graph_name}> DELETE {{ {bundle_iri(uid).n3()} ?p ?o }} "
                f"WHERE {{ {bundle_iri(uid).n3()} ?p ?o }}",
            )

        with self.interleave(someone_else_deletes_the_bundle):
            response = self.patch(uid, {"label": "Mine"}, if_match=etag)

        self.assertEqual(response.status_code, 409, response.data)
        self.assertFalse(
            self.store.ask("ASK { %s ?p ?o }" % bundle_iri(uid).n3()),
            "the guarded write resurrected a bundle that had been deleted",
        )
        self.assertEqual(self.client.get(self.detail_url(uid)).status_code, 404)

    def test_two_creates_cannot_both_take_the_same_acronym(self):
        # Slice 3 checked the acronym and then inserted, which are two
        # requests: both creates passed the check and both landed. The check is
        # now bound inside the write.
        def someone_else_creates_it_first(real_update):
            other = GraphStore.from_settings(graph=self.graph_name)
            graph = build_bundle_graph(
                "aaaaaaaa-0000-0000-0000-000000000000", VALID_PAYLOAD
            )
            real_update(other, other.insert_data(graph))

        with self.interleave(someone_else_creates_it_first):
            response = self.create()

        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(len(self.bundles()), 1, self.bundles())

    def bundles(self):
        return self.store.select("SELECT ?b WHERE { ?b a %s }" % BUNDLE_CLASS.n3())


def guarded_bump(store, uid, label):
    """A competing writer, using the API's own compare-and-set."""
    return _guarded_field(store, uid, "label", label)


def _guarded_field(store, uid, name, value):
    field = bundle_field(name)
    return guarded_operation(
        store,
        uid,
        read_version(store, uid),
        mint_write_token(),
        delete=linked_field_triples(
            store.construct("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"),
            uid,
            field,
        ),
        insert=field_triples(uid, field, value),
    )


class OwnershipTest(BundleApiTestCase):
    def other_user(self, **kwargs):
        return myuser.objects.create_user(
            name=kwargs.pop("name", "someone-else"),
            email=kwargs.pop("email", "else@example.org"),
            affiliation="",
            **kwargs,
        )

    def test_an_unauthenticated_patch_is_refused(self):
        uid, etag = self.created()
        self.client.logout()

        response = self.patch(
            uid, {"label": "Renamed"}, if_match=etag, authenticate=False
        )

        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(
            self.client.get(self.detail_url(uid)).data["label"], VALID_PAYLOAD["label"]
        )

    def test_a_non_owner_is_refused(self):
        uid, etag = self.created()

        response = self.patch(
            uid, {"label": "Renamed"}, if_match=etag, as_user=self.other_user()
        )

        self.assertEqual(response.status_code, 403, response.data)

    def test_a_second_owner_may_write(self):
        # Multi-owner bundles are reachable today through the admin command, so
        # ownership is asked of the access-control model rather than compared
        # against a single creator.
        uid, etag = self.created()
        second = self.other_user()
        ScenarioBundleAccessControl.objects.create(owner_user=second, bundle_id=uid)

        response = self.patch(uid, {"label": "Renamed"}, if_match=etag, as_user=second)

        self.assertEqual(response.status_code, 200, response.data)

    def test_an_ownerless_bundle_is_refused_to_a_normal_user(self):
        uid, etag = self.created()
        ScenarioBundleAccessControl.objects.filter(bundle_id=uid).delete()

        response = self.patch(uid, {"label": "Renamed"}, if_match=etag)

        self.assertEqual(response.status_code, 403, response.data)

    def test_an_ownerless_bundle_is_writable_by_an_administrator(self):
        # Documented as intended: records of unknown provenance fail closed for
        # everyone but an administrator.
        uid, etag = self.created()
        ScenarioBundleAccessControl.objects.filter(bundle_id=uid).delete()
        admin = self.other_user(name="an-admin", email="admin@example.org")
        admin.is_admin = True
        admin.save()

        response = self.patch(uid, {"label": "Renamed"}, if_match=etag, as_user=admin)

        self.assertEqual(response.status_code, 200, response.data)

    def test_a_patch_on_an_unknown_bundle_is_a_404(self):
        response = self.patch(
            "11111111-2222-3333-4444-555555555555",
            {"label": "Renamed"},
            if_match='"1"',
        )

        self.assertEqual(response.status_code, 404, response.data)

    def test_a_patch_on_an_identifier_that_is_not_minted_is_a_404(self):
        response = self.patch("not-a-uuid", {"label": "Renamed"}, if_match='"1"')

        self.assertEqual(response.status_code, 404, response.data)


class VersioningUnitTest(SimpleTestCase):
    """The version node, without a store."""

    def test_the_version_node_is_derived_from_the_bundle(self):
        # Derived rather than looked up, so the compare-and-set can address it
        # in the same request that reads it.
        self.assertEqual(version_iri("u1"), version_iri("u1"))
        self.assertNotEqual(version_iri("u1"), version_iri("u2"))

    def test_the_version_triples_point_at_the_bundle(self):
        triples = version_triples("u1", 3)

        self.assertIn((version_iri("u1"), VERSION_OF, bundle_iri("u1")), triples)
        self.assertIsNone(triples.value(bundle_iri("u1"), VERSION))

    def test_the_version_is_an_integer_literal(self):
        value = version_triples("u1", 3).value(version_iri("u1"), VERSION)

        self.assertEqual(int(value), 3)

    def test_the_version_node_is_untyped(self):
        # Nothing in the shape targets it, and nothing should start to.
        triples = version_triples("u1", 3)

        self.assertIsNone(triples.value(version_iri("u1"), RDF.type))
