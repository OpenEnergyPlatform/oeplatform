"""Deleting a whole bundle, in two steps.

This is the one irreversible operation in the API and the single most dangerous
thing it can do, so it is made deliberately awkward. The awkwardness is the
feature under test:

- **Two guards, defending two different accidents.** The version catches
  *somebody changed this since you looked*; the retyped acronym catches *right
  verb, wrong identifier*, which is the realistic failure for a pipeline
  looping over a list and the one a version cannot see -- it names the correct
  current version of the wrong bundle.
- **Existence first.** A repeated delete answers `404`, and a client may treat
  that as success. A blanket success would swallow the wrong-identifier delete,
  because a bundle that is gone has no acronym left to check against.
- **The blast radius is still bounded by type.** Slice 8's walk, rooted one
  level up: the bundle's own parts go, everything shared is unlinked, and a
  node another bundle cites is kept whatever its class.
- **What the ledger keeps and what it loses.** One event-only line survives,
  and the payloads of that bundle's earlier entries do not -- otherwise a
  deleted bundle would be reconstructable from the record of its own deletion.

Rule 5 of the client page rests on these tests: the two guards catch two
different accidents.

Documents: docs/oeplatform-code/web-api/oekg-api/scenario-bundles.md

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from unittest import mock
from urllib.parse import quote

from rdflib import RDFS, Graph, Literal, URIRef

from factsheet.models import (
    API_ERA,
    EMPTY_LEGACY_PAYLOAD,
    OEKG_Modifications,
    ScenarioBundleAccessControl,
)
from login.models import myuser
from oekg.bundles import BUNDLE_CLASS, bundle_iri
from oekg.fields import DC, HAS_PART
from oekg.history import DELETE
from oekg.removal import plan_bundle_removal
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.bundle_fixtures import VALID_PAYLOAD
from oekg.tests.test_dataset_link_api import DATASET_LINK
from oekg.tests.test_study_report_api import VALID_REPORT
from oekg.tests.test_subresource_delete import (
    ABSENT_BUNDLE,
    BERLIN,
    BRANDENBURG,
    BUNDLE_WITH_SHARED_NODES,
    SCENARIO_WITH_REGIONS,
    SubResourceDeleteTestCase,
)
from oekg.versioning import version_iri

ACRONYM = VALID_PAYLOAD["acronym"]


class BundleDeleteTestCase(SubResourceDeleteTestCase):
    """Everything a bundle can hold, so a delete is tested against a full one."""

    def delete_bundle(
        self,
        uid,
        etag=None,
        confirm=ACRONYM,
        as_user=None,
        authenticate=True,
    ):
        if authenticate:
            self.client.force_login(as_user or self.user)
        url = self.detail_url(uid)
        if confirm is not None:
            url = f"{url}?confirm={quote(confirm)}"
        headers = {} if etag is None else {"HTTP_IF_MATCH": etag}
        return self.client.delete(url, **headers)

    def furnished(self):
        """A bundle with a scenario, a dataset link, a report and shared nodes.

        One fixture rather than one per test: a delete's danger is what it
        reaches, so every test here runs against something that has everything
        to reach.
        """
        uid, etag = self.created(
            {
                **VALID_PAYLOAD,
                **BUNDLE_WITH_SHARED_NODES,
                "scenarios": [SCENARIO_WITH_REGIONS],
                "study_reports": [VALID_REPORT],
            }
        )
        read = self.client.get(self.detail_url(uid))
        sid = read.data["scenarios"][0][READ_ONLY_CONTAINER]["uid"]
        added = self.add_link(uid, sid, etag, DATASET_LINK)
        self.assertEqual(added.status_code, 201, added.data)
        return uid, sid, added["ETag"]

    def bundle_exists_in_graph(self, uid) -> bool:
        return self.store.ask(
            "ASK { %s a %s }" % (bundle_iri(uid).n3(), BUNDLE_CLASS.n3())
        )

    def first_link_node(self, uid, sid) -> URIRef:
        """The dataset link hanging off this scenario, as a node."""
        results = self.client.get(self.links_url(uid, sid)).data["results"]
        return URIRef(results[0][READ_ONLY_CONTAINER]["iri"])

    def delete_while_interfering(self, uid, sid, etag):
        """Delete, with another bundle claiming a scenario after the plan.

        The window the plan's guard exists for: it is read from a graph that
        can move before the write lands, and the bundle's own version does not
        notice a write to somebody else's.
        """
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        planned = plan_bundle_removal

        def plan_then_interfere(*args, **kwargs):
            removal = planned(*args, **kwargs)
            self.reference_from_outside(scenario)
            return removal

        with mock.patch("oekg.writes.plan_bundle_removal", plan_then_interfere):
            return self.delete_bundle(uid, etag)

    def forget_the_version_node(self, uid) -> None:
        """Put a bundle back into the state the browser leaves it in.

        Every bundle in the live graph has no version node until this API first
        writes to it, so this is the ordinary case rather than a contrived one.
        """
        node = version_iri(uid).n3()
        self.store.update(
            "WITH <%s> DELETE { %s ?p ?o } WHERE { %s ?p ?o }"
            % (self.graph_name, node, node)
        )

    def node_labelled(self, label) -> URIRef:
        """The node carrying this label. Minted shared nodes have no other
        address a client can read: the payload's `iri` on a framework or a
        model is the project's homepage, not the node."""
        rows = self.store.select(
            "SELECT ?s WHERE { ?s %s %s }" % (RDFS.label.n3(), Literal(label).n3())
        )
        self.assertEqual(len(rows), 1, f"expected exactly one node labelled {label!r}")
        return URIRef(rows[0]["s"])

    def entries(self, uid):
        return OEKG_Modifications.objects.filter(bundle_id=uid).order_by("id")


