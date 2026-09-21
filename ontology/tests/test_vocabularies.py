"""The registry of what the platform serves under `/ontology/`.

The registry exists because there was no such list. The only source of truth
was the filesystem -- `ontologies/oeo` and `ontologies/oeo_ext` -- which cannot
know about `oekg`, because a knowledge graph is not a directory. So an unknown
name got three different answers depending on which route it hit, and none of
them was a 404.

What these tests hold is the property that makes the registry worth having:
**a name is either registered with a kind that something resolves, or it does
not exist.** A kind with nothing behind it is the dangerous state -- a
vocabulary that silently resolved to nothing reads exactly like data that has
been deleted.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import ast
import sys
from pathlib import Path

from django.test import SimpleTestCase

from ontology import vocabularies
from ontology.vocabularies import (
    KINDS,
    KNOWLEDGE_GRAPH,
    ONTOLOGY,
    VOCABULARIES,
    is_file_backed,
    kind_of,
    names_of_kind,
)


class RegistryTest(SimpleTestCase):
    def test_every_vocabulary_declares_a_known_kind(self):
        # The counterpart of `AllowlistTest` and `ResolverCoverageTest` in
        # `oekg/`: adding a name is a decision somebody makes, and the kind is
        # the half of that decision which says who resolves the address.
        for vocabulary in VOCABULARIES:
            with self.subTest(vocabulary=vocabulary.name):
                self.assertIn(vocabulary.kind, KINDS)

    def test_a_name_is_registered_once(self):
        names = [vocabulary.name for vocabulary in VOCABULARIES]
        self.assertEqual(len(names), len(set(names)))

    def test_the_two_file_backed_ontologies_are_registered(self):
        self.assertEqual(kind_of("oeo"), ONTOLOGY)
        self.assertEqual(kind_of("oeo_ext"), ONTOLOGY)
        self.assertTrue(is_file_backed("oeo"))
        self.assertTrue(is_file_backed("oeo_ext"))

    def test_the_knowledge_graph_is_registered_and_is_not_file_backed(self):
        # The kind is not decoration. `oekg` lives in Fuseki, so sending it to
        # the view that lists a directory is how it came to answer 500.
        self.assertEqual(kind_of("oekg"), KNOWLEDGE_GRAPH)
        self.assertFalse(is_file_backed("oekg"))

    def test_an_unregistered_name_has_no_kind(self):
        self.assertIsNone(kind_of("nonsense"))
        self.assertFalse(is_file_backed("nonsense"))

    def test_a_missing_name_has_no_kind(self):
        # The oeo-initializer route makes the name optional, so `None` reaches
        # the lookup. It used to reach `Path(ONTOLOGY_ROOT, None)` instead.
        self.assertIsNone(kind_of(None))
        self.assertFalse(is_file_backed(None))

    def test_names_of_kind_partitions_the_registry(self):
        self.assertEqual(
            sorted(names_of_kind(ONTOLOGY) + names_of_kind(KNOWLEDGE_GRAPH)),
            sorted(vocabulary.name for vocabulary in VOCABULARIES),
        )

    def test_every_vocabulary_says_what_it_is(self):
        # The registry is also the answer to "what does this platform serve
        # here", which is a question the routes could never answer.
        for vocabulary in VOCABULARIES:
            with self.subTest(vocabulary=vocabulary.name):
                self.assertTrue(vocabulary.title.strip())
                self.assertTrue(vocabulary.description.strip())


class DataOnlyTest(SimpleTestCase):
    """The registry imports nothing, the way `api/api_tags.py` imports nothing.

    Both are read from places that cannot afford a dependency: `api_tags` at
    settings-import time, this one from `ontology/urls.py` and from `oekg/`,
    where the rule is that nothing may reach `factsheet/oekg/connection.py`.
    A registry that imported Django would make that rule a matter of luck.
    """

    def test_it_imports_only_the_standard_library(self):
        source = Path(vocabularies.__file__).read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        self.assertTrue(imported <= set(sys.stdlib_module_names), sorted(imported))

    def test_it_does_no_work_at_import_time(self):
        # No filesystem, no store, no settings: the registry says what the
        # platform offers, not what happens to be on disk right now. Read off
        # the syntax tree rather than the text, so the prose may go on naming
        # `os.listdir` as the thing that used to raise.
        source = Path(vocabularies.__file__).read_text(encoding="utf-8")
        called = {
            node.func.id
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

        self.assertEqual(called & {"open", "Path", "getattr", "eval"}, set())
