"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import subprocess
import sys
import uuid

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDFS

from oekg.graph_store import (
    GraphStore,
    GraphStoreUnavailable,
    GraphUpdateRejected,
    UnsafeClearError,
)
from oekg.tests import OekgGraphTestCase

EX = "https://example.org/oekg-test/"

# Port 9 is the discard service: a connection there is always refused, so LOAD
# fails while the update is RUNNING. A parse error would prove nothing about
# transactions, because the request would never execute.
UNREACHABLE = "http://127.0.0.1:9/nonexistent.ttl"


def triple(subject, label):
    graph = Graph()
    graph.add((URIRef(subject), RDFS.label, Literal(label)))
    return graph


class GraphStoreConfigurationTest(SimpleTestCase):
    """What the store is, without needing one to be running."""

    @override_settings(
        RDF_DATABASES={
            "knowledge": {
                "host": "graphs.example.org",
                "port": "3030",
                "name": "ds",
                "user": "someone",
                "password": "secret",
            }
        }
    )
    def test_it_is_built_from_the_platform_settings(self):
        store = GraphStore.from_settings()

        self.assertEqual(store.query_url, "http://graphs.example.org:3030/ds/query")
        self.assertEqual(store.update_url, "http://graphs.example.org:3030/ds/update")
        self.assertEqual(store.auth, ("someone", "secret"))
        self.assertIsNone(store.graph)

    @override_settings(
        RDF_DATABASES={
            "knowledge": {
                "host": "graphs.example.org",
                "port": "3030",
                "name": "ds",
                "user": "",
                "password": "",
            }
        }
    )
    def test_credentials_are_optional(self):
        self.assertIsNone(GraphStore.from_settings().auth)

    def test_an_unreachable_store_is_reported_not_raised(self):
        store = GraphStore(
            query_url="http://127.0.0.1:9/ds/query",
            update_url="http://127.0.0.1:9/ds/update",
        )

        self.assertFalse(store.is_available())

    def test_reading_from_an_unreachable_store_raises_unavailable(self):
        store = GraphStore(
            query_url="http://127.0.0.1:9/ds/query",
            update_url="http://127.0.0.1:9/ds/update",
        )

        with self.assertRaises(GraphStoreUnavailable):
            store.ask("ASK { ?s ?p ?o }")

    def test_clearing_the_default_graph_is_refused(self):
        # A test helper that could DROP the default graph is one misconfigured
        # endpoint away from erasing the production knowledge graph.
        store = GraphStore(
            query_url="http://localhost:3030/ds/query",
            update_url="http://localhost:3030/ds/update",
            graph=None,
        )

        with self.assertRaises(UnsafeClearError):
            store.clear()

    def test_importing_the_transport_does_not_drag_in_the_ontology(self):
        # factsheet/oekg/connection.py parses the full OEO at import: 1.3 GB
        # resident and ~36 s, per process. The API's transport must not reach
        # it, directly or through oekg/sparqlQuery.py which does import it.
        #
        # Checked in a fresh interpreter on purpose: by the time the suite runs,
        # the factsheet tests have already imported that module here.
        probe = (
            "import sys, oekg.graph_store;"
            "print(any(m.startswith('factsheet') or m == 'owlready2'"
            " for m in sys.modules))"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(settings.BASE_DIR),
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False", result.stderr)


class GraphStoreReadWriteTest(OekgGraphTestCase):
    """Against a real store, in this test's own graph."""

    def test_a_write_is_readable_afterwards(self):
        subject = EX + str(uuid.uuid4())

        self.store.insert(triple(subject, "written and read back"))

        rows = self.store.select(
            "SELECT ?label WHERE { <%s> <%s> ?label }" % (subject, RDFS.label)
        )
        self.assertEqual([row["label"] for row in rows], ["written and read back"])

    def test_a_construct_returns_the_triples_that_were_written(self):
        subject = URIRef(EX + str(uuid.uuid4()))

        self.store.insert(triple(subject, "constructed"))

        graph = self.store.construct(
            "CONSTRUCT { <%s> ?p ?o } WHERE { <%s> ?p ?o }" % (subject, subject)
        )
        self.assertEqual(list(graph), [(subject, RDFS.label, Literal("constructed"))])

    def test_the_graph_starts_empty(self):
        # Holds whatever order the suite runs in, because every test cleans up
        # after itself rather than before.
        self.assertEqual(self.store.select("SELECT ?s WHERE { ?s ?p ?o }"), [])

    def test_clearing_removes_everything_this_test_wrote(self):
        self.store.insert(triple(EX + "leak-check", "written by one test"))

        self.store.clear()

        self.assertEqual(self.store.select("SELECT ?s WHERE { ?s ?p ?o }"), [])

    def test_a_store_that_only_reads_is_not_available(self):
        # Fuseki answers queries to anyone and 401s updates without valid
        # credentials. A probe that only read would call such a store usable
        # and leave every write test failing instead of skipping.
        read_only = GraphStore(
            query_url=self.store.query_url,
            update_url=self.store.update_url,
            auth=("definitely", "wrong"),
        )

        self.assertTrue(read_only.ask("ASK { }"))
        self.assertFalse(read_only.is_available())

    def test_a_rejected_update_does_not_leak_the_store_response(self):
        # Fuseki answers a bad query with a parser dump that echoes the
        # generated query back. That must never reach a client.
        with self.assertRaises(GraphUpdateRejected) as caught:
            self.store.update("THIS IS NOT SPARQL")

        message = str(caught.exception)
        self.assertNotIn("THIS IS NOT SPARQL", message)
        self.assertNotIn("Encountered", message)


class OneRequestIsOneTransactionTest(OekgGraphTestCase):
    """The measured claim the whole write path rests on.

    WF-04 established it against Fuseki 5.1.0 on TDB2 in a prototype; it lives
    in the suite now, so a store upgrade cannot quietly take it away.
    """

    def wrote(self, subject):
        return self.store.ask("ASK { <%s> ?p ?o }" % subject)

    def test_a_failure_after_a_write_rolls_the_write_back(self):
        subject = EX + str(uuid.uuid4())

        with self.assertRaises(GraphUpdateRejected):
            self.store.update(
                self.store.insert_data(triple(subject, "should not survive")),
                "LOAD <%s>" % UNREACHABLE,
            )

        self.assertFalse(self.wrote(subject))

    def test_a_failure_before_a_write_stops_it_landing(self):
        subject = EX + str(uuid.uuid4())

        with self.assertRaises(GraphUpdateRejected):
            self.store.update(
                "LOAD <%s>" % UNREACHABLE,
                self.store.insert_data(triple(subject, "should never land")),
            )

        self.assertFalse(self.wrote(subject))

    def test_the_same_two_as_separate_requests_do_not_roll_back(self):
        # The control. Without it the two tests above would also pass against a
        # store that simply refused every update.
        subject = EX + str(uuid.uuid4())

        self.store.insert(triple(subject, "survives, because this is committed"))
        with self.assertRaises(GraphUpdateRejected):
            self.store.update("LOAD <%s>" % UNREACHABLE)

        self.assertTrue(self.wrote(subject))

    def test_several_writes_in_one_request_all_land(self):
        subjects = [EX + str(uuid.uuid4()) for _ in range(3)]

        self.store.update(
            *[self.store.insert_data(triple(s, "batched")) for s in subjects]
        )

        for subject in subjects:
            self.assertTrue(self.wrote(subject))
