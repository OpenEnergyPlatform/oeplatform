"""Deleting one part of a bundle, bounded by type.

The danger here is not the delete, it is the walk. Today's browser delete
follows one predicate one hop, which is wrong in both directions at once: it
destroys nodes other bundles cite, and it leaves the children of what it did
remove behind as unreachable rubbish.

So these tests are written against the two halves of the bound:

- **What is deleted** is a closed list of classes, walked recursively, so a
  scenario's dataset links go with it rather than being orphaned.
- **What is unlinked** is everything else reachable -- a region, an author, a
  contact, an organisation, a funder, a framework, a model, a cited document.
  There is a test per class rather than one representative, because the
  allowlist was already wrong once while it was being drafted and a
  representative would have covered whichever classes happened to be right.

And a guard clause underneath both: a node anything outside this bundle points
at is unlinked instead of deleted, whatever its class, and the response says so.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest import mock

from django.test import SimpleTestCase
from django.urls import reverse
from rdflib import RDF, RDFS, Graph, Literal, URIRef

from factsheet.models import OEKG_Modifications, ScenarioBundleAccessControl
from login.models import myuser
from oekg.bundles import (
    BUNDLE_PARTS,
    REFERENCE_CLASS,
    SCENARIO_CLASS,
    STUDY_REPORT_CLASS,
    bundle_iri,
)
from oekg.dataset_links import DIRECTIONS
from oekg.fields import HAS_PART, OEO
from oekg.history import DELETE
from oekg.removal import BUNDLE_LOCAL_CLASSES, plan_removal
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.bundle_fixtures import VALID_PAYLOAD
from oekg.tests.test_dataset_link_api import (
    DATASET_LINK,
    TABLE_LINK,
    DatasetLinkTestCase,
)
from oekg.tests.test_scenario_api import VALID_SCENARIO
from oekg.tests.test_study_report_api import VALID_REPORT, StudyReportTestCase

# A region is a shared node: two scenarios in two bundles cite the same one, so
# it is unlinked and never deleted.
BERLIN = "https://openenergyplatform.org/ontology/oekg/region/DE-BE"
BRANDENBURG = "https://openenergyplatform.org/ontology/oekg/region/DE-BB"

SCENARIO_WITH_REGIONS = {
    **VALID_SCENARIO,
    "study_regions": [{"iri": BERLIN, "label": "Berlin"}],
    "interacting_regions": [{"iri": BRANDENBURG, "label": "Brandenburg"}],
}

REPORT_WITH_REFERENCE = {
    **VALID_REPORT,
    "reference": "https://doi.org/10.5281/zenodo.1234567",
}

# Every shared node kind a bundle itself carries, in one payload.
BUNDLE_WITH_SHARED_NODES = {
    "contacts": [{"label": "Grace Hopper"}],
    "organisations": [{"label": "Reiner Lemoine Institut"}],
    "funders": [{"label": "BMWK"}],
    "frameworks": [{"label": "PyPSA"}],
    "models": [{"label": "PyPSA-Eur"}],
}

# Identifiers of the right shape for nothing that exists.
ABSENT = "11111111-1111-1111-1111-111111111111"
ABSENT_BUNDLE = "22222222-2222-2222-2222-222222222222"


class SubResourceDeleteTestCase(DatasetLinkTestCase, StudyReportTestCase):
    """A bundle with every kind of part and every kind of shared node on it.

    Both helper classes are inherited rather than restated: what a delete needs
    is exactly what created the thing being deleted.
    """

    def delete(self, url, etag=None, as_user=None, authenticate=True):
        if authenticate:
            self.client.force_login(as_user or self.user)
        headers = {} if etag is None else {"HTTP_IF_MATCH": etag}
        return self.client.delete(url, **headers)

    def history_url(self, uid):
        return reverse("api:scenario-bundle-history", kwargs={"uid": uid})

    def node_exists(self, iri) -> bool:
        """Whether this node still says anything at all in the store."""
        return self.store.ask("ASK { %s ?p ?o }" % URIRef(str(iri)).n3())

    def linked(self, subject, predicate, obj) -> bool:
        return self.store.ask(
            "ASK { %s %s %s }"
            % (
                URIRef(str(subject)).n3(),
                URIRef(str(predicate)).n3(),
                URIRef(str(obj)).n3(),
            )
        )

    def iris(self, entries) -> set:
        return {entry["iri"] for entry in entries}

    def node_of(self, response) -> URIRef:
        return URIRef(response.data[READ_ONLY_CONTAINER]["iri"])

    def reference_from_outside(self, node) -> None:
        """Another bundle's part pointing at this node.

        On the shared case rather than on the guard tests: the whole-bundle
        delete faces the same guard one level up, and two spellings of "what
        an outside reference looks like" would let the two drift.
        """
        outside = Graph()
        outside.add(
            (URIRef("urn:oep:test:another-bundle"), HAS_PART, URIRef(str(node)))
        )
        self.store.insert(outside)

    def with_scenario_regions(self, payload=None):
        """A bundle plus one scenario citing two shared regions."""
        uid, etag = self.created(payload)
        added = self.add_scenario(uid, etag, SCENARIO_WITH_REGIONS)
        self.assertEqual(added.status_code, 201, added.data)
        return uid, added.data[READ_ONLY_CONTAINER]["uid"], added["ETag"]


class DeleteAScenarioTest(SubResourceDeleteTestCase):
    def test_the_scenario_is_gone_from_the_bundle(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(self.detail_url(uid)).data["scenarios"], [])

    def test_the_scenario_node_is_gone_from_the_graph(self):
        # Not merely unlinked: a scenario is bundle-local, so it is removed.
        uid, sid, etag = self.with_one_scenario()
        node = self.node_of(self.client.get(self.scenario_url(uid, sid)))

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertFalse(self.node_exists(node))

    def test_the_response_names_what_it_deleted(self):
        uid, sid, etag = self.with_one_scenario()
        node = self.node_of(self.client.get(self.scenario_url(uid, sid)))

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(self.iris(response.data["deleted"]), {str(node)})
        self.assertEqual(response.data["unlinked"], [])

    def test_the_response_names_the_class_of_what_it_deleted(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(
            [entry["type"] for entry in response.data["deleted"]],
            [str(SCENARIO_CLASS)],
        )

    def test_a_deleted_scenario_reads_back_as_not_found(self):
        uid, sid, etag = self.with_one_scenario()

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(self.client.get(self.scenario_url(uid, sid)).status_code, 404)

    def test_deleting_it_twice_answers_not_found(self):
        # Existence first, as it is everywhere else in this API: a client may
        # treat this 404 as success after a lost response, and a wrong
        # identifier stays distinguishable from one already gone.
        uid, sid, etag = self.with_one_scenario()
        first = self.delete(self.scenario_url(uid, sid), etag)

        second = self.delete(self.scenario_url(uid, sid), first["ETag"])

        self.assertEqual(second.status_code, 404, second.data)

    def test_the_bundle_version_moves(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertNotEqual(response["ETag"], etag)
        self.assertEqual(
            self.client.get(self.detail_url(uid))["ETag"], response["ETag"]
        )

    def test_a_sibling_scenario_is_untouched(self):
        uid, sid, etag = self.with_one_scenario()
        sibling = self.add_scenario(uid, etag, {**VALID_SCENARIO, "acronym": "LOW-RE"})
        self.assertEqual(sibling.status_code, 201, sibling.data)

        self.delete(self.scenario_url(uid, sid), sibling["ETag"])

        remaining = self.client.get(self.detail_url(uid)).data["scenarios"]
        self.assertEqual([one["acronym"] for one in remaining], ["LOW-RE"])


class DeleteAStudyReportTest(SubResourceDeleteTestCase):
    def test_the_report_is_gone_from_the_bundle(self):
        uid, rid, etag = self.with_one_report()

        response = self.delete(self.report_url(uid, rid), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            self.client.get(self.detail_url(uid)).data["study_reports"], []
        )

    def test_the_report_node_is_gone_from_the_graph(self):
        uid, rid, etag = self.with_one_report()
        node = self.node_of(self.client.get(self.report_url(uid, rid)))

        self.delete(self.report_url(uid, rid), etag)

        self.assertFalse(self.node_exists(node))

    def test_an_unknown_report_answers_not_found(self):
        uid, etag = self.created()

        response = self.delete(self.report_url(uid, ABSENT), etag)

        self.assertEqual(response.status_code, 404, response.data)


class DeleteADatasetLinkTest(SubResourceDeleteTestCase):
    def test_the_link_is_gone_from_the_scenario(self):
        uid, sid, did, etag = self.with_one_link()

        response = self.delete(self.link_url(uid, sid, did), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(self.links_url(uid, sid)).data["results"], [])

    def test_the_link_node_is_gone_from_the_graph(self):
        uid, sid, did, etag = self.with_one_link()
        node = self.node_of(self.client.get(self.link_url(uid, sid, did)))

        self.delete(self.link_url(uid, sid, did), etag)

        self.assertFalse(self.node_exists(node))

    def test_the_scenario_it_hung_off_stays(self):
        uid, sid, did, etag = self.with_one_link()

        self.delete(self.link_url(uid, sid, did), etag)

        self.assertEqual(self.client.get(self.scenario_url(uid, sid)).status_code, 200)

    def test_a_sibling_link_is_untouched(self):
        uid, sid, did, etag = self.with_one_link()
        sibling = self.add_link(uid, sid, etag, DATASET_LINK)
        self.assertEqual(sibling.status_code, 201, sibling.data)

        self.delete(self.link_url(uid, sid, did), sibling["ETag"])

        remaining = self.client.get(self.links_url(uid, sid)).data["results"]
        self.assertEqual([one["name"] for one in remaining], [DATASET_LINK["name"]])

    def test_deleting_one_link_lets_the_same_target_be_linked_again(self):
        # Why duplicates are refused at all: a remove has to be able to name
        # exactly one link, and afterwards the target is free again.
        uid, sid, did, etag = self.with_one_link()

        removed = self.delete(self.link_url(uid, sid, did), etag)
        again = self.add_link(uid, sid, removed["ETag"], TABLE_LINK)

        self.assertEqual(again.status_code, 201, again.data)

    def test_an_unknown_link_answers_not_found(self):
        uid, sid, etag = self.with_one_scenario()

        response = self.delete(self.link_url(uid, sid, ABSENT), etag)

        self.assertEqual(response.status_code, 404, response.data)

    def test_an_unknown_scenario_answers_not_found(self):
        uid, _ = self.created()

        response = self.delete(self.link_url(uid, ABSENT, ABSENT))

        self.assertEqual(response.status_code, 404, response.data)


class TwoHopChildrenTest(SubResourceDeleteTestCase):
    """A scenario's dataset links go with it, rather than being left behind.

    This is the half of today's browser delete that fails silently: input and
    output datasets hang off the *scenario*, one hop further than that delete
    walks, so every one of them leaves dataset nodes in the graph reachable
    from nothing.
    """

    def test_a_scenarios_dataset_links_are_deleted_with_it(self):
        uid, sid, did, etag = self.with_one_link()
        second = self.add_link(uid, sid, etag, DATASET_LINK)
        self.assertEqual(second.status_code, 201, second.data)
        links = [
            self.node_of(self.client.get(self.link_url(uid, sid, did))),
            self.node_of(
                self.client.get(
                    self.link_url(uid, sid, second.data[READ_ONLY_CONTAINER]["uid"])
                )
            ),
        ]

        response = self.delete(self.scenario_url(uid, sid), second["ETag"])

        self.assertEqual(response.status_code, 200, response.data)
        for node in links:
            self.assertFalse(self.node_exists(node), node)

    def test_the_response_names_the_children_it_deleted(self):
        uid, sid, did, etag = self.with_one_link()
        link = self.node_of(self.client.get(self.link_url(uid, sid, did)))
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(
            self.iris(response.data["deleted"]), {str(scenario), str(link)}
        )


class SharedNodesSurviveTest(SubResourceDeleteTestCase):
    """One case per shared class, not one representative.

    Each of these is a node another bundle can cite, so deleting one bundle's
    part may only ever remove the *link*. A representative test would have
    covered whichever classes happened to be right; this ticket exists because
    one of them was not.
    """

    def test_a_study_region_survives_the_scenario_citing_it(self):
        uid, sid, etag = self.with_scenario_regions()

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertTrue(self.node_exists(BERLIN))

    def test_an_interacting_region_survives_the_scenario_citing_it(self):
        uid, sid, etag = self.with_scenario_regions()

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertTrue(self.node_exists(BRANDENBURG))

    def test_a_region_keeps_its_label_for_the_bundles_still_citing_it(self):
        # The damage the browser delete does: stripping the label makes every
        # other bundle citing that node invalid against the shape.
        uid, sid, etag = self.with_scenario_regions()

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertTrue(
            self.store.ask(
                'ASK { %s %s "Berlin" }' % (URIRef(BERLIN).n3(), RDFS.label.n3())
            )
        )

    def test_an_author_survives_the_study_report_citing_them(self):
        uid, rid, etag = self.with_one_report()
        author = URIRef(
            self.client.get(self.report_url(uid, rid)).data["authors"][0]["iri"]
        )

        self.delete(self.report_url(uid, rid), etag)

        self.assertTrue(self.node_exists(author))

    def test_a_cited_document_survives_the_study_report_citing_it(self):
        # The reference node IS the document's URL, typed. Another bundle
        # citing the same paper points at that very node.
        uid, rid, etag = self.with_one_report(REPORT_WITH_REFERENCE)

        self.delete(self.report_url(uid, rid), etag)

        self.assertTrue(
            self.linked(REPORT_WITH_REFERENCE["reference"], RDF.type, REFERENCE_CLASS)
        )

    def test_the_bundles_own_shared_nodes_are_not_reached_at_all(self):
        # Contacts, organisations, funders, frameworks and models hang off the
        # bundle, not off a part, so a part delete must not walk up to them.
        uid, sid, etag = self.with_scenario_regions(
            {**VALID_PAYLOAD, **BUNDLE_WITH_SHARED_NODES}
        )

        self.delete(self.scenario_url(uid, sid), etag)

        read = self.client.get(self.detail_url(uid)).data
        for key, sent in BUNDLE_WITH_SHARED_NODES.items():
            self.assertEqual(
                [entry["label"] for entry in read[key]],
                [entry["label"] for entry in sent],
                key,
            )

    def test_a_picked_ontology_term_is_only_unlinked(self):
        # An sh:in pick is a bare OEO IRI with no triples of ours. All a delete
        # may do is drop the edge, and it may never invent a reason to reach
        # into the ontology.
        uid, sid, etag = self.with_one_scenario()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        term = URIRef(VALID_SCENARIO["scenario_types"][0])

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertFalse(self.linked(scenario, OEO.OEO_00390073, term))
        self.assertFalse(self.node_exists(term))


class GuardClauseTest(SubResourceDeleteTestCase):
    """The allowlist fails safe: anything still referenced is only unlinked.

    The allowlist says a class is bundle-local; the guard asks whether this
    particular node actually is. The two disagree when a node was minted
    globally, or claimed by two bundles, and the guard is what keeps that from
    becoming somebody else's data loss.
    """

    def test_a_scenario_another_bundle_cites_is_unlinked_not_deleted(self):
        uid, sid, etag = self.with_one_scenario()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        self.reference_from_outside(scenario)

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(self.node_exists(scenario))

    def test_the_response_says_it_was_unlinked_rather_than_deleted(self):
        uid, sid, etag = self.with_one_scenario()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        self.reference_from_outside(scenario)

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(self.iris(response.data["unlinked"]), {str(scenario)})
        self.assertEqual(response.data["deleted"], [])

    def test_it_leaves_this_bundle_even_when_it_is_only_unlinked(self):
        uid, sid, etag = self.with_one_scenario()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        self.reference_from_outside(scenario)

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(self.client.get(self.detail_url(uid)).data["scenarios"], [])
        self.assertFalse(self.linked(bundle_iri(uid), HAS_PART, scenario))

    def test_the_children_of_a_retained_node_are_retained_with_it(self):
        # The descent has to stop: the node stays, so everything below it is
        # still reachable, and deleting a child would corrupt the bundle that
        # kept it.
        uid, sid, did, etag = self.with_one_link()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        link = self.node_of(self.client.get(self.link_url(uid, sid, did)))
        self.reference_from_outside(scenario)

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertTrue(self.node_exists(link))

    def test_a_dataset_link_two_scenarios_claim_is_unlinked_not_deleted(self):
        uid, sid, did, etag = self.with_one_link()
        link = self.node_of(self.client.get(self.link_url(uid, sid, did)))
        self.reference_from_outside(link)

        response = self.delete(self.link_url(uid, sid, did), etag)

        self.assertEqual(self.iris(response.data["unlinked"]), {str(link)})
        self.assertTrue(self.node_exists(link))

    def test_a_reference_appearing_after_the_plan_refuses_the_write(self):
        """The plan is read; the graph can move before the write lands.

        The bundle's own version cannot catch this -- a write to *another*
        bundle does not move it -- so the plan's conclusion is asserted again
        inside the update. Nothing is written and the caller retries, and the
        retry sees the reference and unlinks instead of deleting.
        """
        uid, sid, etag = self.with_one_scenario()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        planned = plan_removal

        def plan_then_interfere(*args, **kwargs):
            removal = planned(*args, **kwargs)
            self.reference_from_outside(scenario)
            return removal

        with mock.patch("oekg.subresource_views.plan_removal", plan_then_interfere):
            response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(response.status_code, 409, response.data)
        self.assertTrue(self.node_exists(scenario))
        self.assertTrue(self.linked(bundle_iri(uid), HAS_PART, scenario))

    def test_the_retry_after_that_conflict_unlinks(self):
        # The conflict is worth giving only because the retry then does the
        # right thing: nothing was written, so the version has not moved and
        # the same If-Match still holds -- and this time the plan sees the
        # reference.
        uid, sid, etag = self.with_one_scenario()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        planned = plan_removal

        def plan_then_interfere(*args, **kwargs):
            removal = planned(*args, **kwargs)
            self.reference_from_outside(scenario)
            return removal

        with mock.patch("oekg.subresource_views.plan_removal", plan_then_interfere):
            conflict = self.delete(self.scenario_url(uid, sid), etag)
        self.assertEqual(conflict.status_code, 409, conflict.data)

        retry = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(self.iris(retry.data["unlinked"]), {str(scenario)})
        self.assertTrue(self.node_exists(scenario))


class DeletePreconditionTest(SubResourceDeleteTestCase):
    """The version, and no retyped token: ceremony proportional to blast radius.

    A wrong sub-resource delete removes one bounded, re-creatable part and is
    recorded in the history. A wrong bundle delete is neither, which is why
    that one -- and only that one -- also asks for the acronym back.
    """

    def test_without_if_match_it_is_refused(self):
        uid, sid, _ = self.with_one_scenario()

        response = self.delete(self.scenario_url(uid, sid))

        self.assertEqual(response.status_code, 428, response.data)
        self.assertEqual(self.client.get(self.scenario_url(uid, sid)).status_code, 200)

    def test_a_stale_if_match_is_refused(self):
        uid, sid, etag = self.with_one_scenario()
        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(response.status_code, 412, response.data)
        self.assertEqual(self.client.get(self.scenario_url(uid, sid)).status_code, 200)

    def test_no_confirmation_token_is_asked_for(self):
        # WF-06 decision 4, pinned: the retyped acronym guards the whole-bundle
        # delete and nothing smaller. A sub-resource delete carrying only the
        # version succeeds.
        uid, sid, etag = self.with_one_scenario()

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(response.status_code, 200, response.data)

    def test_a_non_owner_is_refused(self):
        uid, sid, etag = self.with_one_scenario()
        stranger = myuser.objects.create_user(
            name="someone-else", email="else@example.org", affiliation=""
        )

        response = self.delete(self.scenario_url(uid, sid), etag, as_user=stranger)

        self.assertEqual(response.status_code, 403, response.data)
        self.assertEqual(self.client.get(self.scenario_url(uid, sid)).status_code, 200)

    def test_an_ownerless_bundle_is_refused(self):
        uid, sid, etag = self.with_one_scenario()
        ScenarioBundleAccessControl.objects.filter(bundle_id=uid).delete()

        response = self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(response.status_code, 403, response.data)

    def test_an_unauthenticated_delete_is_refused(self):
        uid, sid, etag = self.with_one_scenario()
        self.client.logout()

        response = self.delete(self.scenario_url(uid, sid), etag, authenticate=False)

        self.assertIn(response.status_code, (401, 403))

    def test_an_unknown_part_answers_not_found_before_the_precondition(self):
        # Existence first: a client asking about something that is not there
        # should hear that, rather than be told its header is missing for a
        # resource that does not exist.
        uid, _ = self.created()

        response = self.delete(self.scenario_url(uid, ABSENT))

        self.assertEqual(response.status_code, 404, response.data)

    def test_an_unknown_bundle_answers_not_found(self):
        response = self.delete(self.scenario_url(ABSENT_BUNDLE, ABSENT))

        self.assertEqual(response.status_code, 404, response.data)


class DeleteHistoryTest(SubResourceDeleteTestCase):
    """Every partial delete records, with its diff.

    The asymmetry with the whole-bundle delete is deliberate and belongs to the
    next slice: this one is recoverable by re-creating the part, so what it
    removed is worth keeping; that one carries a whole bundle and would turn
    the history table into a backup store.
    """

    def entries(self, uid):
        return OEKG_Modifications.objects.filter(bundle_id=uid).order_by("id")

    def test_a_delete_writes_one_entry(self):
        uid, sid, etag = self.with_one_scenario()
        before = self.entries(uid).count()

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertEqual(self.entries(uid).count(), before + 1)

    def test_the_entry_names_the_verb_and_the_resource(self):
        uid, sid, etag = self.with_one_scenario()

        self.delete(self.scenario_url(uid, sid), etag)

        entry = self.entries(uid).last()
        self.assertEqual(entry.verb, DELETE)
        self.assertEqual(entry.resource_type, str(SCENARIO_CLASS))
        self.assertEqual(entry.resource_uuid, sid)

    def test_the_entry_carries_the_removed_triples_and_adds_nothing(self):
        uid, sid, etag = self.with_one_scenario()

        self.delete(self.scenario_url(uid, sid), etag)

        entry = self.entries(uid).last()
        self.assertTrue(entry.removed)
        self.assertIsNone(entry.added)

    def test_the_history_names_the_fields_that_went(self):
        uid, sid, etag = self.with_one_scenario()

        self.delete(self.scenario_url(uid, sid), etag)

        latest = self.client.get(self.history_url(uid), {"page_size": 1}).data[
            "results"
        ][0]
        removed = {
            change["field"]: change["removed"]
            for change in latest["changes"]
            if change["field"]
        }
        self.assertEqual(removed["acronym"], [VALID_SCENARIO["acronym"]])
        self.assertEqual(removed["label"], [VALID_SCENARIO["label"]])

    def test_a_deleted_study_report_records_against_its_own_class(self):
        uid, rid, etag = self.with_one_report()

        self.delete(self.report_url(uid, rid), etag)

        entry = self.entries(uid).last()
        self.assertEqual(entry.resource_type, str(STUDY_REPORT_CLASS))
        self.assertEqual(entry.resource_uuid, rid)

    def test_a_deleted_dataset_link_records_against_its_direction(self):
        uid, sid, did, etag = self.with_one_link()

        self.delete(self.link_url(uid, sid, did), etag)

        entry = self.entries(uid).last()
        self.assertEqual(entry.verb, DELETE)
        self.assertEqual(entry.resource_uuid, did)
        self.assertEqual(entry.resource_type, str(DIRECTIONS[0].node_class))  # input

    def test_a_refused_delete_records_nothing(self):
        uid, sid, etag = self.with_one_scenario()
        before = self.entries(uid).count()

        self.delete(self.scenario_url(uid, sid))

        self.assertEqual(self.entries(uid).count(), before)


class AllowlistTest(SimpleTestCase):
    """What may be deleted is a closed list, and it is checked against reality.

    Written out rather than derived from the resources this API mints, because
    a new addressable part is not automatically bundle-local -- the region
    wrapper was believed to be, and is shared by every bundle on the platform.
    This test fails when a part is added, which is the point: joining the
    allowlist has to be a decision somebody made.
    """

    def test_the_allowlist_is_exactly_the_bundle_local_classes(self):
        self.assertEqual(
            BUNDLE_LOCAL_CLASSES,
            frozenset(
                [part.node_class for part in BUNDLE_PARTS]
                + [direction.node_class for direction in DIRECTIONS]
            ),
        )

    def test_shared_classes_are_not_on_it(self):
        shared = [
            OEO.OEO_00000277,  # model
            OEO.OEO_00000172,  # framework
            OEO.OEO_00020032,  # study region wrapper
            OEO.OEO_00020036,  # interacting region wrapper
            OEO.OEO_00000064,  # author
            OEO.OEO_00000107,  # contact person
            OEO.OEO_00030022,  # organisation
            OEO.OEO_00090001,  # funder
            REFERENCE_CLASS,  # the cited document
        ]
        for node_class in shared:
            self.assertNotIn(node_class, BUNDLE_LOCAL_CLASSES, node_class)


class UntypedNodesAreLeftAloneTest(SubResourceDeleteTestCase):
    """Anything untyped or unlisted is unlinked, never removed.

    The allowlist decides by `rdf:type`, so a node carrying none cannot be on
    it. That is the conservative answer for exactly the data this API did not
    write, which is most of the graph.
    """

    def test_an_untyped_node_a_scenario_points_at_survives(self):
        uid, sid, etag = self.with_one_scenario()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        stray = URIRef("urn:oep:test:untyped-node")
        extra = Graph()
        extra.add((URIRef(str(scenario)), OEO.OEO_00020220, stray))
        extra.add((stray, RDFS.label, Literal("Something nobody typed")))
        self.store.insert(extra)

        self.delete(self.scenario_url(uid, sid), etag)

        self.assertTrue(self.node_exists(stray))
