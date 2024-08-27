import os
from pathlib import Path

from django.test import TestCase  # noqa:F401
from owlready2 import get_ontology
from rdflib import URIRef

from oeo_ext.utils import create_new_unit

# from rdflib.compare import graph_diff, to_isomorphic


# Create your tests here.

EXPECTED_OEOX_OWL = Path(
    "/home/jh/github/oeplatform/oeo_ext/oeo_extended_store/test/data/expected_composedUnit.owl"  # noqa
)
TEMP_RESULT_OEO_OWL = "temp_oeox.owl"
TEMP_RESULT_OEO_OWL_PATH = Path(os.getcwd(), TEMP_RESULT_OEO_OWL)
RESULT_URI = URIRef(
    "http://openenergy-platform.org/ontology/oeoxTest/composedUnit/OEOX_2"
)


class OeoxNewUnitTestCase(TestCase):
    def setUp(self):
        self.mock_empty_owl = """<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
        xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
        xmlns:owl="http://www.w3.org/2002/07/owl#"
        xml:base="http://example.org/ontology"
        xmlns="http://openenergy-platform.org/ontology/oeoxTest#">

<owl:Ontology rdf:about="http://openenergy-platform.org/ontology/oeoxTest"/>



</rdf:RDF>
"""
        self.mock_user_data_struct = {
            "nominator": [
                {
                    "position": 1,
                    "unitName": "watt-hour",
                    "unitType": "linear",
                    "unitPrefix": "mega",
                }
            ],
            "denominator": [
                {
                    "position": 1,
                    "unitName": "meter",
                    "unitType": "squared",
                    "unitPrefix": "",
                },
                {
                    "position": 2,
                    "unitName": "year",
                    "unitType": "linear",
                    "unitPrefix": "",
                },
            ],
            "definition": None,
            "unitLabel": None,
        }

        with open(TEMP_RESULT_OEO_OWL_PATH, "w") as owl_file:
            owl_file.write(self.mock_empty_owl)

        self.temp_test_owl = TEMP_RESULT_OEO_OWL_PATH.as_uri()
        self.temp_owl = get_ontology(self.temp_test_owl).load()

        oeo_ext_URI_STR = EXPECTED_OEOX_OWL.as_uri()

        self.expected_oeo_ext_owl = get_ontology(oeo_ext_URI_STR).load()

        self.numerator_data = self.mock_user_data_struct.get("nominator", [])
        self.denumerator_data = self.mock_user_data_struct.get("denominator", [])

    # def compare_owl_files(self, generated_file, expected_file):
    #     graph1 = Graph()
    #     graph2 = Graph()

    #     graph1.parse(generated_file, format="xml")
    #     graph2.parse(expected_file, format="xml")

    #     # Canonicalize blank nodes before comparison
    #     # iso_graph1 = to_isomorphic(graph1)
    #     # iso_graph2 = to_isomorphic(graph2)

    #     in_both, in_first, in_second = graph_diff(graph1, graph2)

    #     # Check isomorphism again and display some differences
    #     are_isomorphic = graph1.isomorphic(graph2)

    #     if in_both:
    #         differences_in_first = list(in_first)[:5]  # Show a few differences
    #         differences_in_second = list(in_second)[:5]
    #         print(
    #             f"Diff found in first graph: {differences_in_first} and second graph:"
    #             f"{differences_in_second}"
    #         )

    #     return are_isomorphic

    """
    Test does not pass due to some incomplete implementation in the interface of
    create new function. It misses to adapt to the correct ontology input parameter
    before checking if the entry already exists against the production oeox owl content.
    This fails as the same class exists already. By passing the ontology parameter
    this behavior could not be changed. It seems that the search result is always
    from oeox and not oeox_test owl file.
    """
    # def test_create_new_oeox_unit(self):
    #     """Compared with the expected result."""

    #     uriref, error = create_new_unit(
    #         numerator=self.numerator_data,
    #         denominator=self.denumerator_data,
    #         oeo_ext=self.temp_owl,
    #         uriref=RESULT_URI,
    #         result_file=TEMP_RESULT_OEO_OWL_PATH,
    #     )

    #     print(uriref, error)

    #     # Verify the results and compare OWL files
    #     self.assertIsNotNone(uriref)
    #     self.assertIsNone(error)

    #     self.assertTrue(
    #         self.compare_owl_files(TEMP_RESULT_OEO_OWL_PATH, EXPECTED_OEOX_OWL),
    #         "The generated OWL file does not match the expected OWL file.",
    #     )

    def test_create_new_oeox_unit_fails_if_unit_exists(self):
        print(self.expected_oeo_ext_owl)
        uriref, error = create_new_unit(
            numerator=self.numerator_data,
            denominator=self.denumerator_data,
            oeo_ext=self.expected_oeo_ext_owl,
            uriref=RESULT_URI,
            result_file=TEMP_RESULT_OEO_OWL_PATH,
        )

        # Verify the results and compare OWL files
        self.assertIsNone(uriref)
        self.assertIsNotNone(error)

    def tearDown(self) -> None:
        # if os.path.exists(TEMP_RESULT_OEO_OWL_PATH):
        #     os.remove(TEMP_RESULT_OEO_OWL_PATH)
        return super().tearDown()
