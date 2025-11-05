"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from dataedit.management.commands.clear_sandbox import (
    clear_sandbox,
    get_sandbox_meta_tables_oedb,
    get_sandbox_tables_django,
    get_sandbox_tables_oedb,
)
from oeplatform.settings import SCHEMA_DEFAULT_TEST_SANDBOX

from . import APITestCase


class TestCommandClearSandbox(APITestCase):
    test_schema = SCHEMA_DEFAULT_TEST_SANDBOX

    def test_clear_sandbox(self):
        # create a test table with data
        # so that sandbox is not empty
        self.create_table(
            table="test_sandbox_table",
            schema=SCHEMA_DEFAULT_TEST_SANDBOX,
            structure={"columns": [{"name": "id", "data_type": "bigint"}]},
            data=[{"id": 1}],
        )

        # check that sandbox is not empty
        self.assertTrue(len(get_sandbox_tables_django()) > 0)
        self.assertTrue(len(get_sandbox_tables_oedb()) > 0)
        self.assertTrue(len(get_sandbox_meta_tables_oedb()) > 0)

        # run the management command
        clear_sandbox(interactive=False)

        # check that sandbox is empty
        self.assertTrue(len(get_sandbox_tables_django()) == 0)
        self.assertTrue(len(get_sandbox_tables_oedb()) == 0)
        self.assertTrue(len(get_sandbox_meta_tables_oedb()) == 0)
