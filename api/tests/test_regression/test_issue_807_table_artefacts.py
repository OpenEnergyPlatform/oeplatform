"""Some api actions run `assert_permission`, which calls
Table.load(table), which used get_or_create().

This caused the creation of an artefact entry in django tables.

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api.actions import assert_permission
from api.tests import APITestCase
from dataedit.models import Table
from oedb.connection import _table_exists_in_oedb
from oeplatform.settings import SCHEMA_DEFAULT_TEST_SANDBOX


class Test_issue_807_table_artefacts(APITestCase):
    schema = SCHEMA_DEFAULT_TEST_SANDBOX  # created in APITestCase
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

        self.assertFalse(_table_exists_in_oedb(self.table, self.schema))
        # this failed before the bugfix
        self.assertFalse(Table.objects.filter(name=self.table).first())
