"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

A Table created through the API records when (#2559, spec #2551), and the
creation time is the one the tables tab shows as Created.
"""  # noqa: 501

from django.utils import timezone

from api.tests import APITestCase
from dataedit.models import Table


class TableCreatedTests(APITestCase):
    test_table = "test_table_created"

    def setUp(self):
        super().setUp()
        self.empty_test_schema()

    def tearDown(self):
        self.empty_test_schema()
        super().tearDown()

    def test_creating_a_table_records_its_creation_time(self):
        before = timezone.now()
        self.create_table(
            structure={"columns": [{"name": "id", "data_type": "bigserial"}]}
        )
        created = Table.objects.get(name=self.test_table).created
        self.assertIsNotNone(created)
        self.assertTrue(before <= created <= timezone.now(), created)
