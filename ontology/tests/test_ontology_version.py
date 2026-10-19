"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Which OEO release directory the platform serves (`get_ontology_version`).

The ontology directory is bind-mounted from the developer's machine, so it can
hold whatever the host's file manager leaves there - on macOS a `.DS_Store` in
every folder that was ever opened in Finder.
"""  # noqa: 501

import tempfile
from pathlib import Path

from django.http import Http404
from django.test import SimpleTestCase

from ontology.utils import get_ontology_version


class OntologyVersionTest(SimpleTestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def release(self, *names):
        for name in names:
            (self.root / name).mkdir()

    def test_the_newest_release_wins_numerically(self):
        self.release("2.9.0", "2.10.0", "2.1.0")
        self.assertEqual(get_ontology_version(self.root), "2.10.0")

    def test_stray_entries_are_ignored(self):
        self.release("2.13.0")
        (self.root / ".DS_Store").write_bytes(b"\x00")
        (self.root / "notes.txt").write_text("not a release")
        (self.root / "latest").mkdir()
        self.assertEqual(get_ontology_version(self.root), "2.13.0")

    def test_a_requested_version_is_returned_as_given(self):
        self.release("2.13.0")
        self.assertEqual(get_ontology_version(self.root, "2.0.0"), "2.0.0")

    def test_a_missing_directory_is_not_found(self):
        with self.assertRaises(Http404):
            get_ontology_version(self.root / "absent")

    def test_a_directory_without_a_release_says_so(self):
        (self.root / ".DS_Store").write_bytes(b"\x00")
        with self.assertRaisesMessage(FileNotFoundError, str(self.root)):
            get_ontology_version(self.root)