class DeleteABundleTest(BundleDeleteTestCase):
    def test_the_bundle_is_gone(self):
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(self.detail_url(uid)).status_code, 404)

    def test_the_bundle_node_is_gone_from_the_graph(self):
        uid, _, etag = self.furnished()

        self.delete_bundle(uid, etag)

        self.assertFalse(self.bundle_exists_in_graph(uid))
        self.assertFalse(self.node_exists(bundle_iri(uid)))

    def test_the_response_names_the_bundle_it_deleted(self):
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag)

        self.assertIn(
            {"iri": str(bundle_iri(uid)), "type": str(BUNDLE_CLASS)},
            response.data["deleted"],
        )

    def test_the_response_names_the_bundle_and_the_version_it_deleted(self):
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag)

        meta = response.data[READ_ONLY_CONTAINER]
        self.assertEqual(meta["uid"], uid)
        self.assertEqual(meta["acronym"], ACRONYM)
        self.assertEqual(f'"{meta["version_before"]}"', etag)

    def test_it_carries_no_entity_tag(self):
        # There is no version left to name. An ETag here would be a validator
        # for a resource the same response says no longer exists.
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag)

        self.assertIsNone(response.headers.get("ETag"))

    def test_its_parts_go_with_it(self):
        uid, sid, etag = self.furnished()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))

        self.delete_bundle(uid, etag)

        self.assertFalse(self.node_exists(scenario))

    def test_its_two_hop_children_go_with_it(self):
        # Dataset links hang off the scenario, one hop further out than the
        # browser's delete walks -- which is how it leaves them behind.
        uid, sid, etag = self.furnished()
        links = self.client.get(self.links_url(uid, sid)).data["results"]
        nodes = [URIRef(one[READ_ONLY_CONTAINER]["iri"]) for one in links]
        self.assertTrue(nodes)

        self.delete_bundle(uid, etag)

        for node in nodes:
            self.assertFalse(self.node_exists(node), node)

    def test_its_study_reports_go_with_it(self):
        uid, _, etag = self.furnished()
        reports = self.client.get(self.detail_url(uid)).data["study_reports"]
        node = URIRef(reports[0][READ_ONLY_CONTAINER]["iri"])

        self.delete_bundle(uid, etag)

        self.assertFalse(self.node_exists(node))

    def test_a_bundle_the_browser_wrote_can_be_deleted(self):
        """No version node, so the precondition is the absence of one.

        Every bundle in the live graph is in this state until the API writes to
        it, so a delete that only worked on API-written bundles would not be a
        delete of the platform's bundles.
        """
        uid, _, _ = self.furnished()
        self.forget_the_version_node(uid)

        response = self.delete_bundle(uid, '"0"')

        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(self.bundle_exists_in_graph(uid))

    def test_the_version_node_goes_with_it(self):
        """The residue the browser's delete leaves behind (issue #2440).

        A version node that outlives its bundle asserts that a bundle nobody
        can read is at version 4, and the next write's guard would match it --
        which is how a patch came to write a deleted bundle's fields back as
        untyped orphans.
        """
        uid, _, etag = self.furnished()

        self.delete_bundle(uid, etag)

        self.assertFalse(self.node_exists(version_iri(uid)))


