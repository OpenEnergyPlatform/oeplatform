"""Creating a table with a FOREIGN KEY, the way `oedialect` sends it.

`oedialect` sends every foreign key twice when it creates a table: once on the
column (`"foreign_key": [{"schema", "table", "column"}]`) and once as a table
constraint (`{"constraint_type": "foreign_key", "target_table", ...}`), because
SQLAlchemy lists the same key under `table.foreign_key_constraints` too.

Before v1.9.0 the table constraint was silently dropped and the column entry
created the key. `df393ee32` stopped the silent drop by *rejecting* a table
FOREIGN KEY, and its message pointed at the table change queue -- which has
never applied anything (#2490). So from v1.9.0 on, every `create_all` with a
foreign key through the dialect answered 400 and there was no route left that
would add one.

The create path now builds a table FOREIGN KEY, and skips one that only repeats
a column's. The first test compiles its body with the installed dialect, so it
fails if the dialect's wire format and this parser drift apart again.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import sqlalchemy as sa
from oedialect.dialect import OEDialect
from sqlalchemy.schema import CreateTable

from api.actions import has_table
from api.tests import APITestCase

PARENT = "fk_create_parent"


def dialect_body(child, parent=PARENT, schema=None):
    """The `columns` and `constraints` `oedialect` sends to create `child`."""
    md = sa.MetaData()
    sa.Table(
        parent, md, sa.Column("id", sa.BigInteger, primary_key=True), schema=schema
    )
    target = f"{schema}.{parent}.id" if schema else f"{parent}.id"
    table = sa.Table(
        child,
        md,
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("parent_id", sa.BigInteger, sa.ForeignKey(target)),
        schema=schema,
    )
    body = CreateTable(table).compile(dialect=OEDialect()).string
    return {"columns": body["columns"], "constraints": body["constraints"]}


def child_structure(constraints):
    return {
        "columns": [
            {"name": "id", "data_type": "bigint"},
            {"name": "parent_id", "data_type": "bigint"},
        ],
        "constraints": [
            {"constraint_type": "PRIMARY KEY", "constraint_parameter": "id"},
            *constraints,
        ],
    }


class TableCreateForeignKeyTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.empty_test_schema()
        self.create_table(
            table=PARENT,
            structure={
                "columns": [{"name": "id", "data_type": "bigint"}],
                "constraints": [
                    {"constraint_type": "PRIMARY KEY", "constraint_parameter": "id"}
                ],
            },
        )

    def tearDown(self):
        self.empty_test_schema()
        super().tearDown()

    def foreign_keys(self, table):
        described = self.api_req("get", table, auth=False)
        return [
            c["definition"]
            for c in described["constraints"].values()
            if c["constraint_type"] == "FOREIGN KEY"
        ]

    def refused(self, table, structure, code=400):
        response = self.api_req(
            "put",
            table,
            data={"query": structure},
            params={"is_sandbox": True},
            exp_code=code,
        )
        self.assertFalse(has_table({"table": table}))
        return response["reason"]

    def test_the_body_oedialect_sends_creates_the_key(self):
        self.create_table(table="fk_dialect", structure=dialect_body("fk_dialect"))

        [key] = self.foreign_keys("fk_dialect")
        self.assertIn("FOREIGN KEY (parent_id) REFERENCES", key)
        self.assertIn(f"{PARENT}(id)", key)

    def test_a_schema_qualified_target_resolves_by_table_name(self):
        # The dialect qualifies the target when the model does; table names
        # are globally unique here, so the name alone identifies it.
        body = dialect_body("fk_qualified", schema="model_draft")
        for column in body["columns"]:
            for fk in column["foreign_key"]:
                fk["schema"] = None  # the column half resolves by name already
        self.create_table(table="fk_qualified", structure=body)

        self.assertEqual(1, len(self.foreign_keys("fk_qualified")))

    def test_a_table_level_key_alone_creates_it(self):
        self.create_table(
            table="fk_table_level",
            structure=child_structure(
                [
                    {
                        "constraint_type": "FOREIGN KEY",
                        "columns": ["parent_id"],
                        "target_table": PARENT,
                        "target_columns": ["id"],
                    }
                ]
            ),
        )

        self.assertEqual(1, len(self.foreign_keys("fk_table_level")))

    def test_the_documented_reference_fields_create_it_too(self):
        # The shape the older payloads in this suite use for a PRIMARY KEY.
        self.create_table(
            table="fk_reference_fields",
            structure=child_structure(
                [
                    {
                        "constraint_type": "FOREIGN KEY",
                        "constraint_parameter": "parent_id",
                        "reference_table": PARENT,
                        "reference_column": "id",
                    }
                ]
            ),
        )

        self.assertEqual(1, len(self.foreign_keys("fk_reference_fields")))

    def test_a_key_without_a_target_is_refused_naming_what_is_missing(self):
        reason = self.refused(
            "fk_no_target",
            child_structure(
                [
                    {
                        "constraint_type": "FOREIGN KEY",
                        "columns": ["parent_id"],
                        "refcolumns": ["id"],
                    }
                ]
            ),
        )

        self.assertIn("target_table", reason)

    def test_a_key_to_a_missing_table_is_refused(self):
        self.refused(
            "fk_missing_target",
            child_structure(
                [
                    {
                        "constraint_type": "FOREIGN KEY",
                        "columns": ["parent_id"],
                        "target_table": "no_such_table_here",
                        "target_columns": ["id"],
                    }
                ]
            ),
            code=404,
        )

    def test_a_referential_action_is_refused_rather_than_dropped(self):
        # ON DELETE / ON UPDATE are not built here. Dropping them silently is
        # the defect df393ee32 existed to stop, so they are refused by name.
        reason = self.refused(
            "fk_cascade",
            child_structure(
                [
                    {
                        "constraint_type": "FOREIGN KEY",
                        "columns": ["parent_id"],
                        "target_table": PARENT,
                        "target_columns": ["id"],
                        "cascades": " ON DELETE CASCADE",
                    }
                ]
            ),
        )

        self.assertIn("ON DELETE CASCADE", reason)
