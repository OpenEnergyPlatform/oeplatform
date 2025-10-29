"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase
from ontology.views import OEO_MODULES_MAIN

TEST_ONTOLOGY = "oeo"


class TestViewsOntology(TestViewsTestCase):
    """Call all (most) views"""

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        # "ontology:oeo-static"  # TODO: why does reverse not work?

        self.get("ontology:index")
        self.get(
            "ontology:oeo-classes",
            kwargs={"ontology": "oeo", "module_or_id": "BFO_0000001"},
        )
        self.get("ontology:oeo-s-c")
        self.get("ontology:oeo-steering-committee")
        self.get("ontology:oeox")
        self.get("ontology:partial-page-content")
        self.get("ontology:releases")

        # these tests only work if local ontology exists
        if TEST_ONTOLOGY in OEO_MODULES_MAIN:
            self.get("ontology:oeo-latest-glossary", kwargs={"ontology": TEST_ONTOLOGY})
            self.get("ontology:oeo-initializer", kwargs={"ontology": TEST_ONTOLOGY})
            self.get("ontology:oeo-latest-full-zip", kwargs={"ontology": TEST_ONTOLOGY})
            self.get("ontology:partial-page-sidebar-content")
