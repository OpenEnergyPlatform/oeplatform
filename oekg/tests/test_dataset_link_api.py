"""Dataset links: a scenario's input and output data, added and removed only.

**Which "dataset" this is.** The OEKG input/output dataset -- a node on a
scenario factsheet saying the scenario consumed or produced data. What it
points at is an OEP Table or an OEP Dataset, and which of the two is the
client's choice: `ref: table` is the reproducible reference, `ref: dataset` the
current one.

Three properties carry this slice:

- **The predicates are the ones the shape validates.** The existing
  manage-datasets route links by different ones and writes no identifier, so
  nothing it writes is reached by the shape -- it is superseded here, not
  extended.
- **There is no `PATCH`.** Every triple is derived from type, ref and name, so
  there is no field to change without changing what the link is.
- **A link is never checked against its target.** A bundle is a published
  record, so a link may outlive the table it cites, and a table's owner is
  never blocked by somebody else's citation.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import SimpleTestCase
from django.urls import reverse
from rdflib.namespace import SH

from factsheet.models import OEKG_Modifications
from login.models import myuser
from oekg.bundles import SCENARIO_CLASS
from oekg.dataset_links import DIRECTION_BY_NAME, reference_kind
from oekg.fields import HAS_IRI, HAS_UUID, OEO
from oekg.history import CREATE
from oekg.serializers import READ_ONLY_CONTAINER, DatasetLinkSerializer
from oekg.shape import shape_graph
from oekg.tests import RequiresShapeArtifactsMixin
from oekg.tests.test_scenario_api import ScenarioTestCase

INPUT_CLASS = DIRECTION_BY_NAME["input"].node_class
OUTPUT_CLASS = DIRECTION_BY_NAME["output"].node_class

TABLE_LINK = {"type": "input", "ref": "table", "name": "abbb_emob"}
DATASET_LINK = {"type": "output", "ref": "dataset", "name": "my_dataset"}


class DatasetLinkTestCase(ScenarioTestCase):
    def links_url(self, uid, sid):
        return reverse(
            "api:scenario-bundle-dataset-links", kwargs={"uid": uid, "sid": sid}
        )

    def link_url(self, uid, sid, did):
        return reverse(
            "api:scenario-bundle-dataset-link",
            kwargs={"uid": uid, "sid": sid, "did": did},
        )

    def add_link(self, uid, sid, etag, payload=None, as_user=None):
        self.client.force_login(as_user or self.user)
        return self.client.post(
            self.links_url(uid, sid),
            data=payload if payload is not None else TABLE_LINK,
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

    def with_one_link(self, payload=None):
        """A bundle, a scenario and one dataset link on it."""
        uid, sid, etag = self.with_one_scenario()
        response = self.add_link(uid, sid, etag, payload)
        self.assertEqual(response.status_code, 201, response.data)
        return uid, sid, response.data[READ_ONLY_CONTAINER]["uid"], response["ETag"]


class DatasetLinkWriteTest(DatasetLinkTestCase):
    def test_a_table_link_is_added(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.add_link(uid, sid, etag)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["type"], "input")
        self.assertEqual(response.data["ref"], "table")
        self.assertEqual(response.data["name"], "abbb_emob")

    def test_a_dataset_link_is_added(self):
        # The coarser reference: one catalogue entry instead of seventeen
        # tables. Both kinds are allowed and the representation says which.
        uid, sid, etag = self.with_one_scenario()

        response = self.add_link(uid, sid, etag, DATASET_LINK)

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["ref"], "dataset")
        self.assertEqual(response.data["type"], "output")

    def test_a_link_hangs_off_its_scenario_by_the_predicate_the_shape_validates(self):
        uid, sid, _, _ = self.with_one_link()

        self.assertTrue(
            self.store.ask(
                "ASK { ?scenario a %s ; %s ?link . ?link a %s }"
                % (
                    SCENARIO_CLASS.n3(),
                    DIRECTION_BY_NAME["input"].predicate.n3(),
                    INPUT_CLASS.n3(),
                )
            )
        )

    def test_an_output_link_uses_the_output_predicate_and_class(self):
        self.with_one_link(DATASET_LINK)

        self.assertTrue(
            self.store.ask(
                "ASK { ?scenario %s ?link . ?link a %s }"
                % (DIRECTION_BY_NAME["output"].predicate.n3(), OUTPUT_CLASS.n3())
            )
        )

    def test_the_link_carries_the_identifier_the_shape_requires(self):
        # The existing route writes none, which is why anything it wrote could
        # not be addressed -- or validated.
        _, _, did, _ = self.with_one_link()

        self.assertTrue(
            self.store.ask("ASK { ?link %s %s }" % (HAS_UUID.n3(), f'"{did}"'))
        )

    def test_the_link_stores_the_platform_url_as_a_string(self):
        # has-iri is typed xsd:string by the shape: it points at a page, it is
        # not the node's identity.
        self.with_one_link()

        rows = self.store.select("SELECT ?iri WHERE { ?link %s ?iri }" % HAS_IRI.n3())
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["iri"].endswith("/database/tables/abbb_emob"))

    def test_the_name_is_stored_as_the_label(self):
        self.with_one_link()

        self.assertTrue(
            self.store.ask(
                "ASK { ?link a %s ; <http://www.w3.org/2000/01/rdf-schema#label> "
                '"abbb_emob" }' % INPUT_CLASS.n3()
            )
        )

    def test_a_link_to_a_table_that_does_not_exist_is_still_written(self):
        # Never blocked and never checked: a bundle is a published record, and
        # blocking would let one user make a stranger's table undeletable.
        uid, sid, etag = self.with_one_scenario()

        response = self.add_link(
            uid, sid, etag, {**TABLE_LINK, "name": "no_such_table_anywhere"}
        )

        self.assertEqual(response.status_code, 201, response.data)

    def test_a_name_that_cannot_be_part_of_a_url_is_refused(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.add_link(uid, sid, etag, {**TABLE_LINK, "name": "not a table"})

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("not a possible OEP table name", response.data["detail"])

    def test_an_unknown_reference_kind_is_refused(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.add_link(uid, sid, etag, {**TABLE_LINK, "ref": "databus"})

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("ref", response.data)

    def test_an_unknown_key_is_refused(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.add_link(uid, sid, etag, {**TABLE_LINK, "key": 12})

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("key", response.data)

    def test_the_same_link_twice_is_refused(self):
        # Two nodes saying one thing, with no way to tell which a later delete
        # took. Refused rather than silently skipped.
        uid, sid, _, etag = self.with_one_link()

        again = self.add_link(uid, sid, etag)

        self.assertEqual(again.status_code, 409, again.data)

    def test_the_same_table_as_input_and_as_output_is_allowed(self):
        uid, sid, _, etag = self.with_one_link()

        response = self.add_link(uid, sid, etag, {**TABLE_LINK, "type": "output"})

        self.assertEqual(response.status_code, 201, response.data)

    def test_a_stranger_cannot_add_a_link(self):
        uid, sid, etag = self.with_one_scenario()
        stranger = myuser.objects.create_user(
            name="stranger", email="stranger@example.org", affiliation=""
        )

        response = self.add_link(uid, sid, etag, as_user=stranger)

        self.assertEqual(response.status_code, 403, response.data)

    def test_a_stale_precondition_is_refused(self):
        uid, sid, etag = self.with_one_scenario()
        self.add_link(uid, sid, etag)

        again = self.add_link(uid, sid, etag, DATASET_LINK)

        self.assertEqual(again.status_code, 412, again.data)

    def test_a_link_on_a_scenario_that_is_not_there_says_so(self):
        uid, etag = self.created()

        response = self.add_link(uid, "no-such-scenario", etag)

        self.assertEqual(response.status_code, 404, response.data)


class DatasetLinkReadTest(DatasetLinkTestCase):
    def test_one_link_reads_back_the_three_keys_a_write_accepts(self):
        uid, sid, did, _ = self.with_one_link()

        read = self.client.get(self.link_url(uid, sid, did)).data

        self.assertEqual(
            {key: read[key] for key in ("type", "ref", "name")}, TABLE_LINK
        )

    def test_the_collection_lists_a_scenarios_links(self):
        uid, sid, _, etag = self.with_one_link()
        self.add_link(uid, sid, etag, DATASET_LINK)

        listed = self.client.get(self.links_url(uid, sid)).data

        self.assertEqual(listed["count"], 2)
        self.assertEqual(
            [(row["type"], row["name"]) for row in listed["results"]],
            [("input", "abbb_emob"), ("output", "my_dataset")],
        )

    def test_a_read_is_public(self):
        uid, sid, did, _ = self.with_one_link()
        self.client.logout()

        self.assertEqual(self.client.get(self.link_url(uid, sid, did)).status_code, 200)

    def test_the_read_carries_the_bundles_entity_tag(self):
        uid, sid, did, etag = self.with_one_link()

        response = self.client.get(self.link_url(uid, sid, did))

        self.assertEqual(response["ETag"], etag)

    def test_reading_a_link_that_is_not_there_says_so(self):
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(self.link_url(uid, sid, "no-such-link"))

        self.assertEqual(response.status_code, 404)
        self.assertIn("dataset link", response.data["detail"])


class DatasetLinkHasNoPatchTest(DatasetLinkTestCase):
    def test_a_dataset_link_cannot_be_patched(self):
        # Not an omission: every field is derived from type, ref and name, so
        # there is nothing to change that does not make it a different link.
        uid, sid, did, etag = self.with_one_link()
        self.client.force_login(self.user)

        response = self.client.patch(
            self.link_url(uid, sid, did),
            data={"name": "another_table"},
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

        self.assertEqual(response.status_code, 405, response.data)

    def test_the_collection_offers_no_patch_either(self):
        uid, sid, _ = self.with_one_scenario()
        self.client.force_login(self.user)

        response = self.client.patch(
            self.links_url(uid, sid),
            data={"name": "another_table"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 405, response.data)


class DatasetLinkHistoryTest(DatasetLinkTestCase):
    def test_adding_a_link_records_a_create_naming_the_link(self):
        uid, _, did, _ = self.with_one_link()

        entry = OEKG_Modifications.objects.filter(resource_uuid=did).get()

        self.assertEqual(entry.verb, CREATE)
        self.assertEqual(entry.resource_type, str(INPUT_CLASS))
        self.assertEqual(entry.bundle_id, uid)

    def test_the_history_reads_the_link_back(self):
        uid, _, did, _ = self.with_one_link()

        results = self.client.get(
            reverse("api:scenario-bundle-history", kwargs={"uid": uid})
        ).data["results"]

        self.assertEqual(results[0]["resource"]["uid"], did)


class ReferenceKindTest(SimpleTestCase):
    """`ref` is read back out of the stored URL, because the shape has no field
    for it -- and the platform's own routes decide what those URLs look like."""

    def test_a_table_url_reads_back_as_a_table_reference(self):
        self.assertEqual(
            reference_kind("https://openenergyplatform.org/database/tables/abc"),
            "table",
        )

    def test_a_dataset_url_reads_back_as_a_dataset_reference(self):
        self.assertEqual(
            reference_kind("https://openenergyplatform.org/database/datasets/abc"),
            "dataset",
        )

    def test_a_link_pointing_somewhere_else_reports_no_kind(self):
        # Honest rather than guessed: links written before these routes existed
        # point at neither, and saying "table" would be a fabrication.
        self.assertIsNone(reference_kind("https://databus.example.org/x/y"))


