"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import io
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings
from rdflib import Graph

from oekg.shape_artifacts import (
    EmptyLabelSubsetError,
    MissingOntologyError,
    NotAShapeError,
    PinnedRef,
    UnpinnedSourceError,
    extract_label_subset,
    fetch_shape,
    raw_github_url,
)

COMMIT = "b4604e02060624b381bdbe2f872df94cfd0f5630"

# A minimal but real SHACL shape: enough that a parse-and-recognise check passes.
SHAPE_TTL = b"""
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
@prefix oeo: <https://openenergyplatform.org/ontology/oeo/> .

ex:StudyShape
    a sh:NodeShape ;
    sh:closed true ;
    sh:targetClass oeo:OEO_00020227 .
"""

OTHER_SHAPE_TTL = SHAPE_TTL.replace(b"ex:StudyShape", b"ex:RenamedStudyShape")

# What GitHub actually serves for a bad path: valid text, not a shape at all.
NOT_FOUND_BODY = b"404: Not Found"

# rdfs:label triples on IRI subjects are the only thing the label subset keeps.
OEO_FIXTURE_TTL = """
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix oeo: <https://openenergyplatform.org/ontology/oeo/> .

oeo:OEO_00020227 a owl:Class ;
    rdfs:label "scenario bundle" ;
    obo:IAO_0000115 "A definition that must not survive the extraction." .

oeo:OEO_00010449 a owl:Class ;
    rdfs:label "wind technology" .

[] rdfs:label "a label on a blank node" .
"""


