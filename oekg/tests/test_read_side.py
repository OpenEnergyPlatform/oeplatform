"""What a read returns beyond the default representation.

Two rules are under test here and they pull against each other on purpose:

- **The default representation is exactly what a write accepts.** Resolution
  is opt-in, so a client can read, edit and send back without stripping
  anything -- the property `replace` is built on.
- **Everything read-only is in one container**, so the payload's top level maps
  onto the closed shape and the enforcement stays structural.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from oekg.fields import OEO
from oekg.labels import LABELS, picked_terms, term_labels
from oekg.serializers import READ_ONLY_CONTAINER
from oekg.tests.bundle_fixtures import VALID_PAYLOAD
from oekg.tests.test_dataset_link_api import DatasetLinkTestCase
from oekg.tests.test_scenario_api import VALID_SCENARIO


class ReadSideTestCase(DatasetLinkTestCase):
    """A bundle with a scenario and a dataset link -- one of everything."""

    def read(self, url, **params):
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def labels_of(self, body):
        return body[READ_ONLY_CONTAINER][LABELS]


class ExpandLabelsTest(ReadSideTestCase):
    def test_a_bundle_read_resolves_the_terms_it_picks(self):
        uid, _ = self.created()

        body = self.read(self.detail_url(uid), expand=LABELS)

        self.assertEqual(self.labels_of(body)[VALID_PAYLOAD["sectors"][0]], "sector")

    def test_every_picked_term_is_a_key(self):
        # A client should never have to tell "no label for this term" from
        # "labels were not resolved".
        uid, _ = self.created()

        labels = self.labels_of(self.read(self.detail_url(uid), expand=LABELS))

        picked = set()
        for field in ("descriptors", "sector_divisions", "sectors", "technologies"):
            picked.update(VALID_PAYLOAD[field])
        self.assertEqual(set(labels), picked)

    def test_resolution_is_off_by_default(self):
        uid, _ = self.created()

        self.assertNotIn(LABELS, self.read(self.detail_url(uid))[READ_ONLY_CONTAINER])

    def test_the_payload_still_carries_the_iris_it_was_written_with(self):
        # Resolution must not replace what a write accepts: the top level has
        # to go back to the server unchanged.
        uid, _ = self.created()

        body = self.read(self.detail_url(uid), expand=LABELS)

        self.assertEqual(body["sectors"], VALID_PAYLOAD["sectors"])

    def test_the_resolved_read_is_still_accepted_back_as_a_create(self):
        # The round trip, with the expansion in it: `_meta` is ignored on a
        # write, so a client sends back what it read without stripping.
        uid, _ = self.created()
        body = self.read(self.detail_url(uid), expand=LABELS)

        response = self.create({**body, "acronym": "ROUND-TRIPPED"})

        self.assertEqual(response.status_code, 201, response.data)

    def test_a_nested_scenario_resolves_its_own_picks(self):
        uid, _ = self.created({**VALID_PAYLOAD, "scenarios": [VALID_SCENARIO]})

        body = self.read(self.detail_url(uid), expand=LABELS)

        self.assertIn(
            VALID_SCENARIO["scenario_types"][0], self.labels_of(body["scenarios"][0])
        )

    def test_a_scenario_read_at_its_own_url_resolves_too(self):
        uid, sid, _ = self.with_one_scenario()

        body = self.read(self.scenario_url(uid, sid), expand=LABELS)

        self.assertEqual(
            self.labels_of(body)[VALID_SCENARIO["scenario_types"][0]],
            "scenario",
        )

    def test_a_dataset_link_picks_no_terms_and_says_so(self):
        # Asking a resource with no picked terms to resolve them is a
        # reasonable question with an empty answer, not a refusal.
        uid, sid, did, _ = self.with_one_link()

        body = self.read(self.link_url(uid, sid, did), expand=LABELS)

        self.assertEqual(self.labels_of(body), {})

    def test_a_term_the_subset_has_no_label_for_reads_as_null(self):
        self.assertEqual(
            term_labels(["https://example.org/not-a-term"]),
            {"https://example.org/not-a-term": None},
        )

    def test_only_enumerated_fields_count_as_picked_terms(self):
        # A minted contact's IRI is not an ontology term and is not in the
        # subset, so resolving it would put a permanent null in every answer.
        from oekg.bundles import BUNDLE_FIELDS

        picked = picked_terms(
            {
                "sectors": [str(OEO.OEO_00000367)],
                "contacts": [{"iri": "https://example.org/someone", "label": "S"}],
            },
            BUNDLE_FIELDS,
        )

        self.assertEqual(picked, [str(OEO.OEO_00000367)])


class UnknownExpansionTest(ReadSideTestCase):
    """An expansion nobody offers is refused, like an unknown key on a write."""

    def test_an_unknown_value_is_refused_on_a_bundle_read(self):
        uid, _ = self.created()

        response = self.client.get(self.detail_url(uid), {"expand": "lables"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("lables", response.data["detail"])

    def test_an_unknown_value_is_refused_on_a_scenario_read(self):
        uid, sid, _ = self.with_one_scenario()

        response = self.client.get(self.scenario_url(uid, sid), {"expand": "all"})

        self.assertEqual(response.status_code, 400)

    def test_an_unknown_value_is_refused_on_a_history_read(self):
        uid, _ = self.created()

        response = self.client.get(
            reverse("api:scenario-bundle-history", kwargs={"uid": uid}),
            {"expand": "everything"},
        )

        self.assertEqual(response.status_code, 400)

    def test_the_listing_offers_no_expansion_at_all(self):
        # A summary is what the listing is for. An expanded listing would put
        # the expensive path on the public endpoint.
        response = self.client.get(self.collection_url, {"expand": LABELS})

        self.assertEqual(response.status_code, 400)

    def test_asking_for_nothing_is_not_asking_for_something_unknown(self):
        uid, _ = self.created()

        self.assertEqual(
            self.client.get(self.detail_url(uid), {"expand": ""}).status_code, 200
        )


class ReadOnlyContainerTest(ReadSideTestCase):
    """It is on every object, so no client needs an existence check."""

    def test_every_object_a_read_returns_carries_one(self):
        uid, sid, did, _ = self.with_one_link()

        bundle = self.read(self.detail_url(uid))

        self.assertIn(READ_ONLY_CONTAINER, bundle)
        self.assertIn(READ_ONLY_CONTAINER, bundle["scenarios"][0])
        self.assertIn(READ_ONLY_CONTAINER, self.read(self.scenario_url(uid, sid)))
        self.assertIn(READ_ONLY_CONTAINER, self.read(self.link_url(uid, sid, did)))

    def test_it_is_there_on_a_collection_entry_too(self):
        uid, sid, did, _ = self.with_one_link()

        for url in (self.collection_url, self.links_url(uid, sid)):
            self.assertIn(READ_ONLY_CONTAINER, self.read(url)["results"][0], url)