class SharedNodesSurviveABundleDeleteTest(BundleDeleteTestCase):
    """A published record of somebody else's may not be damaged by this delete.

    One case per shared class, for the same reason slice 8 has one: the
    allowlist was wrong once while it was being drafted, and a representative
    test would have covered whichever classes happened to be right.
    """

    def deleted_bundle_with_shared_nodes(self):
        """The shared nodes a full bundle points at, and the delete's answer.

        The nodes are found by label rather than read off the payload: a
        framework's `iri` key is the project's *homepage*, per the shape, not
        the node's address, and the node's address is what survives or does
        not.
        """
        uid, _, etag = self.furnished()
        shared = {
            label: self.node_labelled(label)
            for entries in BUNDLE_WITH_SHARED_NODES.values()
            for entry in entries
            for label in [entry["label"]]
        }
        shared["Berlin"] = URIRef(BERLIN)
        shared["Brandenburg"] = URIRef(BRANDENBURG)
        response = self.delete_bundle(uid, etag)
        self.assertEqual(response.status_code, 200, response.data)
        return shared, response

    def test_every_shared_node_it_pointed_at_survives(self):
        shared, _ = self.deleted_bundle_with_shared_nodes()

        for label, node in shared.items():
            self.assertTrue(self.node_exists(node), label)

    def test_they_keep_their_labels_for_the_bundles_still_citing_them(self):
        # The damage the browser's delete does: stripping the label makes every
        # other bundle citing that node invalid against the shape.
        shared, _ = self.deleted_bundle_with_shared_nodes()

        for label, node in shared.items():
            self.assertEqual(self.node_labelled(label), node, label)

    def test_none_of_them_is_reported_as_deleted(self):
        # Nor as unlinked: every delete unlinks the shared nodes its subject
        # pointed at, and listing the rule that always applies would bury the
        # one line that is news -- a node kept because somebody else cites it.
        shared, response = self.deleted_bundle_with_shared_nodes()

        reported = self.iris(response.data["deleted"]) | self.iris(
            response.data["unlinked"]
        )
        self.assertEqual(reported & {str(node) for node in shared.values()}, set())

    def test_another_bundle_citing_the_same_region_is_untouched(self):
        first, _, first_etag = self.furnished()
        second, second_etag = self.created({**VALID_PAYLOAD, "acronym": "OTHER"})
        added = self.add_scenario(second, second_etag, SCENARIO_WITH_REGIONS)
        self.assertEqual(added.status_code, 201, added.data)

        self.delete_bundle(first, first_etag)

        read = self.client.get(self.detail_url(second))
        self.assertEqual(read.status_code, 200, read.data)
        self.assertEqual(len(read.data["scenarios"][0]["study_regions"]), 1)


