"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api import actions
from api.tests import APITestCase
from oeplatform.securitysettings import SCHEMA_DEFAULT_TEST_SANDBOX


class TestTableNameUnique(APITestCase):
    schema_sandbox = SCHEMA_DEFAULT_TEST_SANDBOX

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        actions.perform_sql(f"DROP SCHEMA IF EXISTS {cls.schema_sandbox} CASCADE")
        actions.perform_sql(f"CREATE SCHEMA {cls.schema_sandbox}")
        actions.perform_sql(f"DROP SCHEMA IF EXISTS _{cls.schema_sandbox} CASCADE")
        actions.perform_sql(f"CREATE SCHEMA _{cls.schema_sandbox}")

    def test_table_name_unique(self):
        # create table
        self.create_table()

        # create same table
        # should fail
        self.assertRaises(AssertionError, self.create_table, schema=self.schema_sandbox)
