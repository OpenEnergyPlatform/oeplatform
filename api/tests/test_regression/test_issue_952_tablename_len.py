"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from functools import partial

from api.tests import APITestCase
from oedb.utils import MAX_NAME_LENGTH


class TestTableNameLength(APITestCase):
    def test_table_name_length(self):
        structure = {"columns": [{"name": "id", "data_type": "bigint"}]}
        structure_bad = {
            "columns": [
                {"name": "id", "data_type": "bigint"},
                {"name": "BadName", "data_type": "bigint"},
            ]
        }
        table_ok = "t" + "_" * (MAX_NAME_LENGTH - 1)
        table_too_long = "t" + "_" * (MAX_NAME_LENGTH)
        table_bad_name = "table_Bad"

        # this should fail (too long table name)
        self.assertRaises(
            AssertionError,
            partial(self.create_table, structure, table=table_too_long),
        )

        # this should fail  (bad table name)
        self.assertRaises(
            AssertionError,
            partial(self.create_table, structure, table=table_bad_name),
        )

        # this should fail (bad column name)
        self.assertRaises(
            AssertionError,
            partial(self.create_table, structure_bad, table=table_ok),
        )

        # this works
        self.create_table(structure, table=table_ok)
