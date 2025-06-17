# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: MIT

import unittest

from django.test import TestCase

from factsheet.utils import serialize_publication_date


class SerializePublicationDateTests(TestCase):
    def test_valid_dates(self):
        self.assertEqual(serialize_publication_date("2022-11-28"), "2022")
        self.assertEqual(serialize_publication_date("2023/8/15"), "2023")
        self.assertEqual(serialize_publication_date("2017-03-06^^xsd:date"), "2017")
        self.assertEqual(serialize_publication_date("2023"), "2023")

    def test_invalid_dates(self):
        self.assertEqual(serialize_publication_date("NaN/NaN/NaN"), "None")
        self.assertEqual(serialize_publication_date(""), "None")
        self.assertEqual(serialize_publication_date("invalid-date"), "None")

    def test_edge_cases(self):
        self.assertEqual(serialize_publication_date(None), "None")
        self.assertEqual(serialize_publication_date("0000-00-00"), "0000")
        self.assertEqual(serialize_publication_date("9999-12-31"), "9999")


if __name__ == "__main__":
    unittest.main()
