"""Test support for the OEKG app.

`OekgGraphTestCase` is the seam the OEKG REST API's tests are written against:
a **real** graph store, because the properties that matter here -- above all
that one update request is one transaction -- are properties of the engine, not
of a substitute. An in-memory stand-in would pass whatever we taught it.

The two rules that make that affordable:

- **Each test gets its own named graph**, dropped afterwards, so tests neither
  see nor disturb each other's triples and none of them touch the default graph
  the platform actually uses.
- **A missing store skips, it does not fail.** A developer without the compose
  network gets a green run. The reason is stated, so a skip never reads as
  "these tests do not exist".

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import unittest
import uuid

from django.test import SimpleTestCase

from oekg.graph_store import GraphStore

TEST_GRAPH_PREFIX = "urn:oep:test:"


class OekgGraphTestCase(SimpleTestCase):
    """A test with an isolated graph on a real store, or a stated skip."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        probe = GraphStore.from_settings()
        if not probe.is_available():
            raise unittest.SkipTest(
                f"The OEKG graph store at {probe.update_url} is not available "
                "for reading and writing. Start the compose network, or point "
                "RDF_DATABASE_HOST / RDF_DATABASE_USER / RDF_DATABASE_PASSWORD "
                "at a running Fuseki, to run the graph tests."
            )

    def setUp(self):
        super().setUp()
        self.store = GraphStore.from_settings(
            graph=TEST_GRAPH_PREFIX + str(uuid.uuid4())
        )
        # Cleaning up afterwards rather than beforehand is what lets every test
        # assert on an empty graph without depending on execution order.
        self.addCleanup(self.store.clear)
