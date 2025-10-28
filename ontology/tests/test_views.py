"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase


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
        self.get("ontology:oeo-initializer", kwargs={"ontology": "oeo"})
        self.get("ontology:oeo-latest-full-zip", kwargs={"ontology": "oeo"})
        self.get("ontology:oeo-latest-glossary", kwargs={"ontology": "oeo"})
        self.get("ontology:oeo-s-c")
        self.get("ontology:oeo-steering-committee")
        self.get("ontology:oeox")
        self.get("ontology:partial-page-content")
        self.get("ontology:partial-page-sidebar-content")
        self.get("ontology:releases")