class TempArtifactsTestCase(SimpleTestCase):
    """Gives each test its own shapes directory and OEO release tree."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

        self.shapes_root = self.tmp / "shapes"
        self.shapes_root.mkdir()
        self.shape_path = self.shapes_root / "oekg_shapes.ttl"
        self.labels_path = self.shapes_root / "oeo_labels.ttl"

        self.ontology_root = self.tmp / "ontologies"
        self.oeo_dir = self.ontology_root / "oeo" / "2.13.0"
        self.oeo_dir.mkdir(parents=True)
        self.oeo_full_owl = self.oeo_dir / "oeo-full.owl"
        Graph().parse(data=OEO_FIXTURE_TTL, format="turtle").serialize(
            destination=str(self.oeo_full_owl), format="xml"
        )

    def settings_override(self):
        return override_settings(
            OEKG_SHAPES_ROOT=self.shapes_root,
            OEKG_SHAPES_PATH=self.shape_path,
            OEKG_SHAPE_LABELS_PATH=self.labels_path,
            ONTOLOGY_ROOT=self.ontology_root,
            OEKG_SHAPES_PINNED_COMMIT=COMMIT,
        )


class PinnedRefTest(SimpleTestCase):
    def test_a_commit_sha_is_pinned(self):
        ref = PinnedRef.commit(COMMIT)
        self.assertEqual(ref.value, COMMIT)
        self.assertEqual(ref.kind, "commit")

    def test_an_abbreviated_commit_sha_is_pinned(self):
        self.assertEqual(PinnedRef.commit("b4604e02").value, "b4604e02")

    def test_a_commit_option_that_is_not_a_sha_is_refused(self):
        for value in ["main", "latest", "v1.0.0", "", "b4604", "B4604E02"]:
            with self.subTest(value=value):
                with self.assertRaises(UnpinnedSourceError):
                    PinnedRef.commit(value)

    def test_a_version_tag_is_pinned(self):
        self.assertEqual(PinnedRef.tag("v1.2.0").value, "v1.2.0")
        self.assertEqual(PinnedRef.tag("thesis-madbkr-2025").kind, "tag")

    def test_a_moving_ref_is_refused_even_when_offered_as_a_tag(self):
        for value in [
            "latest",
            "LATEST",
            "HEAD",
            "main",
            "master",
            "develop",
            "production",
            "staging",
            "release-latest",
            "refs/heads/main",
            "..",
            "",
            "  ",
        ]:
            with self.subTest(value=value):
                with self.assertRaises(UnpinnedSourceError):
                    PinnedRef.tag(value)

    def test_the_refusal_says_why_and_what_to_pass(self):
        with self.assertRaises(UnpinnedSourceError) as caught:
            PinnedRef.tag("main")
        message = str(caught.exception)
        self.assertIn("main", message)
        self.assertIn("pinned", message.lower())


class RawUrlTest(SimpleTestCase):
    def test_the_url_carries_the_pinned_ref(self):
        url = raw_github_url(
            "OpenEnergyPlatform/oekg",
            PinnedRef.commit(COMMIT),
            "oekg/shapes/oekg_shapes.ttl",
        )
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/OpenEnergyPlatform/oekg/"
            f"{COMMIT}/oekg/shapes/oekg_shapes.ttl",
        )

    def test_a_tag_ref_is_usable_as_a_url_segment(self):
        url = raw_github_url("o/r", PinnedRef.tag("v2.0.0"), "a/b.ttl")
        self.assertEqual(url, "https://raw.githubusercontent.com/o/r/v2.0.0/a/b.ttl")


class FetchShapeTest(TempArtifactsTestCase):
    def read_ok(self, payload=SHAPE_TTL):
        return lambda url: payload

    def test_a_successful_fetch_lands_the_shape(self):
        result = fetch_shape("http://x/s.ttl", self.shape_path, read_url=self.read_ok())

        self.assertEqual(result.status, "created")
        self.assertTrue(result.changed)
        self.assertEqual(self.shape_path.read_bytes(), SHAPE_TTL)

    def test_re_running_reports_that_nothing_changed(self):
        fetch_shape("http://x/s.ttl", self.shape_path, read_url=self.read_ok())
        result = fetch_shape("http://x/s.ttl", self.shape_path, read_url=self.read_ok())

        self.assertEqual(result.status, "unchanged")
        self.assertFalse(result.changed)

    def test_a_moved_pin_reports_an_update(self):
        fetch_shape("http://x/s.ttl", self.shape_path, read_url=self.read_ok())
        result = fetch_shape(
            "http://x/s.ttl",
            self.shape_path,
            read_url=self.read_ok(OTHER_SHAPE_TTL),
        )

        self.assertEqual(result.status, "updated")
        self.assertEqual(self.shape_path.read_bytes(), OTHER_SHAPE_TTL)

    def test_a_body_that_is_not_a_shape_is_refused(self):
        with self.assertRaises(NotAShapeError):
            fetch_shape(
                "http://x/s.ttl",
                self.shape_path,
                read_url=self.read_ok(NOT_FOUND_BODY),
            )

        self.assertFalse(self.shape_path.exists())

    def test_turtle_without_a_node_shape_is_refused(self):
        with self.assertRaises(NotAShapeError):
            fetch_shape(
                "http://x/s.ttl",
                self.shape_path,
                read_url=self.read_ok(b"@prefix ex: <http://example.org/> .\n"),
            )

        self.assertFalse(self.shape_path.exists())

    def test_a_failed_fetch_leaves_the_previous_shape_usable(self):
        fetch_shape("http://x/s.ttl", self.shape_path, read_url=self.read_ok())

        def boom(url):
            raise OSError("connection reset")

        with self.assertRaises(OSError):
            fetch_shape("http://x/s.ttl", self.shape_path, read_url=boom)

        self.assertEqual(self.shape_path.read_bytes(), SHAPE_TTL)
        Graph().parse(str(self.shape_path), format="turtle")

    def test_a_truncated_body_leaves_the_previous_shape_usable(self):
        fetch_shape("http://x/s.ttl", self.shape_path, read_url=self.read_ok())

        with self.assertRaises(NotAShapeError):
            fetch_shape(
                "http://x/s.ttl",
                self.shape_path,
                read_url=self.read_ok(SHAPE_TTL[:60]),
            )

        self.assertEqual(self.shape_path.read_bytes(), SHAPE_TTL)

    def test_no_partial_file_is_left_behind(self):
        def boom(url):
            raise OSError("connection reset")

        with self.assertRaises(OSError):
            fetch_shape("http://x/s.ttl", self.shape_path, read_url=boom)

        self.assertEqual(sorted(p.name for p in self.shapes_root.iterdir()), [])


class ExtractLabelSubsetTest(TempArtifactsTestCase):
    def test_only_labels_on_iri_subjects_survive(self):
        result = extract_label_subset(self.oeo_full_owl, self.labels_path)

        self.assertEqual(result.status, "created")
        graph = Graph()
        graph.parse(str(self.labels_path), format="turtle")

        labels = {(str(s), str(o)) for s, _, o in graph}
        self.assertEqual(
            labels,
            {
                (
                    "https://openenergyplatform.org/ontology/oeo/OEO_00020227",
                    "scenario bundle",
                ),
                (
                    "https://openenergyplatform.org/ontology/oeo/OEO_00010449",
                    "wind technology",
                ),
            },
        )

    def test_re_extracting_reports_that_nothing_changed(self):
        extract_label_subset(self.oeo_full_owl, self.labels_path)
        result = extract_label_subset(self.oeo_full_owl, self.labels_path)

        self.assertEqual(result.status, "unchanged")

    def test_a_missing_ontology_leaves_the_previous_subset_usable(self):
        extract_label_subset(self.oeo_full_owl, self.labels_path)
        before = self.labels_path.read_bytes()

        with self.assertRaises(MissingOntologyError):
            extract_label_subset(self.oeo_dir / "nope.owl", self.labels_path)

        self.assertEqual(self.labels_path.read_bytes(), before)

    def test_an_ontology_with_no_labels_is_refused(self):
        empty = self.oeo_dir / "empty.owl"
        Graph().serialize(destination=str(empty), format="xml")

        with self.assertRaises(EmptyLabelSubsetError):
            extract_label_subset(empty, self.labels_path)

        self.assertFalse(self.labels_path.exists())


class FetchOekgShapesCommandTest(TempArtifactsTestCase):
    def call(self, payload=SHAPE_TTL, **options):
        """Runs the command with the network stubbed out and stdout captured."""
        self.out = io.StringIO()
        with self.settings_override():
            with mock.patch(
                "oekg.shape_artifacts.read_url_bytes", return_value=payload
            ) as reader:
                call_command("fetch_oekg_shapes", stdout=self.out, **options)
        return reader

    def test_it_lands_both_artifacts(self):
        reader = self.call()

        self.assertEqual(self.shape_path.read_bytes(), SHAPE_TTL)
        self.assertTrue(self.labels_path.exists())
        self.assertEqual(
            reader.call_args[0][0],
            "https://raw.githubusercontent.com/OpenEnergyPlatform/oekg/"
            f"{COMMIT}/oekg/shapes/oekg_shapes.ttl",
        )

    def test_it_creates_the_shapes_directory(self):
        shutil.rmtree(self.shapes_root)
        self.call()
        self.assertTrue(self.shape_path.exists())

    def test_it_names_the_pinned_source_it_used(self):
        self.call()

        self.assertIn(COMMIT, self.out.getvalue())

    def test_it_never_reads_the_full_ontology_over_the_network(self):
        reader = self.call()

        urls = [call.args[0] for call in reader.call_args_list]
        self.assertEqual(len(urls), 1)
        self.assertNotIn("oeo-full", urls[0])

    def test_re_running_is_safe_and_reports_nothing_changed(self):
        self.call()
        first = self.shape_path.read_bytes()
        self.assertIn("created", self.out.getvalue())

        self.call()

        self.assertEqual(self.shape_path.read_bytes(), first)
        self.assertIn("unchanged", self.out.getvalue())
        self.assertIn("already up to date", self.out.getvalue())

    def test_a_moved_pin_is_reported_as_an_update(self):
        self.call()
        self.call(payload=OTHER_SHAPE_TTL)

        report = self.out.getvalue()
        self.assertIn("updated", report)
        self.assertIn("unchanged", report)  # the labels did not move

    def test_an_unpinned_tag_is_refused_before_anything_is_fetched(self):
        with self.settings_override():
            with mock.patch("oekg.shape_artifacts.read_url_bytes") as reader:
                with self.assertRaises(CommandError):
                    call_command(
                        "fetch_oekg_shapes", tag="latest", stdout=io.StringIO()
                    )

        reader.assert_not_called()
        self.assertFalse(self.shape_path.exists())

    def test_a_commit_and_a_tag_together_are_refused(self):
        with self.settings_override():
            with self.assertRaises(CommandError):
                call_command(
                    "fetch_oekg_shapes",
                    commit=COMMIT,
                    tag="v1.0.0",
                    stdout=io.StringIO(),
                )

    def test_a_failed_fetch_is_reported_and_keeps_the_prior_artifacts(self):
        self.call()
        before = self.shape_path.read_bytes()

        with self.settings_override():
            with mock.patch(
                "oekg.shape_artifacts.read_url_bytes",
                side_effect=OSError("connection reset"),
            ):
                with self.assertRaises(CommandError):
                    call_command("fetch_oekg_shapes", stdout=io.StringIO())

        self.assertEqual(self.shape_path.read_bytes(), before)

    def test_a_missing_ontology_is_reported_as_a_command_error(self):
        (self.oeo_full_owl).unlink()

        with self.settings_override():
            with mock.patch(
                "oekg.shape_artifacts.read_url_bytes", return_value=SHAPE_TTL
            ):
                with self.assertRaises(CommandError):
                    call_command("fetch_oekg_shapes", stdout=io.StringIO())
