"""What `manage-datasets/` accepts, and what it writes.

The legacy route that attaches datasets to a scenario (superseded by the
scenario-bundle dataset-link endpoints, still in place) had two defects that
never showed in a happy-path test:

- **Its list validation never ran** (#2508). DRF calls `validate_<field>`, the
  field is `datasets`, and the hook was `validate_dataset`. An empty list and
  duplicate names were accepted.
- **Its SPARQL was built by interpolation** (#2509, part 4). The label is a
  table's human-readable title, which the table's owner edits, and the address
  of an external link only has to start with the databus host. A quote in
  either closed the literal and let the rest of the value become triples.

The query tests run the built update against an in-memory rdflib graph, so
they need no Fuseki: what they check is the statement's text, which is exactly
what an injection changes.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

from uuid import uuid4

from django.test import SimpleTestCase
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDFS

from api.serializers import ScenarioBundleScenarioDatasetSerializer
from oekg.sparqlModels import DatasetConfig
from oekg.sparqlQuery import dataset_exists_query, insert_dataset_query

DATABUS = "https://databus.openenergyplatform.org/some/artifact"
INJECTED = 'x" . <urn:evil:s> <urn:evil:p> <urn:evil:o> . <urn:evil:s> <urn:evil:p> "y'


def external(name, kind="input"):
    return {"name": name, "external_url": DATABUS, "type": kind}


def payload(datasets):
    return {
        "scenario_bundle": str(uuid4()),
        "scenario": str(uuid4()),
        "datasets": datasets,
    }


class DatasetListValidationTest(SimpleTestCase):
    """The rules on the whole list run (#2508)."""

    def errors(self, datasets):
        serializer = ScenarioBundleScenarioDatasetSerializer(data=payload(datasets))
        self.assertFalse(serializer.is_valid())
        return serializer.errors

    def test_an_empty_list_is_refused(self):
        self.assertIn("datasets", self.errors([]))

    def test_duplicate_names_are_refused(self):
        self.assertIn(
            "datasets", self.errors([external("grid"), external("grid", "output")])
        )

    def test_distinct_names_are_accepted(self):
        serializer = ScenarioBundleScenarioDatasetSerializer(
            data=payload([external("grid_a"), external("grid_b")])
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class DatasetQueryEscapingTest(SimpleTestCase):
    """A label or an address is a literal, whatever it contains (#2509)."""

    def config(self, label="Grid", url=DATABUS):
        return DatasetConfig(
            bundle_uuid=uuid4(),
            scenario_uuid=uuid4(),
            dataset_label=label,
            dataset_url=url,
            dataset_id=uuid4(),
            dataset_type="input",
        )

    def written(self, config):
        graph = Graph()
        graph.update(insert_dataset_query(config, "RO_0002233", "OEO_00030029"))
        return graph

    def test_a_plain_link_writes_its_five_triples(self):
        self.assertEqual(5, len(self.written(self.config())))

    def test_a_quote_in_the_label_stays_in_the_label(self):
        graph = self.written(self.config(label=INJECTED))

        self.assertEqual(5, len(graph))
        self.assertNotIn(URIRef("urn:evil:s"), set(graph.subjects()))
        self.assertIn(Literal(INJECTED), set(graph.objects(None, RDFS.label)))

    def test_a_quote_in_the_address_stays_in_the_address(self):
        graph = self.written(self.config(url=DATABUS + INJECTED))

        self.assertEqual(5, len(graph))
        self.assertNotIn(URIRef("urn:evil:s"), set(graph.subjects()))

    def test_a_newline_and_a_backslash_survive_as_text(self):
        label = 'line one\nline two \\ "quoted"'
        graph = self.written(self.config(label=label))

        self.assertIn(Literal(label), set(graph.objects(None, RDFS.label)))

    def test_the_existence_check_is_one_ask_whatever_the_address(self):
        # Read-only, but built the same way: an address carrying a quote must
        # not turn the ASK into something else or into a syntax error.
        graph = Graph()
        result = graph.query(dataset_exists_query(uuid4(), DATABUS + INJECTED))

        self.assertIs(False, result.askAnswer)
