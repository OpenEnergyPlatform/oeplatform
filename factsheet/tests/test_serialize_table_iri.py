"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase

from factsheet.oekg.filters import OekgQuery


class OekgQueryTests(TestCase):
    def setUp(self):
        self.query = OekgQuery()

    def test_serialize_table_iri_internal_urls(self):
        cases = [
            ("dataedit/view/scenario/test_scenario", "scenario/test_scenario"),
            (
                "https://openenergyplatform.org/dataedit/view/scenario/test_scenario",
                "scenario/test_scenario",
            ),
            (
                "https://databus.openenergyplatform.org/dataedit/view/scenario/test_scenario",  # noqa E501
                "scenario/test_scenario",
            ),
            (
                "http://example.com/dataedit/view/scenario/another_test",
                "scenario/another_test",
            ),
        ]

        for iri, expected in cases:
            with self.subTest(iri=iri):
                result = self.query.serialize_table_iri(iri)
                self.assertEqual(result, expected)

    def test_serialize_table_iri_external_urls(self):
        cases = [
            "https://databus.openenergyplatform.org/koubaa/LLEC_Dataset/WS_23_24",
            "urn:example:dataset:abc",
            "",
            "just-a-string",
        ]

        for iri in cases:
            with self.subTest(iri=iri):
                result = self.query.serialize_table_iri(iri)
                self.assertEqual(result, "")
