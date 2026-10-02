"""The repair command: what it fixes, what it refuses to guess, what it records.

This writes to the graph the platform serves, so the tests are about the
safeguards as much as the repairs: the dry run changes nothing, the record is
written before the change, and the two repairs that lose or invent information
have to be asked for by name.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
import logging
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import override_settings
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import XSD

from oekg.bundles import OEO
from oekg.tests import OekgGraphTestCase

HAS_REFERENCE = OEO.OEO_00390078
REFERENCE_CLASS = OEO.OEO_00000353
REGION = URIRef("https://openenergyplatform.org/ontology/oekg/region/Germany")
CODE = URIRef("https://example.org/iso3166/DE")
OTHER_CODE = URIRef("https://example.org/iso3166/DEU")
SCENARIO = URIRef("https://openenergyplatform.org/ontology/oekg/scenario/x")
HAS_YEAR = OEO.OEO_00020440


class RepairCommandTestCase(OekgGraphTestCase):
    def setUp(self):
        super().setUp()
        # The command builds its own store from the settings, so point those at
        # this test's graph rather than at the one the platform serves.
        override = override_settings(OEKG_GRAPH=self.graph_name)
        override.enable()
        self.addCleanup(override.disable)

    def run_command(self, *args):
        out = StringIO()
        call_command("repair_oekg_shape_violations", *args, stdout=out)
        return out.getvalue()

    def triples(self):
        return self.store.construct("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")

    def with_untyped_reference(self):
        graph = Graph()
        graph.add((REGION, HAS_REFERENCE, CODE))
        self.store.insert(graph)


class TypeRepairTest(RepairCommandTestCase):
    def test_it_types_a_node_referenced_as_a_reference(self):
        self.with_untyped_reference()

        self.run_command("--apply", "--record", "/dev/null")

        self.assertIn((CODE, RDF.type, REFERENCE_CLASS), self.triples())

    def test_a_dry_run_changes_nothing(self):
        self.with_untyped_reference()
        before = len(self.triples())

        output = self.run_command()

        self.assertEqual(len(self.triples()), before)
        self.assertIn("dry run", output)

    def test_it_says_what_it_would_do(self):
        self.with_untyped_reference()

        output = self.run_command()

        self.assertIn("triples to add:    1", output)

    def test_running_it_twice_changes_nothing_the_second_time(self):
        self.with_untyped_reference()
        self.run_command("--apply", "--record", "/dev/null")
        after_first = len(self.triples())

        output = self.run_command("--apply", "--record", "/dev/null")

        self.assertEqual(len(self.triples()), after_first)
        self.assertIn("Nothing to repair", output)

    def test_an_already_typed_reference_is_left_alone(self):
        graph = Graph()
        graph.add((REGION, HAS_REFERENCE, CODE))
        graph.add((CODE, RDF.type, REFERENCE_CLASS))
        self.store.insert(graph)

        self.assertIn("Nothing to repair", self.run_command())


class DangerousRepairsAreOptInTest(RepairCommandTestCase):
    def with_two_references(self):
        graph = Graph()
        graph.add((REGION, HAS_REFERENCE, CODE))
        graph.add((REGION, HAS_REFERENCE, OTHER_CODE))
        graph.add((CODE, RDF.type, REFERENCE_CLASS))
        graph.add((OTHER_CODE, RDF.type, REFERENCE_CLASS))
        self.store.insert(graph)

    def with_a_year_only_date(self):
        # rdflib warns, with a traceback, every time it parses this literal --
        # and it parses it on every read, so a handful of tests write hundreds
        # of lines. The warning is correct and is exactly the defect the
        # `year-dates` repair exists for, so it is quieted here, where the
        # literal is written on purpose, rather than anywhere that would also
        # hide one coming from real data.
        logger = logging.getLogger("rdflib.term")
        was = logger.level
        logger.setLevel(logging.ERROR)
        self.addCleanup(logger.setLevel, was)

        graph = Graph()
        graph.add((SCENARIO, HAS_YEAR, Literal("2020", datatype=XSD.dateTime)))
        self.store.insert(graph)

    def test_a_surplus_reference_survives_a_default_run(self):
        # It destroys data, so it is not something a default does.
        self.with_two_references()

        self.run_command("--apply", "--record", "/dev/null")

        self.assertEqual(len(list(self.triples().objects(REGION, HAS_REFERENCE))), 2)

    def test_a_year_only_date_survives_a_default_run(self):
        # It invents a day and a time nobody stated.
        self.with_a_year_only_date()

        self.run_command("--apply", "--record", "/dev/null")

        self.assertIn(
            Literal("2020", datatype=XSD.dateTime),
            list(self.triples().objects(SCENARIO, HAS_YEAR)),
        )

    def test_the_default_run_names_what_it_did_not_do(self):
        output = self.run_command()

        self.assertIn("Not selected", output)
        self.assertIn("duplicate-references", output)
        self.assertIn("year-dates", output)

    def test_a_surplus_reference_goes_when_asked_for_by_name(self):
        self.with_two_references()

        self.run_command(
            "--apply", "--repair", "duplicate-references", "--record", "/dev/null"
        )

        self.assertEqual(len(list(self.triples().objects(REGION, HAS_REFERENCE))), 1)

    def test_dropping_a_reference_says_which_one_was_lost(self):
        self.with_two_references()

        output = self.run_command("--repair", "duplicate-references")

        self.assertIn("lost", output)
        self.assertIn("nothing says which", output)

    def test_a_year_becomes_a_timestamp_when_asked_for_by_name(self):
        self.with_a_year_only_date()

        self.run_command("--apply", "--repair", "year-dates", "--record", "/dev/null")

        values = [str(o) for o in self.triples().objects(SCENARIO, HAS_YEAR)]
        self.assertEqual(values, ["2020-01-01T00:00:00+00:00"])

    def test_inventing_a_date_says_so(self):
        self.with_a_year_only_date()

        output = self.run_command("--repair", "year-dates")

        self.assertIn("nobody stated", output)


class TheRecordTest(RepairCommandTestCase):
    def test_it_records_every_triple_it_added(self):
        self.with_untyped_reference()

        with TemporaryDirectory() as folder:
            path = Path(folder, "record.json")
            self.run_command("--apply", "--record", str(path))
            record = json.loads(path.read_text())

        self.assertEqual(record["repairs"], ["types"])
        self.assertEqual(len(record["added"]), 1)
        self.assertEqual(record["added"][0][2], {"iri": str(REFERENCE_CLASS)})

    def test_it_records_what_it_removed_and_why(self):
        graph = Graph()
        graph.add((REGION, HAS_REFERENCE, CODE))
        graph.add((REGION, HAS_REFERENCE, OTHER_CODE))
        self.store.insert(graph)

        with TemporaryDirectory() as folder:
            path = Path(folder, "record.json")
            self.run_command(
                "--apply", "--repair", "duplicate-references", "--record", str(path)
            )
            record = json.loads(path.read_text())

        self.assertEqual(len(record["removed"]), 1)
        self.assertTrue(record["notes"])

    def test_a_dry_run_writes_no_record(self):
        self.with_untyped_reference()

        with TemporaryDirectory() as folder:
            path = Path(folder, "record.json")
            self.run_command("--record", str(path))

            self.assertFalse(path.exists())

    def test_the_graph_is_untouched_when_the_record_cannot_be_written(self):
        # The record goes first on purpose: a change nobody can undo is worse
        # than no change.
        self.with_untyped_reference()
        before = len(self.triples())

        with self.assertRaises(OSError):
            self.run_command("--apply", "--record", "/nope/nowhere/record.json")

        self.assertEqual(len(self.triples()), before)
