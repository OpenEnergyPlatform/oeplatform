"""
Creating a table with a FOREIGN KEY or CHECK constraint returned 201 and
silently dropped the constraint, because the create path only ever recognised
PRIMARY KEY and UNIQUE and fell through for everything else. A FOREIGN KEY is
now built when it names its target (test_table_create_foreign_key); what is
still refused here is refused by name.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from api.actions import has_table
from api.tests import APITestCase


class TestTableCreateConstraintRejection(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        # each test creates its own table; keep the module order-independent so
        # one failure cannot cascade into the next test
        self.empty_test_schema()

    def tearDown(self) -> None:
        self.empty_test_schema()
        super().tearDown()

    def _structure(self, constraints):
        return {
            "columns": [
                {"name": "id", "data_type": "bigint"},
                {"name": "other_id", "data_type": "bigint"},
            ],
            "constraints": constraints,
        }

    def _create_expecting_rejection(self, table, constraints):
        json_resp = self.api_req(
            "put",
            table,
            data={"query": self._structure(constraints)},
            params={"is_sandbox": True},
            exp_code=400,
        )
        # a rejected create must not leave a Main Table behind
        self.assertFalse(has_table({"table": table}))
        return json_resp

    def test_foreign_key_without_a_target_is_rejected_naming_what_is_missing(self):
        # A FOREIGN KEY with a target is created now; see
        # test_table_create_foreign_key. This one names no table to point at.
        json_resp = self._create_expecting_rejection(
            "reject_foreign_key",
            [
                {
                    "constraint_type": "FOREIGN KEY",
                    "columns": ["other_id"],
                    "refcolumns": ["id"],
                }
            ],
        )

        self.assertIn("FOREIGN KEY", json_resp["reason"])
        self.assertIn("target_table", json_resp["reason"])

    def test_check_is_rejected_as_unsupported(self):
        json_resp = self._create_expecting_rejection(
            "reject_check",
            [{"constraint_type": "CHECK", "constraint_parameter": "id > 0"}],
        )

        self.assertIn("CHECK", json_resp["reason"])

    def test_unknown_constraint_type_is_rejected_naming_what_was_sent(self):
        json_resp = self._create_expecting_rejection(
            "reject_unknown",
            [{"constraint_type": "EXCLUDE", "columns": ["id"]}],
        )

        self.assertIn("EXCLUDE", json_resp["reason"])
        self.assertIn("PRIMARY KEY, UNIQUE", json_resp["reason"])

    def test_supported_constraints_still_create_the_table(self):
        table = "accept_pk_and_unique"
        self.create_table(
            table=table,
            structure=self._structure(
                [
                    {"constraint_type": "PRIMARY KEY", "constraint_parameter": "id"},
                    {"constraint_type": "UNIQUE", "columns": ["other_id"]},
                ]
            ),
        )

        described = self.api_req("get", table, auth=False)
        constraint_types = {
            c["constraint_type"] for c in described["constraints"].values()
        }
        self.assertIn("PRIMARY KEY", constraint_types)
        self.assertIn("UNIQUE", constraint_types)
