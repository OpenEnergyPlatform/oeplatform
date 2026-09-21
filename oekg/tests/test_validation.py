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
"""  # noqa: E501

from collections import Counter

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


def without(*keys) -> dict:
    """``VALID_PAYLOAD`` minus some fields: a bundle violating known rules."""
    return {k: v for k, v in VALID_PAYLOAD.items() if k not in keys}


# A bundle carrying one of everything that puts a node two or three hops out:
# a scenario with both kinds of region, a study report with an author and a
# reference. Those are where sh:targetObjectsOf reaches furthest, so a flat
# bundle alone would not exercise the filter where it matters most.
NESTED_PAYLOAD = {
    **VALID_PAYLOAD,
    "contacts": [{"label": "Grace Hopper"}],
    "organisations": [{"label": "Reiner Lemoine Institut"}],
    "funders": [{"label": "BMWK"}],
    "frameworks": [{"label": "PyPSA"}],
    "scenarios": [
        {
            "label": "A high renewables scenario",
            "acronym": "HIGH-RE",
            "scenario_types": [str(OEO.OEO_00000364)],
            "years": ["2030-01-01T00:00:00+00:00"],
            "study_regions": [
                {
                    "iri": "https://openenergyplatform.org/oekg/regions/berlin",
                    "label": "Berlin",
                }
            ],
            "interacting_regions": [
                {
                    "iri": "https://openenergyplatform.org/oekg/regions/brandenburg",
                    "label": "Brandenburg",
                }
            ],
        }
    ],
    "study_reports": [
        {
            "label": "Energy scenarios for 2045",
            "authors": [{"label": "Ada Lovelace"}],
            "publication_date": "2024-03-01T00:00:00+00:00",
            "reference": "https://doi.org/10.5281/zenodo.1234567",
        }
    ],
}


def violations_of(graph: Graph):
    """Validate exactly ``graph``, merging nothing into it.

    The reference the narrowed merge is measured against. Hand it
    ``post_state + label_graph()`` for what ``validate_post_state`` used to
    do, or the bare post-state for what it would report with no labels at all.

    It repeats ``validate_post_state``'s body on purpose: a reference that
    called the function under test could not measure it. The one thing it
    must keep sharing is ``_violation``, because the comparison is between
    violations and not between report graphs -- hence the private import,
    which is the only one in this package's tests.
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
            ("nested", NESTED_PAYLOAD),
            ("nested, no technologies", {**NESTED_PAYLOAD, "technologies": []}),
            ("no technologies", without("technologies")),
            ("no sectors", without("sectors")),
            ("no acronym", without("acronym")),
            ("no label or abstract", without("label", "abstract")),
            ("empty", {}),
        ]:
            with self.subTest(payload=name):
                post_state = build_bundle_graph(UID, payload)
                # As a multiset, the way `introduced_violations` compares
                # them: two violations sharing a sort key keep rdflib's own
                # iteration order, which two validations need not agree on,
                # and an ordering difference is not a difference in verdict.
                self.assertEqual(
                    Counter(validate_post_state(post_state)),
                    Counter(violations_of(post_state + label_graph())),
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


class ShapeTargetsTest(ValidationTestCase):
    """The one fact about the shape that the narrow merge argues from.

    Leaving a term's label out is safe because nothing in the shape can
    select or read a node the post-state never mentions. That is true of the
    shape as it stands, not of SHACL in general -- so this fails rather than
    the equivalence quietly weakening if the shape grows a target or a
    constraint that reaches further. The answer is not necessarily to revert;
    it is to re-check `_with_the_labels_it_names` against the new construct.
    """

    def test_every_target_is_a_class_or_the_objects_of_a_predicate(self):
        # sh:targetClass needs an rdf:type the label subset does not carry;
        # the objects of a predicate come only from the post-state. Either
        # way a term the post-state never names cannot be a focus node.
        targets = {
            str(predicate)
            for _, predicate, _ in shape_graph()
            if str(predicate).startswith(str(SH)) and "target" in str(predicate)
        }

        self.assertEqual(targets, {str(SH.targetClass), str(SH.targetObjectsOf)})

    def test_the_shape_reads_nothing_by_query_or_rule(self):
        # sh:targetNode names a node outright; sh:sparql and sh:rule can read
        # or write anywhere in the data graph. Any of the three would make
        # "only what the post-state names" the wrong set.
        for construct in (SH.targetNode, SH.sparql, SH.rule, SH.select):
            with self.subTest(construct=str(construct)):
                self.assertEqual([], list(shape_graph().subject_objects(construct)))


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
