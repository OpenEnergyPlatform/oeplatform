"""Every write leaves a record, and the record reads back.

Two properties carry this slice, and both are easy to lose:

- **The record is complete.** Today only the user interface's update path
  records anything; creates, deletes and every API write are silent. The rule
  here is "the history is the log of writes", with no per-operation judgement
  to make or to get wrong.
- **The graph is the truth and the history is the note about it.** They cannot
  share a transaction, so the graph commits first and a failed history write
  still answers success -- the gap is named in the response and in the log
  rather than hidden, because a phantom entry would be worse.

The stored diff is lossless and untranslated; field names are computed at read
time, so a later shape change never re-interprets an old row.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
from unittest.mock import patch

from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDFS

from factsheet.models import API_ERA, PRE_API_ERA, OEKG_Modifications
from login.models import myuser
from oekg.bundles import BUNDLE_CLASS, DC, HAS_PART, OEO, bundle_iri
from oekg.history import CREATE, UPDATE, changed_fields, record_write
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.bundle_fixtures import VALID_PAYLOAD, BundleApiTestCase


class HistoryTestCase(BundleApiTestCase):
    def history_url(self, uid):
        return reverse("api:scenario-bundle-history", kwargs={"uid": uid})

    def entries(self, uid):
        return list(OEKG_Modifications.objects.filter(bundle_id=uid).order_by("id"))

    def read_history(self, uid, **params):
        return self.client.get(self.history_url(uid), params)


class EveryWriteRecordsTest(HistoryTestCase):
    def test_a_create_writes_one_entry(self):
        uid, _ = self.created()

        entries = self.entries(uid)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].verb, CREATE)
        self.assertEqual(entries[0].user, self.user)

    def test_a_create_records_the_version_it_produced(self):
        # A timestamp cannot answer "which change produced this state"; the
        # version pair can.
        uid, _ = self.created()

        entry = self.entries(uid)[0]

        self.assertEqual(entry.version_before, 0)
        self.assertEqual(entry.version_after, 1)

    def test_a_patch_writes_one_entry(self):
        uid, etag = self.created()

        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        entries = self.entries(uid)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[1].verb, UPDATE)
        self.assertEqual((entries[1].version_before, entries[1].version_after), (1, 2))

    def test_an_entry_names_the_resource_it_touched(self):
        uid, _ = self.created()

        entry = self.entries(uid)[0]

        self.assertEqual(entry.resource_type, str(BUNDLE_CLASS))
        self.assertIsNone(entry.resource_uuid)

    def test_a_refused_write_records_nothing(self):
        uid, etag = self.created()

        self.patch(uid, {"technologies": []}, if_match=etag)

        self.assertEqual(len(self.entries(uid)), 1)

    def test_entries_are_written_as_the_api_era(self):
        uid, _ = self.created()

        self.assertEqual(self.entries(uid)[0].era, API_ERA)


class TheStoredDiffTest(HistoryTestCase):
    def test_a_patch_stores_what_changed_and_nothing_else(self):
        uid, etag = self.created()

        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        entry = self.entries(uid)[1]
        self.assertEqual(self.labels_in(entry.removed), [VALID_PAYLOAD["label"]])
        self.assertEqual(self.labels_in(entry.added), ["Renamed"])

    def test_a_create_stores_the_whole_bundle_as_added(self):
        uid, _ = self.created()

        entry = self.entries(uid)[0]

        self.assertIn(VALID_PAYLOAD["label"], self.labels_in(entry.added))
        self.assertEqual(self.triples_in(entry.removed), 0)

    def test_the_payload_is_real_json_and_not_a_string(self):
        # The pre-API rows hold a JSON-LD *string* inside a JSON column. New
        # rows do not repeat that: the column holds structured data.
        uid, _ = self.created()

        self.assertNotIsInstance(self.entries(uid)[0].added, str)

    def test_the_legacy_columns_stay_empty_on_an_api_row(self):
        # Empty and not null. Writing a second representation into them would
        # break the diff viewer that reads them as strings -- and so would a
        # null, which is why these are "" rather than None.
        uid, _ = self.created()

        entry = self.entries(uid)[0]
        self.assertEqual(entry.old_state, "")
        self.assertEqual(entry.new_state, "")

    def test_an_api_row_survives_the_existing_diff_viewer(self):
        # That viewer renders every row of the global dump in one pass and
        # hands both columns to a component that splits them, so one row of a
        # type it cannot take would blank the whole page.
        uid, _ = self.created()

        entry = self.entries(uid)[0]
        for value in (entry.old_state, entry.new_state):
            self.assertIsInstance(value, str)

    def test_the_stored_diff_round_trips_as_triples(self):
        # Lossless: what was stored parses back to the triples that changed.
        uid, etag = self.created()
        self.patch(uid, {"abstract": "Ein anderer Text"}, if_match=etag)

        added = self.graph_of(self.entries(uid)[1].added)

        self.assertIn(
            (bundle_iri(uid), DC.abstract, Literal("Ein anderer Text")), added
        )

    def graph_of(self, payload):
        # The column holds structured JSON, not a JSON-LD document, so it has
        # to be re-serialised to be parsed. That is the property under test.
        graph = Graph()
        if payload:
            graph.parse(data=json.dumps(payload), format="json-ld")
        return graph

    def labels_in(self, payload):
        return [str(o) for o in self.graph_of(payload).objects(None, RDFS.label)]

    def triples_in(self, payload):
        return len(self.graph_of(payload))


class RenderedChangesTest(HistoryTestCase):
    def test_the_summary_names_the_field_that_changed(self):
        uid, etag = self.created()
        self.patch(uid, {"abstract": "Ein anderer Text"}, if_match=etag)

        entry = self.read_history(uid).data["results"][0]

        changed = {change["field"] for change in entry["changes"]}
        self.assertIn("abstract", changed)

    def test_the_summary_carries_the_values_on_both_sides(self):
        uid, etag = self.created()
        self.patch(uid, {"abstract": "Ein anderer Text"}, if_match=etag)

        changes = self.read_history(uid).data["results"][0]["changes"]

        abstract = next(c for c in changes if c["field"] == "abstract")
        self.assertEqual(abstract["removed"], [VALID_PAYLOAD["abstract"]])
        self.assertEqual(abstract["added"], ["Ein anderer Text"])

    def test_the_summary_matches_the_stored_triples(self):
        # The rendering is computed from the diff at read time, so it cannot
        # drift from it -- this is the test that says so.
        uid, etag = self.created()
        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        entry = self.read_history(uid, expand="triples").data["results"][0]

        rendered = next(c for c in entry["changes"] if c["field"] == "label")
        stored = Graph()
        stored.parse(data=json.dumps(entry["triples"]["added"]), format="json-ld")
        self.assertEqual(
            rendered["added"], [str(o) for o in stored.objects(None, RDFS.label)]
        )

    def test_a_triple_that_names_no_field_is_reported_rather_than_dropped(self):
        # A minted contact brings its own type and label with it. Those are not
        # bundle fields, and silently dropping them would make the summary look
        # complete when it is not.
        uid, etag = self.created()

        self.patch(uid, {"contacts": [{"label": "A contact"}]}, if_match=etag)

        changes = self.read_history(uid).data["results"][0]["changes"]
        self.assertTrue(any(change["field"] is None for change in changes))
        self.assertTrue(any(change["field"] == "contacts" for change in changes))

    def test_the_triples_are_only_returned_when_asked_for(self):
        uid, _ = self.created()

        self.assertNotIn("triples", self.read_history(uid).data["results"][0])
        self.assertIn(
            "triples", self.read_history(uid, expand="triples").data["results"][0]
        )

    def test_an_unknown_expansion_is_refused(self):
        uid, _ = self.created()

        response = self.read_history(uid, expand="everything")

        self.assertEqual(response.status_code, 400, response.data)


class HistoryReadTest(HistoryTestCase):
    def test_the_history_is_public(self):
        uid, _ = self.created()
        self.client.logout()

        self.assertEqual(self.read_history(uid).status_code, 200)

    def test_the_actor_is_a_username_and_not_an_internal_identifier(self):
        uid, _ = self.created()

        entry = self.read_history(uid).data["results"][0]

        self.assertEqual(entry["actor"], self.user.name)
        self.assertNotIn(str(self.user.pk), str(entry["actor"]))

    def test_the_newest_change_comes_first(self):
        uid, etag = self.created()
        self.patch(uid, {"label": "Renamed"}, if_match=etag)

        results = self.read_history(uid).data["results"]

        self.assertEqual([entry["verb"] for entry in results], [UPDATE, CREATE])

    def test_it_is_paginated(self):
        uid, etag = self.created()
        for number in range(1, 4):
            etag = self.patch(uid, {"label": f"Rename {number}"}, if_match=etag)["ETag"]

        page = self.read_history(uid, page_size=2)

        self.assertEqual(len(page.data["results"]), 2)
        self.assertEqual(page.data["count"], 4)
        self.assertIsNotNone(page.data["next"])

    def test_a_page_size_beyond_the_ceiling_is_capped(self):
        # A public endpoint with an unbounded mode is a dump waiting to happen.
        uid, _ = self.created()

        page = self.read_history(uid, page_size=100000)

        self.assertLessEqual(len(page.data["results"]), 100)

    def test_it_shows_only_this_bundle(self):
        first, _ = self.created()
        second, _ = self.created({**VALID_PAYLOAD, "acronym": "OTHER"})

        results = self.read_history(first).data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(self.read_history(second).data["count"], 1)

    def test_an_unknown_bundle_is_a_404(self):
        response = self.read_history("11111111-2222-3333-4444-555555555555")

        self.assertEqual(response.status_code, 404)

    def test_an_identifier_that_is_not_minted_is_a_404(self):
        self.assertEqual(self.read_history("not-a-uuid").status_code, 404)


class LegacyRowTest(HistoryTestCase):
    """Rows the user interface wrote, which are not migrated."""

    def legacy_row(self, uid):
        return OEKG_Modifications.objects.create(
            bundle_id=uid,
            user=self.user,
            old_state='{"@graph": []}',
            new_state='{"@graph": []}',
        )

    def test_a_legacy_row_reads_as_the_era_it_came_from(self):
        uid, _ = self.created()
        self.legacy_row(uid)

        eras = {entry["era"] for entry in self.read_history(uid).data["results"]}

        self.assertEqual(eras, {API_ERA, PRE_API_ERA})

    def test_a_legacy_row_claims_no_field_level_summary(self):
        # Null rather than an empty list: an empty list would claim that
        # nothing changed, which is not what is known about these rows.
        uid, _ = self.created()
        self.legacy_row(uid)

        entry = next(
            e for e in self.read_history(uid).data["results"] if e["era"] == PRE_API_ERA
        )

        self.assertIsNone(entry["changes"])
        self.assertIsNone(entry["verb"])

    def test_a_legacy_row_keeps_its_double_encoded_payload(self):
        uid, _ = self.created()
        row = self.legacy_row(uid)

        row.refresh_from_db()

        self.assertIsInstance(row.old_state, str)


class HistoryWriteFailureTest(HistoryTestCase):
    """The graph is the truth; the history is the note about it."""

    def failing_history(self):
        return patch(
            "oekg.history.OEKG_Modifications.objects.create",
            side_effect=DatabaseError("no room at the inn"),
        )

    def test_a_create_still_succeeds(self):
        with self.failing_history():
            response = self.create()

        self.assertEqual(response.status_code, 201, response.data)
        uid = response.data[READ_ONLY_CONTAINER]["uid"]
        self.assertEqual(self.client.get(self.detail_url(uid)).status_code, 200)

    def test_the_gap_is_named_in_the_response(self):
        with self.failing_history():
            response = self.create()

        self.assertFalse(response.data[READ_ONLY_CONTAINER]["history_recorded"])

    def test_a_patch_still_succeeds_and_names_the_gap(self):
        uid, etag = self.created()

        with self.failing_history():
            response = self.patch(uid, {"label": "Renamed"}, if_match=etag)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data[READ_ONLY_CONTAINER]["history_recorded"])
        self.assertEqual(self.client.get(self.detail_url(uid)).data["label"], "Renamed")

    def test_a_successful_write_does_not_claim_a_gap(self):
        # The key is only there when there is something to say; a client should
        # not have to check it on every response.
        response = self.create()

        self.assertNotIn("history_recorded", response.data[READ_ONLY_CONTAINER])

    def test_the_failure_is_logged(self):
        with self.failing_history():
            with self.assertLogs("oeplatform.oekg_history", level="ERROR") as logs:
                self.create()

        self.assertIn("oekg_history", logs.output[0])
        self.assertIn("outcome=not_recorded", logs.output[0])


class RealHistoryFailureTest(TestCase):
    """A real database error, not a mocked one.

    Mocking the insert proves the caller handles a raised exception; it cannot
    prove the transaction survives it. Only a genuine rejection does that, and
    without the savepoint the next query raises instead -- which would turn a
    write that succeeded into a 500.
    """

    def test_a_rejected_row_does_not_poison_the_transaction(self):
        user = myuser.objects.create_user(
            name="history-author", email="history@example.org", affiliation=""
        )

        recorded = record_write(
            bundle_uid="x" * 401,  # longer than the column
            verb=CREATE,
            actor=user,
            version_before=0,
            version_after=1,
        )

        self.assertFalse(recorded)
        # The connection is still usable. This is the assertion the savepoint
        # exists for; without it this line raises TransactionManagementError.
        self.assertEqual(OEKG_Modifications.objects.count(), 0)


class ChangedFieldsTest(SimpleTestCase):
    """The renderer, without a store."""

    def test_a_bundle_predicate_becomes_its_field_name(self):
        removed, added = Graph(), Graph()
        added.add((bundle_iri("u1"), DC.abstract, Literal("neu")))

        changes = changed_fields("u1", removed, added)

        self.assertEqual(
            changes,
            [
                {
                    "field": "abstract",
                    "predicate": str(DC.abstract),
                    "removed": [],
                    "added": ["neu"],
                }
            ],
        )

    def test_both_sides_of_one_field_are_one_change(self):
        removed, added = Graph(), Graph()
        removed.add((bundle_iri("u1"), DC.abstract, Literal("alt")))
        added.add((bundle_iri("u1"), DC.abstract, Literal("neu")))

        changes = changed_fields("u1", removed, added)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["removed"], ["alt"])

    def test_a_shared_predicate_is_told_apart_by_the_type_in_the_diff(self):
        # Frameworks and models both hang off has-part, so the predicate alone
        # cannot name the field. An added part carries its type in the same
        # diff, and that decides it.
        added = Graph()
        node = URIRef("https://example.org/m1")
        added.add((bundle_iri("u1"), HAS_PART, node))
        added += _typed(node, OEO.OEO_00000277)

        named = {change["field"] for change in changed_fields("u1", Graph(), added)}

        self.assertIn("models", named)
        self.assertNotIn("frameworks", named)

    def test_an_unlinked_part_is_reported_as_unknown_rather_than_guessed(self):
        # A patch unlinks and never deletes, so a removed part brings no type
        # with it and the field is honestly not knowable. Guessing one of the
        # two would put the change under the wrong heading.
        removed = Graph()
        removed.add((bundle_iri("u1"), HAS_PART, URIRef("https://example.org/m1")))

        named = {change["field"] for change in changed_fields("u1", removed, Graph())}

        self.assertEqual(named, {None})

    def test_a_triple_about_another_subject_names_no_field(self):
        added = Graph()
        added.add((URIRef("https://example.org/c1"), RDFS.label, Literal("A contact")))

        changes = changed_fields("u1", Graph(), added)

        self.assertEqual(changes[0]["field"], None)

    def test_an_unattributed_change_still_says_what_it_was_about(self):
        # A bare list of values with no predicate would be barely better than
        # dropping them.
        added = Graph()
        added.add((URIRef("https://example.org/c1"), RDFS.label, Literal("A contact")))

        changes = changed_fields("u1", Graph(), added)

        self.assertEqual(changes[0]["predicate"], str(RDFS.label))

    def test_nothing_changed_renders_as_nothing(self):
        self.assertEqual(changed_fields("u1", Graph(), Graph()), [])


class RecordWriteTest(SimpleTestCase):
    def test_it_refuses_to_guess_a_verb(self):
        with self.assertRaises(ValueError):
            record_write(
                bundle_uid="u1",
                verb="PUT",
                actor=None,
                version_before=1,
                version_after=2,
            )


def _typed(node, node_class):
    from rdflib import RDF

    graph = Graph()
    graph.add((node, RDF.type, node_class))
    graph.add((node, RDFS.label, Literal("A part")))
    return graph
