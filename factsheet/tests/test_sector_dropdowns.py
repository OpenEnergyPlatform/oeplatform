"""
SPDX-FileCopyrightText: 2026 Jonas Huber
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import unittest

from factsheet.helper import (
    OTHER_DIVISION_LABEL,
    SECTOR_CLASS,
    build_sector_dropdowns_from_oeo,
)
from factsheet.oekg.connection import oeo
from factsheet.oekg.namespaces import OEO

NC_BR_DIVISION = str(OEO.OEO_00010304)  # class-modelled, 7 members
EU_LEGISLATION_DIVISION = str(OEO.OEO_00010403)  # class-modelled, 5 members
KSG_DIVISION = str(OEO.OEO_00010056)  # individual-modelled, 7 members
CRF_2006_DIVISION = str(OEO.OEO_00000242)  # individual-modelled, 108 members
NACE_DIVISION = str(OEO.OEO_00000291)  # no members in the OEO


class TestSectorDropdowns(unittest.TestCase):
    """The dynamic sector-division payload served by the populate endpoint.

    Counts come from the OEKG scenario-bundles wayfinder research (WF-01 and its
    NC/BR addendum) against the OEO shipped in this repo.
    """

    @classmethod
    def setUpClass(cls):
        cls.divisions, cls.sectors = build_sector_dropdowns_from_oeo(oeo)
        cls.by_iri = {d["iri"]: d for d in cls.divisions}

    def test_divisions_are_not_the_former_hardcoded_three(self):
        # SECTOR_DEVISIONS used to pin the list to KSG, CRF 2006 and NC/BR.
        self.assertGreater(len(self.divisions), 3)

    def test_divisions_without_members_are_listed_too(self):
        self.assertIn(NACE_DIVISION, self.by_iri)
        self.assertEqual(self.by_iri[NACE_DIVISION]["options"], [])

    def test_individual_pattern_members(self):
        self.assertEqual(len(self.by_iri[KSG_DIVISION]["options"]), 7)
        # 108, not 109: the division asserting "is defined by" itself is filtered.
        self.assertEqual(len(self.by_iri[CRF_2006_DIVISION]["options"]), 108)
        self.assertNotIn(
            CRF_2006_DIVISION,
            [o["iri"] for o in self.by_iri[CRF_2006_DIVISION]["options"]],
        )

    def test_class_restriction_pattern_members(self):
        # These two divisions are classes whose members carry the division via an
        # rdf:type restriction; the individual-only query missed them entirely.
        self.assertEqual(len(self.by_iri[NC_BR_DIVISION]["options"]), 7)
        self.assertEqual(len(self.by_iri[EU_LEGISLATION_DIVISION]["options"]), 5)

    def test_every_division_option_carries_label_and_iri(self):
        for division in self.divisions:
            self.assertTrue(division["label"])
            self.assertIn(division["kind"], ("individuals", "tree"))
            for option in division["options"]:
                self.assertTrue(option["label"], division["label"])
                self.assertTrue(option["iri"], division["label"])

    def test_other_entry_carries_the_sector_tree(self):
        other = self.divisions[-1]
        self.assertEqual(other["label"], OTHER_DIVISION_LABEL)
        self.assertEqual(other["kind"], "tree")
        self.assertEqual(other["iri"], str(SECTOR_CLASS))
        self.assertTrue(other["options"])
        # a tree, not a flat list
        self.assertTrue(any(node.get("children") for node in other["options"]))

    def test_legacy_flat_sector_list_is_still_served(self):
        self.assertTrue(self.sectors)
        divisions_seen = {sector["sector_division"] for sector in self.sectors}
        self.assertIn(NC_BR_DIVISION, divisions_seen)

    def test_payload_is_memoized(self):
        self.assertIs(build_sector_dropdowns_from_oeo(oeo)[0], self.divisions)