class DatasetLinkShapeConformanceTest(RequiresShapeArtifactsMixin, SimpleTestCase):
    """Every property the shape validates on a dataset link is accounted for.

    Its shape targets the objects of the two link predicates rather than a
    class, so the lookup starts from those rather than from `sh:targetClass`.
    """

    #: has-id. Allowed by the shape and deliberately never written: it would be
    #: a copy of a database key that nothing keeps in step, and a link resolves
    #: by name on read instead.
    NOT_WRITTEN = {"https://openenergyplatform.org/ontology/oekg/has_id"}

    def dataset_shape_paths(self):
        shape = shape_graph()
        node = shape.value(
            predicate=SH.targetObjectsOf, object=DIRECTION_BY_NAME["input"].predicate
        )
        return {
            str(shape.value(constraint, SH.path))
            for constraint in shape.objects(node, SH.property)
            if shape.value(constraint, SH.path) is not None
        }

    def test_every_dataset_property_in_the_shape_is_covered(self):
        paths = self.dataset_shape_paths()
        written = {
            "http://www.w3.org/2000/01/rdf-schema#label",
            str(HAS_IRI),
            str(HAS_UUID),
        }

        self.assertTrue(paths, "the shape declares no dataset properties")
        self.assertEqual(paths - written - self.NOT_WRITTEN, set())
        self.assertEqual(written - paths, set())

    def test_the_serializer_offers_only_the_three_derived_keys(self):
        self.assertEqual(set(DatasetLinkSerializer().fields), {"type", "ref", "name"})

    def test_a_client_cannot_supply_the_identifier(self):
        self.assertNotIn("uid", DatasetLinkSerializer().fields)
        self.assertNotIn("uuid", DatasetLinkSerializer().fields)


class ScenarioReadDepthTest(DatasetLinkTestCase):
    def test_a_link_is_inside_the_post_state_the_shape_is_asked_about(self):
        # A link is two hops from the bundle and its own triples are the third,
        # so the pruner has to reach it -- otherwise the shape would never see
        # a link at all and DatasetShape would be dead weight.
        from oekg.bundles import bundle_subgraph
        from oekg.graph_store import GraphStore
        from oekg.reads import read_bundle

        uid, _, _, _ = self.with_one_link()

        pruned = bundle_subgraph(read_bundle(GraphStore.from_settings(), uid), uid)

        self.assertTrue(
            (None, HAS_IRI, None) in pruned and (None, OEO.OEO_00020437, None) in pruned
        )