class BundleDeleteGuardClauseTest(BundleDeleteTestCase):
    """A node another bundle cites is kept, and the response says so."""

    def test_a_scenario_another_bundle_cites_is_unlinked_not_deleted(self):
        uid, sid, etag = self.furnished()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        self.reference_from_outside(scenario)

        response = self.delete_bundle(uid, etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(self.node_exists(scenario))
        self.assertIn(str(scenario), self.iris(response.data["unlinked"]))
        self.assertNotIn(str(scenario), self.iris(response.data["deleted"]))

    def test_the_bundle_still_goes_when_a_child_is_kept(self):
        # The guard may only ever downgrade a *child*. A bundle nothing can
        # delete would be a worse outcome than one deleted while something
        # cited a part of it.
        uid, sid, etag = self.furnished()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        self.reference_from_outside(scenario)

        self.delete_bundle(uid, etag)

        self.assertFalse(self.bundle_exists_in_graph(uid))

    def test_the_bundle_no_longer_cites_the_node_it_kept(self):
        uid, sid, etag = self.furnished()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        self.reference_from_outside(scenario)

        self.delete_bundle(uid, etag)

        self.assertFalse(self.linked(bundle_iri(uid), HAS_PART, scenario))

    def test_the_children_of_a_kept_node_are_kept_with_it(self):
        # The descent stops where the guard does: the scenario stays, so its
        # dataset link is still reachable, and deleting it would corrupt the
        # bundle that kept the scenario.
        uid, sid, etag = self.furnished()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        link = self.first_link_node(uid, sid)
        self.reference_from_outside(scenario)

        self.delete_bundle(uid, etag)

        self.assertTrue(self.node_exists(link))

    def test_a_kept_nodes_children_are_reported_beside_it(self):
        """They were candidates and they survived, so they are in the answer.

        Reporting them says something slightly stronger than it means -- the
        link was not unlinked from anything, it was simply never reached --
        but the alternative is a delete that silently leaves nodes behind, and
        a list the caller can check is worth that imprecision.
        """
        uid, sid, etag = self.furnished()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        link = self.first_link_node(uid, sid)
        self.reference_from_outside(scenario)

        response = self.delete_bundle(uid, etag)

        self.assertEqual(
            self.iris(response.data["unlinked"]), {str(scenario), str(link)}
        )

    def test_a_reference_appearing_after_the_plan_refuses_the_write(self):
        """The plan is read; the graph can move before the write lands.

        The bundle's own version cannot catch this -- a write to *another*
        bundle does not move it -- so the plan's conclusion travels with the
        write and is asserted inside it.
        """
        uid, sid, etag = self.furnished()

        response = self.delete_while_interfering(uid, sid, etag)

        self.assertEqual(response.status_code, 409, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_nothing_is_recorded_when_the_guard_refuses(self):
        uid, sid, etag = self.furnished()
        before = self.entries(uid).count()

        self.delete_while_interfering(uid, sid, etag)

        self.assertEqual(self.entries(uid).count(), before)
        self.assertTrue(
            ScenarioBundleAccessControl.objects.filter(bundle_id=uid).exists()
        )

    def test_the_retry_after_that_conflict_unlinks(self):
        # The conflict is worth giving only because the retry then does the
        # right thing: nothing was written, so the version has not moved and
        # the same If-Match still holds -- and this time the plan sees the
        # reference.
        uid, sid, etag = self.furnished()
        scenario = self.node_of(self.client.get(self.scenario_url(uid, sid)))
        conflict = self.delete_while_interfering(uid, sid, etag)
        self.assertEqual(conflict.status_code, 409, conflict.data)

        retry = self.delete_bundle(uid, etag)

        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertIn(str(scenario), self.iris(retry.data["unlinked"]))
        self.assertTrue(self.node_exists(scenario))


class FirstStepTest(BundleDeleteTestCase):
    """Step one is the read a client needs anyway.

    Nothing is built for it -- that is the point of a two-step delete whose
    first step is a `GET`. What is pinned here is that the read really does
    carry both tokens the second step asks for, because a delete needing a
    value no read returns is not a two-step delete, it is an impossible one.
    """

    def test_the_read_names_the_confirmation_token(self):
        uid, _, _ = self.furnished()

        read = self.client.get(self.detail_url(uid))

        self.assertEqual(read.data["acronym"], ACRONYM)

    def test_the_read_names_the_version_to_guard_on(self):
        uid, _, etag = self.furnished()

        read = self.client.get(self.detail_url(uid))

        self.assertEqual(read["ETag"], etag)
        self.assertEqual(f'"{read.data[READ_ONLY_CONTAINER]["version"]}"', etag)

    def test_what_the_read_returns_is_enough_to_delete_with(self):
        uid, _, _ = self.furnished()
        read = self.client.get(self.detail_url(uid))

        response = self.delete_bundle(uid, read["ETag"], confirm=read.data["acronym"])

        self.assertEqual(response.status_code, 200, response.data)


class BundleDeleteConfirmationTest(BundleDeleteTestCase):
    """The guard a version cannot give: right verb, wrong identifier."""

    def test_without_a_confirmation_it_is_refused(self):
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag, confirm=None)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_the_refusal_says_what_to_send(self):
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag, confirm=None)

        self.assertIn("confirm=", response.data["detail"])

    def test_another_bundles_acronym_is_refused(self):
        # The accident this exists for: a pipeline looping over identifiers,
        # holding a perfectly current version of the wrong bundle.
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag, confirm="SOME-OTHER-BUNDLE")

        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_the_comparison_is_exact(self):
        # Normalising would let `api-test` confirm a delete of `API-TEST`,
        # which is the confusion the check exists to catch.
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag, confirm=ACRONYM.lower())

        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_an_empty_confirmation_is_refused(self):
        uid, _, etag = self.furnished()

        response = self.client.delete(
            f"{self.detail_url(uid)}?confirm=", HTTP_IF_MATCH=etag
        )

        self.assertEqual(response.status_code, 400, response.data)

    def test_a_bundle_with_no_acronym_cannot_be_confirmed(self):
        """A browser-written bundle may have none, and then there is no token.

        Refused rather than substituted: the way out is to give it an acronym
        with a `PATCH`, which is allowed because the missing one is a violation
        this caller did not introduce.
        """
        uid, _, etag = self.furnished()
        stored = Graph()
        stored.add((bundle_iri(uid), DC.acronym, Literal(ACRONYM)))
        self.store.update(self.store.delete_data(stored))

        response = self.delete_bundle(uid, etag, confirm=ACRONYM)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("no acronym", response.data["detail"])
        self.assertTrue(self.bundle_exists_in_graph(uid))


