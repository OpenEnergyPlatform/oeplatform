"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse
from rdflib import RDF, RDFS, Graph, Literal
from rdflib.namespace import SH

from factsheet.models import ScenarioBundleAccessControl
from login.models import myuser
from oekg.bundles import (
    BUNDLE_CLASS,
    BUNDLE_FIELDS,
    DC,
    ENUM,
    LITERAL,
    NODE,
    OEO,
    PART,
    build_bundle_graph,
    bundle_iri,
    bundle_payload,
)
from oekg.graph_store import GraphStore
from oekg.serializers import READ_ONLY_CONTAINER, ScenarioBundleSerializer
from oekg.shape import enumeration, shape_graph
from oekg.tests import OekgGraphAPITestCase, RequiresShapeArtifactsMixin

# Real picks from the shape's own sh:in lists -- the four the shape requires.
VALID_PAYLOAD = {
    "label": "A scenario bundle written by the API",
    "acronym": "API-TEST",
    "abstract": "Created by the test suite.",
    "descriptors": [str(OEO.OEO_00000143)],
    "sector_divisions": [str(OEO.OEO_00000368)],
    "sectors": [str(OEO.OEO_00000367)],
    "technologies": [str(OEO.OEO_00000407)],
}


class BundleApiTestCase(OekgGraphAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = myuser.objects.create_user(
            name="bundle-author", email="author@example.org", affiliation=""
        )
        self.collection_url = reverse("api:scenario-bundles")

    def create(self, payload=None, authenticate=True):
        if authenticate:
            self.client.force_login(self.user)
        return self.client.post(
            self.collection_url,
            data=payload if payload is not None else VALID_PAYLOAD,
            content_type="application/json",
        )

    def detail_url(self, uid):
        return reverse("api:scenario-bundle", kwargs={"uid": uid})


class CreateBundleTest(BundleApiTestCase):
    def test_a_bundle_is_created_and_reads_back(self):
        response = self.create()

        self.assertEqual(response.status_code, 201, response.data)
        uid = response.data[READ_ONLY_CONTAINER]["uid"]

        read = self.client.get(self.detail_url(uid))
        self.assertEqual(read.status_code, 200)
        self.assertEqual(read.data["label"], VALID_PAYLOAD["label"])
        self.assertEqual(read.data["acronym"], VALID_PAYLOAD["acronym"])
        self.assertEqual(read.data["technologies"], VALID_PAYLOAD["technologies"])

    def test_the_response_names_where_the_bundle_now_lives(self):
        response = self.create()

        uid = response.data[READ_ONLY_CONTAINER]["uid"]
        self.assertEqual(response["Location"], self.detail_url(uid))

    def test_the_server_mints_the_identifier(self):
        # A client that picks its own identifier can overwrite a stranger's
        # bundle by guessing. There is no key to supply one through.
        response = self.create({**VALID_PAYLOAD, "uid": "chosen-by-the-client"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("uid", response.data)

    def test_two_bundles_get_different_identifiers(self):
        first = self.create()
        second = self.create({**VALID_PAYLOAD, "acronym": "API-TEST-2"})

        self.assertNotEqual(
            first.data[READ_ONLY_CONTAINER]["uid"],
            second.data[READ_ONLY_CONTAINER]["uid"],
        )

    def test_the_creator_owns_the_bundle(self):
        # Without this the bundle is ownerless, which means administrator-only
        # -- so the person who created it could never edit it.
        response = self.create()

        uid = response.data[READ_ONLY_CONTAINER]["uid"]
        self.assertTrue(ScenarioBundleAccessControl.user_has_access(self.user, uid))

    def test_an_unauthenticated_write_is_refused(self):
        response = self.create(authenticate=False)

        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(self.store.ask("ASK { ?s ?p ?o }"))

    def test_a_read_needs_no_authentication(self):
        uid = self.create().data[READ_ONLY_CONTAINER]["uid"]
        self.client.logout()

        self.assertEqual(self.client.get(self.detail_url(uid)).status_code, 200)

    def test_an_unknown_bundle_is_a_404(self):
        response = self.client.get(self.detail_url("does-not-exist"))

        self.assertEqual(response.status_code, 404)

    def test_an_identifier_that_is_not_iri_safe_is_a_404(self):
        # Not a 500: these characters make rdflib refuse to build the IRI, and
        # that refusal is also what keeps the query free of injection.
        for uid in ["a b", "a<b", 'a"b', "a|b", "a^b"]:
            with self.subTest(uid=uid):
                response = self.client.get(f"/api/v0/scenario-bundles/{uid}/")
                self.assertEqual(response.status_code, 404)

    def test_an_iri_that_is_not_a_bundle_is_a_404(self):
        # Minting puts other nodes in the same namespace. Reading one of those
        # as though it were a bundle would answer 200 with an empty payload.
        uid = self.create({**VALID_PAYLOAD, "contacts": [{"label": "A contact"}]}).data[
            READ_ONLY_CONTAINER
        ]["uid"]
        contact_iri = self.client.get(self.detail_url(uid)).data["contacts"][0]["iri"]
        contact_uid = contact_iri.rsplit("/", 1)[-1]

        response = self.client.get(self.detail_url(contact_uid))

        self.assertEqual(response.status_code, 404)


class AcronymUniquenessTest(BundleApiTestCase):
    def test_a_duplicate_acronym_is_refused(self):
        self.create()

        response = self.create()

        self.assertEqual(response.status_code, 409)

    def test_an_acronym_the_old_check_would_miss_is_still_caught(self):
        # The user interface compares a normalised acronym against the raw
        # stored value, so anything with a space, hyphen, umlaut, slash, colon
        # or parenthesis slips through. Each of these is one of those.
        for acronym in ["Wind Study", "wind-study", "Wärme", "a/b", "x:y", "p(q)"]:
            with self.subTest(acronym=acronym):
                first = self.create({**VALID_PAYLOAD, "acronym": acronym})
                self.assertEqual(first.status_code, 201, first.data)

                second = self.create({**VALID_PAYLOAD, "acronym": acronym})
                self.assertEqual(second.status_code, 409, second.data)

    def test_an_acronym_is_checked_and_stored_as_the_same_value(self):
        # Checking a stripped value and storing an unstripped one is how a
        # duplicate slips through.
        first = self.create({**VALID_PAYLOAD, "acronym": "SPACED "})
        self.assertEqual(first.status_code, 201, first.data)

        second = self.create({**VALID_PAYLOAD, "acronym": "SPACED"})

        self.assertEqual(second.status_code, 409, second.data)

    def test_a_refused_duplicate_writes_nothing(self):
        self.create()
        before = len(self.store.construct("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"))

        self.create()

        after = self.store.construct("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")
        self.assertEqual(len(after), before)


class SharedNodeTest(BundleApiTestCase):
    """A shared contact or organisation is referenced, never rewritten."""

    def existing_contact(self):
        uid = self.create(
            {**VALID_PAYLOAD, "contacts": [{"label": "Institute of Things"}]}
        ).data[READ_ONLY_CONTAINER]["uid"]
        read = self.client.get(self.detail_url(uid)).data
        return read["contacts"][0]["iri"]

    def test_referencing_an_existing_node_writes_no_second_label(self):
        iri = self.existing_contact()

        response = self.create(
            {
                **VALID_PAYLOAD,
                "acronym": "API-TEST-2",
                "contacts": [{"iri": iri, "label": "Institute of Things"}],
            }
        )

        self.assertEqual(response.status_code, 201, response.data)
        labels = self.store.select(
            "SELECT ?l WHERE { <%s> <http://www.w3.org/2000/01/rdf-schema#label> ?l }"
            % iri
        )
        self.assertEqual(len(labels), 1, labels)

    def test_renaming_a_shared_node_is_refused(self):
        # A shared node is cited by other bundles, so one payload rewriting its
        # label would change every one of them.
        iri = self.existing_contact()

        response = self.create(
            {
                **VALID_PAYLOAD,
                "acronym": "API-TEST-2",
                "contacts": [{"iri": iri, "label": "A different name"}],
            }
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data["conflicts"][0]["iri"], iri)


class ShapeValidationTest(BundleApiTestCase):
    def test_a_payload_the_shape_rejects_writes_nothing(self):
        # No technologies: the shape requires at least one.
        payload = {key: v for key, v in VALID_PAYLOAD.items() if key != "technologies"}

        response = self.create(payload)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.store.ask("ASK { ?s ?p ?o }"))

    def test_the_rejection_carries_the_shapes_own_words(self):
        payload = {key: v for key, v in VALID_PAYLOAD.items() if key != "technologies"}

        response = self.create(payload)

        messages = [v["message"] for v in response.data["violations"]]
        self.assertIn(
            "Study target: This should cover at least one technology.", messages
        )

    def test_an_unknown_key_is_refused(self):
        response = self.create({**VALID_PAYLOAD, "sectorz": ["typo"]})

        self.assertEqual(response.status_code, 400)
        self.assertIn("sectorz", response.data)

    def test_a_pick_outside_the_shapes_list_is_refused(self):
        response = self.create(
            {**VALID_PAYLOAD, "technologies": [str(OEO.OEO_99999999)]}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("technologies", response.data)

    def test_minted_nodes_are_typed(self):
        # The shape's sh:class constraints require it and the user interface
        # does not do it, so the live graph carries violations it produced.
        response = self.create(
            {
                **VALID_PAYLOAD,
                "contacts": [{"label": "A contact"}],
                "organisations": [{"label": "An institute"}],
                "funders": [{"label": "A funder"}],
            }
        )

        self.assertEqual(response.status_code, 201, response.data)
        for node_class in [OEO.OEO_00000107, OEO.OEO_00030022, OEO.OEO_00090001]:
            with self.subTest(node_class=node_class):
                self.assertTrue(self.store.ask("ASK { ?node a %s }" % node_class.n3()))


class RoundTripTest(BundleApiTestCase):
    def test_a_read_can_be_sent_back_unchanged(self):
        # The property replace will depend on: what a read returns is what a
        # write accepts, including the read-only container, which writes ignore.
        uid = self.create().data[READ_ONLY_CONTAINER]["uid"]
        read = self.client.get(self.detail_url(uid)).data

        sent_back = self.client.post(
            self.collection_url,
            data={**read, "acronym": "API-TEST-COPY"},
            content_type="application/json",
        )

        self.assertEqual(sent_back.status_code, 201, sent_back.data)

    def test_a_bundle_with_every_optional_absent_round_trips(self):
        # The round trip is the property replace will depend on, and it breaks
        # on nulls: an absent abstract reads back as null, and a framework
        # without an iri carries null too.
        minimal = {key: v for key, v in VALID_PAYLOAD.items() if key != "abstract"}
        minimal["frameworks"] = [{"label": "A framework with no page"}]
        uid = self.create(minimal).data[READ_ONLY_CONTAINER]["uid"]

        read = self.client.get(self.detail_url(uid)).data
        self.assertIsNone(read["abstract"])
        self.assertIsNone(read["frameworks"][0]["iri"])

        sent_back = self.client.post(
            self.collection_url,
            data={**read, "acronym": "API-TEST-MINIMAL"},
            content_type="application/json",
        )
        self.assertEqual(sent_back.status_code, 201, sent_back.data)

    def test_reading_twice_gives_the_same_answer(self):
        uid = self.create().data[READ_ONLY_CONTAINER]["uid"]

        first = self.client.get(self.detail_url(uid)).data
        second = self.client.get(self.detail_url(uid)).data

        self.assertEqual(first, second)


class OneWriteTest(BundleApiTestCase):
    def test_creating_a_bundle_is_one_request_to_the_store(self):
        # The whole write path rests on this. Today's user interface writes one
        # committed request per triple, which is why a bundle create costs ~200
        # requests and can leave half a bundle behind.
        real_update = GraphStore.update
        updates = []

        def counting_update(store, *operations):
            updates.append(operations)
            return real_update(store, *operations)

        with patch.object(GraphStore, "update", counting_update):
            response = self.create()

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(updates), 1, updates)


class ShapeConformanceTest(RequiresShapeArtifactsMixin, SimpleTestCase):
    """Every property the shape validates on a bundle has a serializer field.

    This is the anti-drift property a generator would have given, without the
    generator: if the shape gains a property, this fails rather than the API
    quietly ignoring it.
    """

    def test_every_bundle_property_in_the_shape_has_a_field(self):
        shape = shape_graph()
        bundle_shape = shape.value(predicate=SH.targetClass, object=BUNDLE_CLASS)
        paths = {
            str(shape.value(constraint, SH.path))
            for constraint in shape.objects(bundle_shape, SH.property)
            if shape.value(constraint, SH.path) is not None
        }

        covered = {str(field.predicate) for field in BUNDLE_FIELDS}
        self.assertTrue(paths, "the shape declares no bundle properties")
        self.assertEqual(
            paths - covered,
            set(),
            "the shape validates properties the serializer has no field for",
        )
        self.assertEqual(
            covered - paths,
            set(),
            "the serializer has fields the shape does not validate",
        )

    def test_every_serializer_field_is_a_field_the_builder_knows(self):
        serializer_fields = set(ScenarioBundleSerializer().fields)
        builder_fields = {field.name for field in BUNDLE_FIELDS}

        self.assertEqual(serializer_fields, builder_fields)

    def test_every_enumerated_field_reads_its_values_from_the_shape(self):
        for field in BUNDLE_FIELDS:
            if field.kind == ENUM:
                with self.subTest(field=field.name):
                    self.assertTrue(enumeration(str(field.predicate)))


class BundleGraphTest(RequiresShapeArtifactsMixin, SimpleTestCase):
    """The builder, without a store."""

    def test_a_field_absent_from_the_payload_writes_nothing(self):
        graph = build_bundle_graph("u1", {"label": "Only a label"})

        self.assertIsNone(graph.value(bundle_iri("u1"), DC.acronym))

    def test_the_bundle_is_typed(self):
        graph = build_bundle_graph("u1", {"label": "L"})

        self.assertIn((bundle_iri("u1"), RDF.type, BUNDLE_CLASS), graph)

    def test_every_field_kind_round_trips(self):
        payload = {
            **VALID_PAYLOAD,
            "contacts": [{"label": "A contact"}],
            "frameworks": [{"label": "A framework", "iri": "https://example.org/f"}],
            "models": [{"label": "A model", "iri": "https://example.org/m"}],
        }
        graph = build_bundle_graph("u1", payload)

        read_back = bundle_payload(graph, "u1")

        self.assertEqual(read_back["label"], payload["label"])
        self.assertEqual(read_back["sectors"], payload["sectors"])
        self.assertEqual(read_back["contacts"][0]["label"], "A contact")
        self.assertEqual(read_back["frameworks"][0]["iri"], "https://example.org/f")
        self.assertEqual(read_back["models"][0]["label"], "A model")

    def test_frameworks_and_models_do_not_bleed_into_each_other(self):
        # They share the has-part predicate; only their type tells them apart.
        graph = build_bundle_graph(
            "u1",
            {
                "label": "L",
                "frameworks": [{"label": "F"}],
                "models": [{"label": "M"}],
            },
        )

        read_back = bundle_payload(graph, "u1")

        self.assertEqual([f["label"] for f in read_back["frameworks"]], ["F"])
        self.assertEqual([m["label"] for m in read_back["models"]], ["M"])


class FieldTableTest(RequiresShapeArtifactsMixin, SimpleTestCase):
    def test_the_field_kinds_are_the_ones_the_builder_handles(self):
        self.assertEqual(
            {field.kind for field in BUNDLE_FIELDS},
            {LITERAL, ENUM, NODE, PART},
        )

    def test_node_and_part_fields_declare_the_class_they_type(self):
        for field in BUNDLE_FIELDS:
            if field.kind in (NODE, PART):
                with self.subTest(field=field.name):
                    self.assertIsNotNone(field.node_class)
                    self.assertTrue(field.mint_segment)


class LabelsAreWrittenTest(RequiresShapeArtifactsMixin, SimpleTestCase):
    def test_a_minted_node_carries_exactly_one_plain_label(self):
        graph = build_bundle_graph(
            "u1", {"label": "L", "contacts": [{"label": "A contact"}]}
        )

        contact = next(graph.objects(bundle_iri("u1"), OEO.OEO_00000508))
        labels = list(graph.objects(contact, RDFS.label))
        self.assertEqual(labels, [Literal("A contact")])
        self.assertIsNone(labels[0].language)


class GraphIsNotTouchedByReadsTest(RequiresShapeArtifactsMixin, SimpleTestCase):
    def test_building_a_graph_touches_no_store(self):
        # The builder is pure: it is what makes validate-before-write possible.
        graph = build_bundle_graph("u1", VALID_PAYLOAD)

        self.assertIsInstance(graph, Graph)
        self.assertGreater(len(graph), 0)
