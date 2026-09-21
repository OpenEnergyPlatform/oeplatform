"""What the validator merges in, and why merging less changes no verdict.

``ex:CommonShape`` requires exactly one plain-string ``rdfs:label`` on every
OEO term a bundle picks, and a payload carries labels only for the nodes it
mints. So the label subset has to be in the graph the validator reads -- but
only the part of it the post-state actually names.

These tests pin the claim that makes the narrow merge safe: the subset is flat
(one predicate, IRI subjects), so a term the post-state never mentions can
neither be targeted nor reached by a constraint. Each test below compares the
narrow merge against the whole subset rather than asserting a remembered
answer, because the property is *equivalence*, not a particular verdict.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import SimpleTestCase
from pyshacl import validate as pyshacl_validate
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import RDFS, SH

from oekg.bundles import build_bundle_graph
from oekg.fields import OEO
from oekg.shape import label_graph, labels_by_term, shape_graph
from oekg.tests import RequiresShapeArtifactsMixin
from oekg.tests.bundle_fixtures import VALID_PAYLOAD
from oekg.validation import (
    _violation,
    _with_the_labels_it_names,
    validate_post_state,
)

UID = "11111111-2222-3333-4444-555555555555"

# The four picks of VALID_PAYLOAD, minus one at a time: each of these is a real
# bundle shape, and between them they exercise a conforming post-state and
# several that violate different rules.
WITHOUT_TECHNOLOGIES = {k: v for k, v in VALID_PAYLOAD.items() if k != "technologies"}
WITHOUT_SECTORS = {k: v for k, v in VALID_PAYLOAD.items() if k != "sectors"}
WITHOUT_ACRONYM = {k: v for k, v in VALID_PAYLOAD.items() if k != "acronym"}


def violations_of(graph: Graph):
    """Validate exactly ``graph``, merging nothing into it.

    The reference the narrowed merge is measured against. Hand it
    ``post_state + label_graph()`` for what ``validate_post_state`` used to
    do, or the bare post-state for what it would report with no labels at all.
    """
    conforms, report, _ = pyshacl_validate(
        graph, shacl_graph=shape_graph(), advanced=True, inference="none"
    )
    if conforms:
        return []
    return sorted(
        (
            _violation(report, result)
            for result in report.subjects(RDF.type, SH.ValidationResult)
        ),
        key=lambda v: (v.path or "", v.message),
    )


class ValidationTestCase(RequiresShapeArtifactsMixin, SimpleTestCase):
    """No store and no database: validation happens before either is touched."""


class NarrowedMergeTest(ValidationTestCase):
    def test_a_conforming_bundle_still_conforms(self):
        # If the picked terms lost their labels, every one of them would break
        # ex:CommonShape's sh:minCount 1 -- so this failing means the filter
        # dropped something it needed.
        self.assertEqual(
            validate_post_state(build_bundle_graph(UID, VALID_PAYLOAD)), []
        )

    def test_it_reports_exactly_what_the_whole_subset_reported(self):
        for name, payload in [
            ("valid", VALID_PAYLOAD),
            ("no technologies", WITHOUT_TECHNOLOGIES),
            ("no sectors", WITHOUT_SECTORS),
            ("no acronym", WITHOUT_ACRONYM),
            ("empty", {}),
        ]:
            with self.subTest(payload=name):
                post_state = build_bundle_graph(UID, payload)
                self.assertEqual(
                    validate_post_state(post_state),
                    violations_of(post_state + label_graph()),
                )

    def test_the_labels_are_load_bearing_and_not_merely_unused(self):
        # Guards the equivalence test above from passing for the wrong reason.
        # If the narrow merge degenerated to merging nothing, the two sides
        # would still have to agree -- unless merging nothing is visibly
        # different, which is what this asserts.
        post_state = build_bundle_graph(UID, VALID_PAYLOAD)

        self.assertEqual([], validate_post_state(post_state))
        self.assertNotEqual([], violations_of(post_state))

    def test_it_merges_the_label_of_a_term_the_bundle_picks(self):
        merged = _with_the_labels_it_names(build_bundle_graph(UID, VALID_PAYLOAD))

        for iri in (
            VALID_PAYLOAD["descriptors"]
            + VALID_PAYLOAD["sector_divisions"]
            + VALID_PAYLOAD["sectors"]
            + VALID_PAYLOAD["technologies"]
        ):
            with self.subTest(term=iri):
                self.assertIsNotNone(merged.value(URIRef(iri), RDFS.label))

    def test_it_leaves_out_the_terms_the_bundle_never_names(self):
        merged = _with_the_labels_it_names(build_bundle_graph(UID, VALID_PAYLOAD))
        labelled = {s for s, _, _ in merged.triples((None, RDFS.label, None))}

        # The subset holds thousands; a bundle picks a handful plus whatever
        # labels it mints for itself.
        self.assertLess(len(labelled), 50)
        self.assertLess(len(labelled), len(labels_by_term()))

    def test_a_term_with_no_label_in_the_subset_gains_none(self):
        # An IRI the OEO does not know is exactly the case ex:CommonShape is
        # there to catch, and nothing may invent a label for it.
        unknown = URIRef(str(OEO) + "OEO_99999999")
        post_state = build_bundle_graph(
            UID, {**VALID_PAYLOAD, "technologies": [str(unknown)]}
        )

        merged = _with_the_labels_it_names(post_state)

        self.assertIsNone(merged.value(unknown, RDFS.label))
        self.assertIn(
            (str(unknown), str(RDFS.label)),
            [(v.focus_node, v.path) for v in validate_post_state(post_state)],
        )


class NothingLeaksTest(ValidationTestCase):
    """The merge is fresh, so no validation can reach the next one.

    Both directions matter. Writing into the caller's post-state would let a
    pre-state validation change what the post-state validation then sees --
    which is the comparison ``introduced_violations`` rests on. Writing into
    the cached label subset would leak one request's triples into every later
    one in the process, and in the suite into every later test.
    """

    def test_the_post_state_handed_in_is_not_written_to(self):
        post_state = build_bundle_graph(UID, VALID_PAYLOAD)
        before = set(post_state)

        validate_post_state(post_state)

        self.assertEqual(before, set(post_state))

    def test_the_cached_label_subset_is_not_written_to(self):
        before = set(label_graph())

        validate_post_state(build_bundle_graph(UID, VALID_PAYLOAD))

        self.assertEqual(before, set(label_graph()))

    def test_the_lookup_table_refuses_to_be_written_to(self):
        with self.assertRaises(TypeError):
            labels_by_term()[URIRef("urn:nope")] = (Literal("nope"),)

    def test_the_merged_graph_is_not_the_post_state(self):
        post_state = build_bundle_graph(UID, VALID_PAYLOAD)

        merged = _with_the_labels_it_names(post_state)

        self.assertIsNot(merged, post_state)
        self.assertGreater(len(merged), len(post_state))
