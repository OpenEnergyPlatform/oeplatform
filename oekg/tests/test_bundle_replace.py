"""Replace a whole bundle in one call: the endpoint the API was built towards.

Three properties carry this slice, and each of them is something the obvious
implementation gets wrong:

- **Omission removes, and removal is still the typed containment walk.** A node
  another bundle cites is unlinked rather than destroyed, and the response says
  which were which -- so a client asserts on the consequence rather than
  inferring it from a status code.
- **Identity survives a re-import.** A nested resource that sends back the
  `_meta.uid` it was read with keeps its node. Without that, every run would
  delete and recreate every scenario in the bundle, churning identifiers and
  filling the history with deletions nobody asked for -- and the happy-path
  test would still pass.
- **Dataset links are part of the bundle payload.** They are bundle-local for
  the purposes of deletion but used to be absent from the bundle read, which is
  exactly the combination that makes a naive replace destroy every citation in
  the bundle. `ReplaceKeepsDatasetLinksTest` is the test that would not have
  been written by accident; issue #2473 is where the hazard was found.

Rule 3 of the client page rests on these tests: delete-by-omission lives
at this one address and nowhere else.

Documents: docs/oeplatform-code/web-api/oekg-api/scenario-bundles.md

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse
from rdflib import RDF, RDFS, Graph, URIRef

from factsheet.models import OEKG_Modifications
from oekg.bundles import (
    BUNDLE_FIELDS,
    SCENARIO,
    SCENARIO_CLASS,
    SCENARIO_FIELDS,
    STUDY_REPORT_FIELDS,
    bundle_iri,
    find_part,
)
from oekg.fields import OEO
from oekg.graph_store import GraphStore
from oekg.history import REPLACE
from oekg.reads import read_bundle
from oekg.replacement import EMPTY_VALUE
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.bundle_fixtures import VALID_PAYLOAD
from oekg.tests.test_dataset_link_api import (
    DATASET_LINK,
    TABLE_LINK,
    DatasetLinkTestCase,
    ExternalLinkMixin,
)
from oekg.tests.test_scenario_api import VALID_SCENARIO

OTHER_SCENARIO = {
    "label": "A low renewables scenario",
    "acronym": "LOW-RE",
    "scenario_types": [str(OEO.OEO_00000364)],
}


class EmptyValueCoverageTest(SimpleTestCase):
    """Every field kind says what omitting it means, or omission is undefined.

    The same shape as `AllowlistTest` and `ResolverCoverageTest`: a table this
    API reads at runtime, checked by a test that fails when somebody adds to
    the thing it has to keep up with. Without it the first declaration to omit
    a field of a new kind is the one that finds out -- and this is the endpoint
    where omission means deletion, so "finding out" is the expensive kind.
    """

    def test_every_field_kind_in_use_says_what_omitting_it_means(self):
        kinds = {
            field.kind
            for table in (BUNDLE_FIELDS, SCENARIO_FIELDS, STUDY_REPORT_FIELDS)
            for field in table
        }

        self.assertEqual(
            kinds - set(EMPTY_VALUE),
            set(),
            "A field table uses a kind `EMPTY_VALUE` has no entry for, so a "
            "replace that omits such a field has no defined meaning. Decide "
            "what an absent one declares and add it to the table.",
        )


class ReplaceTestCase(DatasetLinkTestCase):
    """A bundle, and the two calls a pipeline makes: read it, declare it."""

    def replace_url(self, uid):
        return reverse("api:scenario-bundle-replace", kwargs={"uid": uid})

    def replace(self, uid, payload, if_match=None, as_user=None, authenticate=True):
        if authenticate:
            self.client.force_login(as_user or self.user)
        headers = {} if if_match is None else {"HTTP_IF_MATCH": if_match}
        return self.client.post(
            self.replace_url(uid),
            data=payload,
            content_type="application/json",
            **headers,
        )

    def read_body(self, uid):
        """The bundle as a client receives it -- through the renderer.

        Not `response.data`, which still holds `datetime` objects and the
        framework's own wrappers. A round trip that went through neither would
        prove nothing about the one a pipeline makes.
        """
        response = self.client.get(self.detail_url(uid))
        self.assertEqual(response.status_code, 200, response.data)
        return json.loads(response.content), response["ETag"]

    def declared(self, body, **changes):
        """A read body with the read-only container dropped and edits applied."""
        payload = {key: value for key, value in body.items() if key != "_meta"}
        payload.update(changes)
        return payload

    def stored(self, uid):
        return read_bundle(GraphStore.from_settings(), uid)


class ReplaceAppliesTheDeclarationTest(ReplaceTestCase):
    def test_a_declared_field_is_changed(self):
        uid, etag = self.created()
        body, _ = self.read_body(uid)

        response = self.replace(uid, self.declared(body, label="Renamed"), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["label"], "Renamed")

    def test_a_field_the_declaration_omits_is_emptied(self):
        # The whole difference between this endpoint and a `PATCH`: there, an
        # absent key is untouched; here it is a statement that the bundle does
        # not have that field.
        uid, etag = self.created()
        body, _ = self.read_body(uid)
        declaration = self.declared(body)
        del declaration["abstract"]

        response = self.replace(uid, declaration, etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNone(response.data["abstract"])

    def test_a_nested_field_the_declaration_omits_is_emptied_too(self):
        # The rule reaches all the way down: a declaration is the whole bundle,
        # so a key a nested resource does not carry is a statement about that
        # resource, not silence about it.
        uid, etag = self.created()
        added = self.add_scenario(
            uid, etag, {**VALID_SCENARIO, "abstract": "Written once"}
        )
        self.assertEqual(added.status_code, 201, added.data)
        body, etag = self.read_body(uid)
        scenario = {
            key: value
            for key, value in body["scenarios"][0].items()
            if key != "abstract"
        }

        response = self.replace(uid, self.declared(body, scenarios=[scenario]), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNone(response.data["scenarios"][0]["abstract"])

    def test_a_scenario_the_declaration_omits_is_removed(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body, scenarios=[]), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["scenarios"], [])
        self.assertIsNone(find_part(self.stored(uid), uid, SCENARIO, sid))

    def test_a_scenario_the_declaration_adds_is_created(self):
        uid, etag = self.created()
        body, _ = self.read_body(uid)

        response = self.replace(
            uid, self.declared(body, scenarios=[VALID_SCENARIO]), etag
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["scenarios"]), 1)
        self.assertEqual(response.data["scenarios"][0]["acronym"], "HIGH-RE")

    def test_adding_changing_and_removing_happen_in_one_call(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)
        kept = body["scenarios"][0]

        response = self.replace(
            uid,
            self.declared(
                body,
                label="Declared afresh",
                scenarios=[{**kept, "label": "Still here"}, OTHER_SCENARIO],
            ),
            etag,
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["label"], "Declared afresh")
        acronyms = sorted(one["acronym"] for one in response.data["scenarios"])
        self.assertEqual(acronyms, ["HIGH-RE", "LOW-RE"])
        self.assertEqual(find_part(self.stored(uid), uid, SCENARIO, sid) is None, False)

    def test_the_version_advances_once(self):
        uid, etag = self.created()
        body, _ = self.read_body(uid)

        response = self.replace(uid, self.declared(body, label="Renamed"), etag)

        self.assertEqual(response.data[READ_ONLY_CONTAINER]["version"], 2)
        self.assertEqual(response["ETag"], '"2"')


class ReplaceReportsWhatItRemovedTest(ReplaceTestCase):
    """A client asserts on the consequence rather than inferring it."""

    def test_the_answer_names_what_was_deleted(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)
        node = str(find_part(self.stored(uid), uid, SCENARIO, sid))

        response = self.replace(uid, self.declared(body, scenarios=[]), etag)

        deleted = response.data[READ_ONLY_CONTAINER]["deleted"]
        self.assertIn(node, [entry["iri"] for entry in deleted])
        self.assertIn(str(SCENARIO_CLASS), [entry["type"] for entry in deleted])

    def test_a_declaration_that_removes_nothing_reports_nothing(self):
        uid, etag = self.created()
        body, _ = self.read_body(uid)

        response = self.replace(uid, self.declared(body, label="Renamed"), etag)

        self.assertEqual(response.data[READ_ONLY_CONTAINER]["deleted"], [])
        self.assertEqual(response.data[READ_ONLY_CONTAINER]["unlinked"], [])

    def test_a_node_something_else_cites_is_unlinked_and_not_destroyed(self):
        # The guard can only ever downgrade a delete to an unlink, and omission
        # is a different way of naming which nodes go -- not a different rule
        # about what going means.
        uid, sid, etag = self.with_one_scenario()
        node = find_part(self.stored(uid), uid, SCENARIO, sid)
        citation = Graph()
        citation.add((bundle_iri("another-bundle"), OEO.OEO_00000000, node))
        self.store.insert(citation)
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body, scenarios=[]), etag)

        meta = response.data[READ_ONLY_CONTAINER]
        self.assertEqual([entry["iri"] for entry in meta["unlinked"]], [str(node)])
        self.assertEqual(meta["deleted"], [])
        # Detached from this bundle, and still itself for the one that cites it.
        self.assertIsNone(find_part(self.stored(uid), uid, SCENARIO, sid))
        self.assertTrue(
            self.store.ask("ASK { %s a %s }" % (node.n3(), SCENARIO_CLASS.n3()))
        )


class ReplaceKeepsIdentityTest(ReplaceTestCase):
    """A re-import updates its parts. It does not churn them."""

    def test_a_scenario_that_names_itself_keeps_its_identifier(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)
        scenario = body["scenarios"][0]

        response = self.replace(
            uid,
            self.declared(body, scenarios=[{**scenario, "label": "Renamed"}]),
            etag,
        )

        self.assertEqual(response.status_code, 200, response.data)
        (kept,) = response.data["scenarios"]
        self.assertEqual(kept[READ_ONLY_CONTAINER]["uid"], sid)
        self.assertEqual(kept["label"], "Renamed")
        self.assertEqual(response.data[READ_ONLY_CONTAINER]["deleted"], [])

    def test_a_scenario_that_names_none_is_created_beside_it(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)

        response = self.replace(
            uid,
            self.declared(body, scenarios=[body["scenarios"][0], OTHER_SCENARIO]),
            etag,
        )

        identifiers = {
            one[READ_ONLY_CONTAINER]["uid"] for one in response.data["scenarios"]
        }
        self.assertIn(sid, identifiers)
        self.assertEqual(len(identifiers), 2)

    def test_an_identifier_this_bundle_does_not_have_is_refused(self):
        # Matched, never created from: an identifier that is not here means the
        # payload was built from a different bundle.
        uid, etag = self.created()
        body, _ = self.read_body(uid)
        stranger = {
            **VALID_SCENARIO,
            "_meta": {"uid": "9f1d6a0e-0000-0000-0000-000000000000"},
        }

        response = self.replace(uid, self.declared(body, scenarios=[stranger]), etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("no scenario", response.data["detail"].lower())

    def test_the_same_identifier_declared_twice_is_refused(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)
        scenario = body["scenarios"][0]

        response = self.replace(
            uid,
            self.declared(body, scenarios=[scenario, {**scenario, "label": "Other"}]),
            etag,
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("twice", response.data["detail"])

    def test_frameworks_are_not_re_minted_by_a_round_trip(self):
        # Frameworks and models are fields, not sub-resources, so a client has
        # no identifier to send back for one. Matching them by what they say is
        # what keeps a nightly re-import from rewriting every one of them.
        uid, etag = self.created(
            {**VALID_PAYLOAD, "frameworks": [{"label": "PyPSA", "iri": None}]}
        )
        before = self._framework_nodes(uid)
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self._framework_nodes(uid), before)

    def _framework_nodes(self, uid):
        graph = self.stored(uid)
        framework = OEO.OEO_00000172
        return {
            str(node)
            for node in graph.objects(bundle_iri(uid), None)
            if (node, RDF.type, framework) in graph
        }


class ReplaceIsIdempotentTest(ReplaceTestCase):
    """The second run of a pipeline costs nothing and records nothing."""

    def test_sending_back_what_was_read_writes_nothing(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response["ETag"], etag)
        self.assertEqual(response.data[READ_ONLY_CONTAINER]["version"], 1 + 1)

    def test_running_the_same_replace_twice_changes_nothing_the_second_time(self):
        uid, etag = self.created()
        body, etag = self.read_body(uid)
        first = self.replace(uid, self.declared(body, label="Declared"), etag)
        self.assertEqual(first.status_code, 200, first.data)

        second = self.replace(uid, self.declared(body, label="Declared"), first["ETag"])

        self.assertEqual(second.status_code, 200, second.data)
        self.assertEqual(second["ETag"], first["ETag"])

    def test_a_replace_that_changes_nothing_records_no_history_entry(self):
        # An entry with an empty diff would say a change happened. The point of
        # the endpoint is that it did not.
        uid, etag = self.created()
        body, etag = self.read_body(uid)
        before = OEKG_Modifications.objects.filter(bundle_id=uid).count()

        self.replace(uid, self.declared(body), etag)

        self.assertEqual(
            OEKG_Modifications.objects.filter(bundle_id=uid).count(), before
        )

    def test_a_replace_that_changes_nothing_reports_nothing_removed(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body), etag)

        meta = response.data[READ_ONLY_CONTAINER]
        self.assertEqual((meta["deleted"], meta["unlinked"]), ([], []))
        self.assertEqual(response.data["scenarios"][0][READ_ONLY_CONTAINER]["uid"], sid)


class ReplaceIsOneWriteTest(ReplaceTestCase):
    """One request to the store, one entry in the ledger. Never two."""

    def test_the_whole_operation_is_one_request_to_the_store(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)
        sent = []
        original = GraphStore.update

        def counting(store, update):
            sent.append(update)
            return original(store, update)

        GraphStore.update = counting
        try:
            response = self.replace(
                uid,
                self.declared(body, label="Declared", scenarios=[OTHER_SCENARIO]),
                etag,
            )
        finally:
            GraphStore.update = original

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(sent), 1, sent)

    def test_it_records_one_entry_with_a_real_diff(self):
        uid, etag = self.created()
        body, etag = self.read_body(uid)

        self.replace(uid, self.declared(body, label="Declared"), etag)

        entries = OEKG_Modifications.objects.filter(bundle_id=uid).order_by("id")
        self.assertEqual([entry.verb for entry in entries], ["POST", REPLACE])
        self.assertTrue(entries.last().added)
        self.assertTrue(entries.last().removed)

    def test_the_history_reads_the_replace_back_as_its_own_kind_of_write(self):
        # `REPLACE` is the one verb here that is not an HTTP method: `POST`
        # already means created in this column, and a reader auditing a
        # pipeline needs to see that the write was a declaration of the whole
        # bundle.
        uid, etag = self.created()
        body, etag = self.read_body(uid)
        self.replace(uid, self.declared(body, label="Declared"), etag)

        history = self.client.get(
            reverse("api:scenario-bundle-history", kwargs={"uid": uid})
        ).data

        self.assertEqual(history["results"][0]["verb"], REPLACE)
        self.assertIn(
            "label", [change["field"] for change in history["results"][0]["changes"]]
        )


class ReplaceRefusalsTest(ReplaceTestCase):
    """The same order every write in this API uses: exist, own, precondition."""

    def test_without_if_match_it_is_refused(self):
        uid, _ = self.created()
        body, _ = self.read_body(uid)

        response = self.replace(uid, self.declared(body))

        self.assertEqual(response.status_code, 428, response.data)

    def test_a_stale_precondition_is_refused(self):
        uid, etag = self.created()
        body, etag = self.read_body(uid)
        self.patch(uid, {"label": "Moved"}, if_match=etag)

        response = self.replace(uid, self.declared(body), etag)

        self.assertEqual(response.status_code, 412, response.data)

    def test_a_stranger_may_not_replace_a_bundle(self):
        uid, etag = self.created()
        body, etag = self.read_body(uid)

        response = self.replace(
            uid, self.declared(body), etag, as_user=self.other_user()
        )

        self.assertEqual(response.status_code, 403, response.data)

    def test_anonymously_it_is_refused(self):
        # `401` exactly, not "401 or 403": `BasicAuthentication` is first in
        # DEFAULT_AUTHENTICATION_CLASSES and supplies `WWW-Authenticate`, so
        # this API answers an anonymous write with `401`. Hedging both would
        # be defensive rather than evidence.
        uid, etag = self.created()
        body, etag = self.read_body(uid)
        self.client.logout()

        response = self.replace(uid, self.declared(body), etag, authenticate=False)

        self.assertEqual(response.status_code, 401, response.data)

    def test_a_bundle_that_is_not_there_answers_404(self):
        # Existence first, as everywhere: a replace is not a create, and a
        # pipeline that finds no bundle by acronym creates one with `POST`.
        response = self.replace(
            "9f1d6a0e-0000-0000-0000-000000000000", VALID_PAYLOAD, '"1"'
        )

        self.assertEqual(response.status_code, 404, response.data)

    def test_an_unknown_key_is_refused(self):
        uid, etag = self.created()
        body, _ = self.read_body(uid)

        response = self.replace(uid, self.declared(body, nonsense=1), etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("nonsense", response.data)

    def test_an_expansion_this_endpoint_does_not_offer_is_refused(self):
        uid, etag = self.created()
        body, _ = self.read_body(uid)
        self.client.force_login(self.user)

        response = self.client.post(
            self.replace_url(uid) + "?expand=nonsense",
            data=self.declared(body),
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

        self.assertEqual(response.status_code, 400, response.data)


class ReplaceIsNotOnTheBundleUrlTest(ReplaceTestCase):
    """Full replacement is named or it is not available."""

    def test_the_bundle_url_has_no_put(self):
        uid, etag = self.created()
        self.client.force_login(self.user)

        response = self.client.put(
            self.detail_url(uid),
            data=VALID_PAYLOAD,
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

        self.assertEqual(response.status_code, 405)

    def test_the_bundle_url_takes_no_post_either(self):
        uid, etag = self.created()
        self.client.force_login(self.user)

        response = self.client.post(
            self.detail_url(uid),
            data=VALID_PAYLOAD,
            content_type="application/json",
            HTTP_IF_MATCH=etag,
        )

        self.assertEqual(response.status_code, 405)


class ReplaceIsJudgedByWhatItIntroducesTest(ReplaceTestCase):
    """The rule every write here follows, asked of a payload that is the whole
    bundle."""

    def test_a_declaration_that_drops_a_required_field_is_refused(self):
        # Omission removes, and what it removed here is something the shape
        # requires -- so this declaration introduces the violation and answers
        # for it.
        uid, etag = self.created()
        body, etag = self.read_body(uid)
        declaration = self.declared(body)
        del declaration["sectors"]

        response = self.replace(uid, declaration, etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(response.data["violations"])

    def test_a_violation_the_bundle_already_carried_is_not_blamed_on_it(self):
        # Most bundles in the live graph do not conform. A replace that leaves
        # an inherited defect exactly as it found it is not this caller's to
        # answer for -- otherwise the fields a human would supply by declaring
        # them are unfixable through the API.
        uid, etag = self.created()
        self.store.update(
            self.store.guarded_modification(
                "%s a ?type" % bundle_iri(uid).n3(),
                delete=self._sector_triples(uid),
            )
        )
        body, etag = self.read_body(uid)
        declaration = self.declared(body, label="Declared anyway")
        declaration.pop("sectors", None)

        response = self.replace(uid, declaration, etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["label"], "Declared anyway")

    def _sector_triples(self, uid):
        graph = self.stored(uid)
        triples = Graph()
        for obj in graph.objects(bundle_iri(uid), OEO.OEO_00020439):
            triples.add((bundle_iri(uid), OEO.OEO_00020439, obj))
        return triples


class ReplaceAnswersForTheAcronymTest(ReplaceTestCase):
    """The lookup a stateless pipeline depends on has to stay unambiguous."""

    def test_declaring_an_acronym_another_bundle_holds_is_refused(self):
        uid, etag = self.created()
        self.created({**VALID_PAYLOAD, "acronym": "TAKEN"})
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body, acronym="TAKEN"), etag)

        self.assertEqual(response.status_code, 409, response.data)

    def test_the_bound_guard_refuses_on_its_own(self):
        # The friendly check in front is a separate request, so two writes can
        # both pass it. Mocking it away is what losing that race looks like
        # from inside the write -- and the guard bound into the update has to
        # refuse without it.
        uid, etag = self.created()
        self.created({**VALID_PAYLOAD, "acronym": "TAKEN"})
        body, etag = self.read_body(uid)

        with patch("oekg.replace_views.acronym_taken", return_value=False):
            response = self.replace(uid, self.declared(body, acronym="TAKEN"), etag)

        self.assertEqual(response.status_code, 409, response.data)
        # And nothing was written: the bundle still answers to its own acronym.
        self.assertEqual(self.read_body(uid)[0]["acronym"], "API-TEST")

    def test_declaring_the_acronym_it_already_has_is_not_a_conflict(self):
        # A bundle never counts against itself, or sending back what was read
        # would be refused by its own value.
        uid, etag = self.created()
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body, label="Renamed"), etag)

        self.assertEqual(response.status_code, 200, response.data)


class BundleReadNestsDatasetLinksTest(ReplaceTestCase):
    """A read has to mention everything a declaration is allowed to remove."""

    def test_a_bundle_read_nests_each_scenarios_dataset_links(self):
        uid, sid, did, _etag = self.with_one_link()

        body, _ = self.read_body(uid)

        (scenario,) = body["scenarios"]
        (link,) = scenario["datasets"]
        self.assertEqual(
            {key: link[key] for key in ("type", "ref", "name")}, TABLE_LINK
        )
        self.assertEqual(link[READ_ONLY_CONTAINER]["uid"], did)

    def test_a_nested_link_still_says_what_it_resolves_to(self):
        uid, sid, _did, _etag = self.with_one_link()

        body, _ = self.read_body(uid)

        link = body["scenarios"][0]["datasets"][0]
        self.assertIn("resolvable", link[READ_ONLY_CONTAINER])

    def test_a_scenarys_own_read_does_not_nest_them(self):
        # Two read shapes for one resource, because there are two write shapes:
        # at its own endpoint a link has its own URL.
        uid, sid, _did, _etag = self.with_one_link()

        read = self.client.get(self.scenario_url(uid, sid)).data

        self.assertNotIn("datasets", read)

    def test_a_bundle_is_created_with_its_scenarios_datasets_in_one_call(self):
        uid, _ = self.created(
            {
                **VALID_PAYLOAD,
                "scenarios": [{**VALID_SCENARIO, "datasets": [TABLE_LINK]}],
            }
        )

        body, _ = self.read_body(uid)

        (link,) = body["scenarios"][0]["datasets"]
        self.assertEqual(link["name"], TABLE_LINK["name"])


class TheWholePipelineStoryTest(ReplaceTestCase):
    """The loop the endpoint exists for, walked once end to end.

    A modelling pipeline keeps no state between runs: it looks its bundle up by
    acronym, creates it if there is none, and otherwise declares it. Each half
    is tested elsewhere; nothing pinned that they join up, and the join is the
    whole claim.
    """

    def by_acronym(self, acronym):
        return self.client.get(f"{self.collection_url}?acronym={acronym}").data

    def test_a_pipeline_holding_no_state_creates_then_declares(self):
        # Run one: nothing is there, so the pipeline creates.
        self.assertEqual(self.by_acronym("API-TEST")["count"], 0)
        self.created({**VALID_PAYLOAD, "scenarios": [VALID_SCENARIO]})

        # Run two: it finds the bundle again by acronym alone, and what it
        # finds carries the identifier and the version its next write needs.
        found = self.by_acronym("API-TEST")
        self.assertEqual(found["count"], 1)
        meta = found["results"][0][READ_ONLY_CONTAINER]
        uid, version = meta["uid"], meta["version"]

        body, _ = self.read_body(uid)
        response = self.replace(
            uid,
            self.declared(body, label="Declared by the pipeline"),
            f'"{version}"',
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["label"], "Declared by the pipeline")
        # Run three declares the same thing and writes nothing at all.
        again = self.replace(
            uid,
            self.declared(body, label="Declared by the pipeline"),
            response["ETag"],
        )
        self.assertEqual(again.status_code, 200, again.data)
        self.assertEqual(again["ETag"], response["ETag"])


class ReplaceKeepsDatasetLinksTest(ReplaceTestCase):
    """The test that would not have been written by accident -- issue #2473.

    Dataset links are bundle-local for the purposes of deletion, so the typed
    containment walk reaches them. They used to be absent from the bundle
    payload, so a declaration had no way to mention one. A replace built on
    that payload destroys every citation in the bundle **and passes the
    happy-path test anybody would write**: add a scenario, change a field,
    remove a scenario.
    """

    def test_the_happy_path_replace_does_not_destroy_a_citation(self):
        uid, sid, did, etag = self.with_one_link()
        body, etag = self.read_body(uid)

        response = self.replace(
            uid,
            self.declared(
                body,
                label="Declared afresh",
                scenarios=[body["scenarios"][0], OTHER_SCENARIO],
            ),
            etag,
        )

        self.assertEqual(response.status_code, 200, response.data)
        kept = [
            one for one in response.data["scenarios"] if one["acronym"] == "HIGH-RE"
        ]
        self.assertEqual(len(kept), 1, response.data["scenarios"])
        self.assertEqual(len(kept[0]["datasets"]), 1, kept[0])
        self.assertEqual(kept[0]["datasets"][0][READ_ONLY_CONTAINER]["uid"], did)
        self.assertEqual(response.data[READ_ONLY_CONTAINER]["deleted"], [])

    def test_a_link_the_declaration_omits_is_removed(self):
        # The other half of the same decision: because links are mentionable, a
        # pipeline has a declarative way to drop one.
        uid, sid, did, etag = self.with_one_link()
        body, etag = self.read_body(uid)
        scenario = {**body["scenarios"][0], "datasets": []}

        response = self.replace(uid, self.declared(body, scenarios=[scenario]), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["scenarios"][0]["datasets"], [])
        self.assertEqual(self.client.get(self.link_url(uid, sid, did)).status_code, 404)

    def test_a_link_the_declaration_adds_is_created(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)
        scenario = {**body["scenarios"][0], "datasets": [DATASET_LINK]}

        response = self.replace(uid, self.declared(body, scenarios=[scenario]), etag)

        self.assertEqual(response.status_code, 200, response.data)
        (link,) = response.data["scenarios"][0]["datasets"]
        self.assertEqual(link["name"], DATASET_LINK["name"])

    def test_a_link_declared_twice_on_one_scenario_is_refused(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)
        scenario = {**body["scenarios"][0], "datasets": [TABLE_LINK, TABLE_LINK]}

        response = self.replace(uid, self.declared(body, scenarios=[scenario]), etag)

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("twice", response.data["detail"])

    def test_removing_a_scenario_takes_its_links_with_it(self):
        uid, sid, did, etag = self.with_one_link()
        body, etag = self.read_body(uid)
        link_node = body["scenarios"][0]["datasets"][0][READ_ONLY_CONTAINER]["iri"]

        response = self.replace(uid, self.declared(body, scenarios=[]), etag)

        deleted = [
            entry["iri"] for entry in response.data[READ_ONLY_CONTAINER]["deleted"]
        ]
        self.assertIn(link_node, deleted)


class ReplaceRoundTripsAnExternalLinkTest(ExternalLinkMixin, ReplaceTestCase):
    """An address this platform has no route for is expressible, so it survives.

    Answering only the nesting question would have left a pipeline unable to
    send back a bundle holding a databus URL: `ref` read as null, the body was
    refused, the link was omitted, and the replace removed it.
    """

    def test_its_reference_kind_reads_back_as_external(self):
        uid, sid = self.with_an_external_link()

        read = self.client.get(self.link_url(uid, sid, "legacy")).data

        self.assertEqual(read["ref"], "external")
        self.assertEqual(read["url"], self.EXTERNAL)

    def test_a_bundle_holding_one_is_declared_back_unchanged(self):
        uid, sid = self.with_an_external_link()
        body, etag = self.read_body(uid)

        response = self.replace(uid, self.declared(body), etag)

        self.assertEqual(response.status_code, 200, response.data)
        (link,) = response.data["scenarios"][0]["datasets"]
        self.assertEqual(link["url"], self.EXTERNAL)
        self.assertEqual(response.data[READ_ONLY_CONTAINER]["deleted"], [])

    def test_an_external_link_can_be_declared_from_scratch(self):
        uid, sid, etag = self.with_one_scenario()
        body, etag = self.read_body(uid)
        scenario = {
            **body["scenarios"][0],
            "datasets": [
                {
                    "type": "input",
                    "ref": "external",
                    "name": "WS_23_24",
                    "url": self.EXTERNAL,
                }
            ],
        }

        response = self.replace(uid, self.declared(body, scenarios=[scenario]), etag)

        self.assertEqual(response.status_code, 200, response.data)
        (link,) = response.data["scenarios"][0]["datasets"]
        self.assertEqual(link["url"], self.EXTERNAL)
        self.assertIsNone(link[READ_ONLY_CONTAINER]["resolvable"])


class ReplaceLeavesWhatItCannotExpressTest(ReplaceTestCase):
    """Silence about something a client cannot send is not permission to delete.

    The boundary of delete-by-omission: the bundle's own field predicates and
    its bundle-local nodes. A predicate no field table names -- and the live
    graph has several, written by the browser -- is outside what this API can
    show its caller, so a declaration says nothing about it either way.
    """

    def test_a_predicate_no_field_names_survives_a_replace(self):
        uid, etag = self.created()
        stray = Graph()
        stray.add((bundle_iri(uid), OEO.OEO_00000000, URIRef("urn:oep:something")))
        self.store.insert(stray)
        body, etag = self.read_body(uid)

        self.replace(uid, self.declared(body, label="Declared"), etag)

        self.assertTrue(
            self.store.ask(
                "ASK { %s %s <urn:oep:something> }"
                % (bundle_iri(uid).n3(), OEO.OEO_00000000.n3())
            )
        )

    def test_a_shared_node_the_declaration_drops_keeps_its_own_triples(self):
        uid, etag = self.created({**VALID_PAYLOAD, "contacts": [{"label": "A person"}]})
        body, etag = self.read_body(uid)
        contact = URIRef(body["contacts"][0]["iri"])

        response = self.replace(uid, self.declared(body, contacts=[]), etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["contacts"], [])
        self.assertTrue(
            self.store.ask("ASK { %s %s ?label }" % (contact.n3(), RDFS.label.n3()))
        )
        # And it is not reported: every write here detaches shared nodes, so
        # listing them would bury the line that is news under the rule that
        # always applies.
        self.assertEqual(response.data[READ_ONLY_CONTAINER]["unlinked"], [])
