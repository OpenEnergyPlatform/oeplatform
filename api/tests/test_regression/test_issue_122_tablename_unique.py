# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.   # noqa E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from api.actions import has_table
from api.tests import APITestCase
from oeplatform.settings import DATASETS_SCHEMA_TEST, SANDBOX_SCHEMA


class TestTableNameUnique(APITestCase):
    def test_table_name_unique(self):
        # create table in default (test) schema
        self.create_table(schema=DATASETS_SCHEMA_TEST)

        # create same table in another (sandbox) schema
        # should fail
        self.assertRaises(AssertionError, self.create_table, schema=SANDBOX_SCHEMA)

        # also check: table should not have been created in oedb
        self.assertFalse(
            has_table({"table": self.test_table, "schema": SANDBOX_SCHEMA})
        )
