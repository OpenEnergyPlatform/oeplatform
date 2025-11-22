"""Some api actions run `assert_permission`, which calls
Table.load(table), which used get_or_create().

This caused the creation of an artefact entry in django tables.

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api.actions import assert_permission
from api.tests import APITestCase
from dataedit.models import Table
from oedb.connection import _get_engine
from oeplatform.settings import SCHEMA_DEFAULT_TEST_SANDBOX


def _table_exists_in_oedb(table):
    """check if table exists in oedb

    Args:
        table (str): table name

    Returns:
        bool
    """
    engine = _get_engine()
    conn = engine.connect()
    try:
        result = engine.dialect.has_table(
            conn, table, schema=SCHEMA_DEFAULT_TEST_SANDBOX
        )
    finally:
        conn.close()
    return result


class Test_issue_807_table_artefacts(APITestCase):
    table = "nonexisting_table"

    def test_issue_807_table_artefacts(self):
        try:
            assert_permission(
                user=self.user,  # created in APITestCase
                table=self.table,
                permission=0,  # any value will do
            )
        except Exception:
            pass

        self.assertFalse(_table_exists_in_oedb(self.table))
        # this failed before the bugfix
        self.assertFalse(Table.objects.filter(name=self.table).first())
