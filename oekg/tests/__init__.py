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
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings

from oekg.graph_store import GraphStore

TEST_GRAPH_PREFIX = "urn:oep:test:"

# These tests WRITE. They only ever write their own named graph, but a store is
# whatever RDF_DATABASE_HOST points at -- and a developer's securitysettings.py
# is a local file that could point anywhere. So the suite runs against a store
# it can recognise as local, and skips otherwise rather than writing to a
# stranger's graph. The repo's precedent for touching production deliberately is
# an explicit flag (--i-am-a-human-confirming-production); there is no reason a
# test run should have a quieter one.
LOCAL_GRAPH_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "[::1]", "fuseki"})


class RequiresShapeArtifactsMixin:
    """Skips unless the fetched shape artifacts are on disk.

    Same bargain as the graph store: a developer who has not run
    `manage.py fetch_oekg_shapes` gets a stated skip rather than a wall of
    failures. CI runs the command, so there the tests always execute.
    """

    @classmethod
    def setUpClass(cls):
        for setting in ("OEKG_SHAPES_PATH", "OEKG_SHAPE_LABELS_PATH"):
            path = Path(getattr(settings, setting))
            if not path.is_file():
                raise unittest.SkipTest(
                    f"The OEKG shape artifact {path} is missing. Run "
                    "'python manage.py fetch_oekg_shapes' to obtain it."
                )
        super().setUpClass()


class IsolatedGraphMixin:
    """Points a test at a real store, in a graph of its own, or skips."""

    @classmethod
    def setUpClass(cls):
        # Both checks run BEFORE super(). A TestCase opens class-level atomics
        # in setUpClass, and raising SkipTest after that skips tearDownClass
        # too, leaving them open -- which breaks the NEXT test class with
        # "connection already closed", nowhere near the cause.
        host = settings.RDF_DATABASES["knowledge"]["host"]
        if host not in LOCAL_GRAPH_HOSTS:
            raise unittest.SkipTest(
                f"The OEKG graph store is configured at {host!r}, which is not "
                "a recognised local host. These tests write, so they refuse to "
                "run against a store that might not be yours. Point "
                "RDF_DATABASE_HOST at localhost or the compose network."
            )
        probe = GraphStore.from_settings()
        if not probe.is_available():
            raise unittest.SkipTest(
                f"The OEKG graph store at {probe.update_url} is not available "
                "for reading and writing -- probed with a no-op write, because "
                "reads and updates are not the same permission. Start the "
                "compose network, or point "
                "RDF_DATABASE_HOST / RDF_DATABASE_USER / RDF_DATABASE_PASSWORD "
                "at a running Fuseki, to run the graph tests."
            )
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.graph_name = TEST_GRAPH_PREFIX + str(uuid.uuid4())
        self.store = GraphStore.from_settings(graph=self.graph_name)
        # Cleaning up afterwards rather than beforehand is what lets every test
        # assert on an empty graph without depending on execution order.
        self.addCleanup(self.store.clear)


class OekgGraphTestCase(IsolatedGraphMixin, SimpleTestCase):
    """A graph test with no database. The transport needs none."""


class OekgGraphAPITestCase(RequiresShapeArtifactsMixin, IsolatedGraphMixin, TestCase):
    """A graph test that also has the database.

    The API writes ownership rows to Postgres beside the graph, so its tests
    need both. `OEKG_GRAPH` points the views' own store at this test's graph
    without the tests having to reach inside them.
    """

    def setUp(self):
        super().setUp()
        override = override_settings(OEKG_GRAPH=self.graph_name)
        override.enable()
        self.addCleanup(override.disable)
