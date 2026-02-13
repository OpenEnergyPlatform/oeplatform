"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DC, RDF, RDFS

# Import your view
from factsheet.views import get_scenarios_view


class GetScenariosViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("factsheet.views.OekgQuery")  # patch where it is imported/used
    @patch("factsheet.views.oekg")  # patch the global graph in the views module
    def test_view_handles_internal_and_databus_datasets(self, mock_oekg, MockOekgQuery):
        # Mock study descriptors call to avoid DB/real KG logic
        MockOekgQuery.return_value.get_bundle_study_descriptors_where_scenario_is_part_of.return_value = (  # noqa: E501
            []
        )

        # Build a minimal RDF graph
        g = Graph()
        OEO = Namespace("https://openenergyplatform.org/ontology/oeo/")
        OBO = Namespace("http://purl.obolibrary.org/obo/")

        scenario_uid = "60a682d8-6a41-25d3-c817-e258a90a5d5e"
        scenario = URIRef(f"https://openenergyplatform.org/scenario/{scenario_uid}")

        g.add((scenario, RDF.type, OEO.OEO_00000365))
        g.add((scenario, RDFS.label, Literal("Scenario A")))
        g.add((scenario, DC.abstract, Literal("Scenario abstract")))

        # Provide a study so study_label/study_abstract exist
        study = URIRef("https://openenergyplatform.org/study/study1")
        g.add((study, OBO.BFO_0000051, scenario))
        g.add((study, RDFS.label, Literal("Study A")))
        g.add((study, DC.abstract, Literal("Study abstract")))

        # Input dataset: internal URL
        inp = URIRef("https://openenergyplatform.org/dataset/inp1")
        g.add((scenario, OEO.OEO_00020437, inp))
        g.add((inp, RDFS.label, Literal("Input DS")))
        g.add(
            (
                inp,
                OEO.OEO_00390094,
                Literal("database/tables/eu_leg_data_2021_rep_table_3"),
            )
        )

        # Output dataset: databus URL
        out = URIRef("https://openenergyplatform.org/dataset/out1")
        g.add((scenario, OEO.OEO_00020436, out))
        g.add((out, RDFS.label, Literal("Output DS")))
        g.add(
            (
                out,
                OEO.OEO_00390094,
                Literal(
                    "https://databus.openenergyplatform.org/zl_energie/ZLE/IKT_Input/FinalData_v2"  # noqa: E501
                ),
            )
        )

        # Make the view use our graph
        mock_oekg.triples.side_effect = g.triples
        mock_oekg.value.side_effect = g.value

        # Call the view
        request = self.factory.get(
            "/scenario-bundles/get_scenarios/",
            data={"scenarios_uid": json.dumps([scenario_uid])},
        )
        response = get_scenarios_view(request)

        self.assertEqual(response.status_code, 200)

        payload = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(payload), 1)

        data = payload[0]["data"]

        # Assert datasets exist
        self.assertEqual(len(data["input_datasets"]), 1)
        self.assertEqual(len(data["output_datasets"]), 1)

        # If you return dicts for datasets (recommended)
        self.assertEqual(data["input_datasets"][0]["kind"], "oep_table")
        self.assertEqual(
            data["input_datasets"][0]["table_name"], "eu_leg_data_2021_rep_table_3"
        )

        self.assertEqual(data["output_datasets"][0]["kind"], "databus")
        self.assertEqual(
            data["output_datasets"][0]["external_id"],
            "zl_energie/ZLE/IKT_Input/FinalData_v2",
        )
