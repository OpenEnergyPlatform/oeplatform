# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut  # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from api.actions import has_table
from api.tests import APITestCase
from oeplatform.settings import SANDBOX_SCHEMA


class TestTableNameUnique(APITestCase):
    def test_tables_should_not_exists_on_error(self):
        test_duplicate_column_table_name = "table_column_duplicate"
        # create table with duplicated column names will should an error
        duplicate_field_error_data_struct = {
            "columns": [
                {"name": "id", "data_type": "bigint"},
                {"name": "id", "data_type": "bigint"},
            ]
        }
        # create table in default (test) schema (django_db)
        self.assertRaises(
            AssertionError,
            self.create_table,
            table=test_duplicate_column_table_name,
            structure=duplicate_field_error_data_struct,
            schema=SANDBOX_SCHEMA,
        )

        # also check: table should not have been created in oedb
        self.assertFalse(
            has_table(
                {
                    "table": test_duplicate_column_table_name,
                    "schema": SANDBOX_SCHEMA,
                }
            )
        )