class BundleDeletePreconditionTest(BundleDeleteTestCase):
    """The version, exactly as every other write asks for it."""

    def test_without_if_match_it_is_refused(self):
        uid, _, _ = self.furnished()

        response = self.delete_bundle(uid)

        self.assertEqual(response.status_code, 428, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_a_stale_if_match_is_refused(self):
        uid, _, etag = self.furnished()
        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        response = self.delete_bundle(uid, etag)

        self.assertEqual(response.status_code, 412, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_a_wildcard_if_match_is_refused_as_absent(self):
        # `*` satisfies the letter of the precondition while withholding the
        # one thing it is for.
        uid, _, _ = self.furnished()

        response = self.delete_bundle(uid, "*")

        self.assertEqual(response.status_code, 428, response.data)

    def test_the_current_version_and_the_acronym_together_succeed(self):
        uid, _, etag = self.furnished()

        response = self.delete_bundle(uid, etag)

        self.assertEqual(response.status_code, 200, response.data)


class BundleDeleteOrderTest(BundleDeleteTestCase):
    """The order of the refusals is the contract, not an accident.

    Existence, then ownership, then the version, then the confirmation. Each
    of these asserts that a *later* guard's failure does not mask an earlier
    one's answer.
    """

    def test_an_unknown_bundle_answers_not_found_with_nothing_else_sent(self):
        self.client.force_login(self.user)

        response = self.client.delete(self.detail_url(ABSENT_BUNDLE))

        self.assertEqual(response.status_code, 404, response.data)

    def test_an_identifier_this_api_never_mints_answers_not_found(self):
        self.client.force_login(self.user)

        response = self.client.delete(self.detail_url("not-a-uuid"))

        self.assertEqual(response.status_code, 404, response.data)

    def test_deleting_it_twice_answers_not_found(self):
        """A client may treat this as success after a lost response.

        And it is why the second call is not a blanket success: a bundle that
        is gone has no acronym left to check a confirmation against, so
        answering `204` to anything would confirm anything.
        """
        uid, _, etag = self.furnished()
        first = self.delete_bundle(uid, etag)
        self.assertEqual(first.status_code, 200, first.data)

        second = self.delete_bundle(uid, etag)

        self.assertEqual(second.status_code, 404, second.data)

    def test_a_non_owner_is_refused_before_the_confirmation_is_read(self):
        uid, _, etag = self.furnished()
        stranger = self.other_user()

        response = self.delete_bundle(uid, etag, confirm="WRONG", as_user=stranger)

        self.assertEqual(response.status_code, 403, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_the_precondition_is_read_before_the_confirmation(self):
        uid, _, _ = self.furnished()

        response = self.delete_bundle(uid, etag=None, confirm=None)

        self.assertEqual(response.status_code, 428, response.data)

    def test_an_unauthenticated_delete_is_refused(self):
        uid, _, etag = self.furnished()
        self.client.logout()

        response = self.delete_bundle(uid, etag, authenticate=False)

        self.assertIn(response.status_code, (401, 403))
        self.assertTrue(self.bundle_exists_in_graph(uid))


class BundleDeleteOwnershipTest(BundleDeleteTestCase):
    def test_the_ownership_rows_go_with_the_bundle(self):
        uid, _, etag = self.furnished()
        self.assertTrue(
            ScenarioBundleAccessControl.objects.filter(bundle_id=uid).exists()
        )

        self.delete_bundle(uid, etag)

        self.assertFalse(
            ScenarioBundleAccessControl.objects.filter(bundle_id=uid).exists()
        )

    def test_every_owners_row_goes_not_just_the_callers(self):
        uid, _, etag = self.furnished()
        second = self.other_user()
        ScenarioBundleAccessControl.objects.create(owner_user=second, bundle_id=uid)

        self.delete_bundle(uid, etag)

        self.assertEqual(
            ScenarioBundleAccessControl.objects.filter(bundle_id=uid).count(), 0
        )

    def test_another_bundles_ownership_rows_are_untouched(self):
        uid, _, etag = self.furnished()
        other, _ = self.created({**VALID_PAYLOAD, "acronym": "OTHER"})

        self.delete_bundle(uid, etag)

        self.assertTrue(
            ScenarioBundleAccessControl.objects.filter(bundle_id=other).exists()
        )

    def test_a_non_owner_is_refused(self):
        uid, _, etag = self.furnished()
        stranger = myuser.objects.create_user(
            name="a-stranger", email="stranger@example.org", affiliation=""
        )

        response = self.delete_bundle(uid, etag, as_user=stranger)

        self.assertEqual(response.status_code, 403, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_a_second_owner_may_delete(self):
        uid, _, etag = self.furnished()
        second = self.other_user()
        ScenarioBundleAccessControl.objects.create(owner_user=second, bundle_id=uid)

        response = self.delete_bundle(uid, etag, as_user=second)

        self.assertEqual(response.status_code, 200, response.data)

    def test_an_ownerless_bundle_is_refused_to_a_normal_user(self):
        # Intended, not an accident: records of unknown provenance fail closed.
        uid, _, etag = self.furnished()
        ScenarioBundleAccessControl.objects.filter(bundle_id=uid).delete()

        response = self.delete_bundle(uid, etag)

        self.assertEqual(response.status_code, 403, response.data)
        self.assertTrue(self.bundle_exists_in_graph(uid))

    def test_an_ownerless_bundle_is_deletable_by_an_administrator(self):
        uid, _, etag = self.furnished()
        ScenarioBundleAccessControl.objects.filter(bundle_id=uid).delete()
        admin = self.other_user(name="an-admin", email="admin@example.org")
        admin.is_admin = True
        admin.save()

        response = self.delete_bundle(uid, etag, as_user=admin)

        self.assertEqual(response.status_code, 200, response.data)

    def test_a_lost_ownership_removal_is_named_beside_the_success(self):
        # The graph has already committed; a failure here may be reported but
        # never turned into an error for a delete that happened.
        uid, _, etag = self.furnished()

        with mock.patch("oekg.writes.forget_ownership", return_value=False):
            response = self.delete_bundle(uid, etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIs(response.data[READ_ONLY_CONTAINER]["ownership_forgotten"], False)


class BundleDeleteHistoryTest(BundleDeleteTestCase):
    """One event-only line, and the payloads underneath it pruned."""

    def deleted(self):
        uid, _, etag = self.furnished()
        before = self.entries(uid).count()
        self.assertGreater(before, 1, "the fixture should have written history")
        response = self.delete_bundle(uid, etag)
        self.assertEqual(response.status_code, 200, response.data)
        return uid, response

    def test_the_delete_is_recorded(self):
        uid, _ = self.deleted()

        latest = self.entries(uid).last()
        self.assertEqual(latest.verb, DELETE)
        self.assertEqual(latest.resource_type, str(BUNDLE_CLASS))
        self.assertEqual(latest.era, API_ERA)

    def test_the_line_names_the_actor_the_acronym_and_the_version(self):
        uid, _ = self.deleted()

        latest = self.entries(uid).last()
        self.assertEqual(latest.user, self.user)
        self.assertEqual(latest.acronym, ACRONYM)
        self.assertIsNotNone(latest.version_before)
        self.assertIsNone(latest.version_after)

    def test_the_line_carries_no_payload(self):
        # A diff would be a copy of the bundle that was just deleted, which
        # would mean deleting did not delete.
        uid, _ = self.deleted()

        latest = self.entries(uid).last()
        self.assertIsNone(latest.removed)
        self.assertIsNone(latest.added)

    def test_the_earlier_entries_lose_their_payloads(self):
        uid, _ = self.deleted()

        for entry in self.entries(uid):
            self.assertIsNone(entry.removed, entry.verb)
            self.assertIsNone(entry.added, entry.verb)

    def test_the_earlier_entries_keep_their_structured_columns(self):
        # The ledger survives: what changed and who changed it is still there,
        # and only the content of the change is gone.
        uid, _ = self.deleted()

        creates = self.entries(uid).filter(verb="POST")
        self.assertTrue(creates.exists())
        for entry in creates:
            self.assertEqual(entry.user, self.user)
            self.assertIsNotNone(entry.version_after)

    def test_a_legacy_payload_is_pruned_too(self):
        # Browser rows store the bundle's whole state rather than a diff, so
        # they are the ones a deleted bundle would be rebuilt from.
        uid, _, etag = self.furnished()
        legacy = OEKG_Modifications.objects.create(
            bundle_id=uid, old_state="{}", new_state='{"label": "secret"}'
        )

        self.delete_bundle(uid, etag)

        legacy.refresh_from_db()
        self.assertEqual(legacy.old_state, EMPTY_LEGACY_PAYLOAD)
        self.assertEqual(legacy.new_state, EMPTY_LEGACY_PAYLOAD)

    def test_another_bundles_payloads_are_untouched(self):
        uid, _, etag = self.furnished()
        other, _ = self.created({**VALID_PAYLOAD, "acronym": "OTHER"})

        self.delete_bundle(uid, etag)

        self.assertTrue(
            any(entry.added for entry in self.entries(other)),
            "pruning must be scoped to the deleted bundle",
        )

    def test_the_history_is_still_readable_after_the_delete(self):
        # The one line a whole-bundle delete leaves is the whole of what it
        # leaves. A trace nobody can read is not much of a trace.
        uid, _ = self.deleted()

        response = self.client.get(self.history_url(uid))

        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["results"])

    def test_the_read_history_names_the_deleted_bundles_acronym(self):
        uid, _ = self.deleted()

        latest = self.client.get(self.history_url(uid)).data["results"][0]

        self.assertEqual(latest["verb"], DELETE)
        self.assertEqual(latest["acronym"], ACRONYM)
        self.assertIsNone(latest["version_after"])

    def test_the_read_history_says_nothing_about_what_the_entries_changed(self):
        # Not an empty list -- that would say nothing changed. The payloads are
        # gone, so what is known is that nothing records which fields moved.
        uid, _ = self.deleted()

        for entry in self.client.get(self.history_url(uid)).data["results"]:
            self.assertIsNone(entry["changes"], entry["verb"])

    def test_a_bundle_that_never_existed_still_answers_not_found(self):
        response = self.client.get(self.history_url(ABSENT_BUNDLE))

        self.assertEqual(response.status_code, 404, response.data)

    def test_a_lost_history_entry_is_named_beside_the_success(self):
        uid, _, etag = self.furnished()

        with mock.patch("oekg.writes.record_bundle_deletion", return_value=False):
            response = self.delete_bundle(uid, etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIs(response.data[READ_ONLY_CONTAINER]["history_recorded"], False)
        self.assertFalse(self.bundle_exists_in_graph(uid))
