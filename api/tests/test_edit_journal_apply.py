"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Applying the edit journal of a table (issue #2362).

Every row write lands in a meta table (_<name>_insert/_edit/_delete) first and is
then applied to the table. These tests pin the two things #2362 changed that the
row API tests do not reach: changes of different kinds pending at once are all
applied, and the partial index on unapplied journal rows exists - on new meta
tables at creation, on old ones through the oedb migration.
"""  # noqa: 501

import importlib

from django.test import SimpleTestCase
from sqlalchemy import text

from api.actions import apply_changes
from api.tests import APITestCaseWithTable
from dataedit.models import Table
from oedb.connection import _get_engine
from oedb.utils import unapplied_index_name

migration = importlib.import_module(
    "oedb.versions.e3b1f6c2d9a4_index_unapplied_meta_rows"
)


class JournalTestCase(APITestCaseWithTable):
    def setUp(self):
        super().setUp()
        oedb_table = Table.objects.get(name=self.test_table).get_oedb_table_proxy(
            user=None
        )
        self.main = oedb_table._main_table
        self.meta = {
            "insert": oedb_table._insert_table,
            "update": oedb_table._edit_table,
            "delete": oedb_table._delete_table,
        }
        for meta_table in self.meta.values():
            meta_table.get_sa_table()  # created on first use

    def autocommit(self):
        return _get_engine().connect().execution_options(isolation_level="AUTOCOMMIT")

    def journal(self, kind, row_id, name, seconds_ago):
        """Write one unapplied journal entry, as a pending change would be."""
        meta_table = self.meta[kind]
        with _get_engine().begin() as connection:
            connection.execute(
                text(
                    f'INSERT INTO "{meta_table.schema_name}"."{meta_table.name}" '
                    "(_id, id, name, _user, _type, _submitted) VALUES ("
                    "nextval('public._edit_base__id_seq'), :id, :name, 'test', "
                    ":kind, now() - make_interval(secs => :ago))"
                ),
                id=row_id,
                name=name,
                kind=kind,
                ago=seconds_ago,
            )

    def rows(self):
        with _get_engine().connect() as connection:
            return connection.execute(
                f'SELECT id, name FROM "{self.main.schema_name}"."{self.main.name}" '
                "ORDER BY id"
            ).fetchall()

    def pending(self):
        with _get_engine().connect() as connection:
            return sum(
                connection.execute(
                    f'SELECT count(*) FROM "{m.schema_name}"."{m.name}" '
                    "WHERE NOT _applied"
                ).scalar()
                for m in self.meta.values()
            )

    def index_exists(self, meta_table):
        with _get_engine().connect() as connection:
            return (
                connection.execute(
                    text(
                        "SELECT 1 FROM pg_indexes "
                        "WHERE schemaname = :schema AND indexname = :index"
                    ),
                    schema=meta_table.schema_name,
                    index=unapplied_index_name(meta_table.name),
                ).first()
                is not None
            )

    def drop_indexes(self):
        with self.autocommit() as connection:
            for meta_table in self.meta.values():
                connection.execute(
                    f'DROP INDEX IF EXISTS "{meta_table.schema_name}".'
                    f'"{unapplied_index_name(meta_table.name)}"'
                )


class MixedPendingChangesTest(JournalTestCase):
    def test_changes_of_different_kinds_are_all_applied(self):
        # Before #2362 the change that started a new kind was dropped, and the
        # last batch was then applied empty - which raised.
        self.journal("insert", 10, "a", seconds_ago=30)
        self.journal("insert", 11, "b", seconds_ago=20)
        self.journal("delete", 10, None, seconds_ago=10)
        self.journal("insert", 12, "c", seconds_ago=5)

        apply_changes(Table.objects.get(name=self.test_table))

        self.assertEqual([tuple(r) for r in self.rows()], [(11, "b"), (12, "c")])
        self.assertEqual(self.pending(), 0)


class UnappliedIndexTest(JournalTestCase):
    def test_a_new_meta_table_gets_the_index(self):
        for kind, meta_table in self.meta.items():
            with self.subTest(kind=kind):
                self.assertTrue(self.index_exists(meta_table))

    def test_the_migration_adds_missing_indexes(self):
        self.drop_indexes()
        with self.autocommit() as connection:
            skipped = migration.index_meta_tables(
                connection, schema=self.meta["insert"].schema_name
            )
        self.assertEqual(skipped, [])
        for meta_table in self.meta.values():
            self.assertTrue(self.index_exists(meta_table))

    def test_a_locked_meta_table_is_skipped_not_fatal(self):
        self.drop_indexes()
        locked = self.meta["delete"]
        holder = _get_engine().connect()
        transaction = holder.begin()
        try:
            holder.execute(
                f'LOCK TABLE "{locked.schema_name}"."{locked.name}" '
                "IN ACCESS EXCLUSIVE MODE"
            )
            with self.autocommit() as connection:
                skipped = migration.index_meta_tables(
                    connection,
                    lock_timeout="100ms",
                    schema=locked.schema_name,
                )
        finally:
            transaction.rollback()
            holder.close()

        self.assertIn((locked.schema_name, locked.name), skipped)
        self.assertFalse(self.index_exists(locked))
        self.assertTrue(self.index_exists(self.meta["insert"]))


class IndexNameTest(SimpleTestCase):
    """The runtime name and the migration's frozen copy must agree."""

    def test_names_agree_and_fit(self):
        for meta_table_name in (
            "_t_insert",
            "_" + "x" * 41 + "_insert",  # just short enough for the plain name
            "_" + "x" * 55 + "_insert",  # a meta table name of 63
        ):
            with self.subTest(length=len(meta_table_name)):
                name = unapplied_index_name(meta_table_name)
                self.assertEqual(name, migration._index_name(meta_table_name))
                self.assertLessEqual(len(name), 63)
                self.assertNotEqual(name, meta_table_name[:63])

    def test_long_names_of_one_table_stay_distinct(self):
        base = "_" + "y" * 50
        names = {
            unapplied_index_name(base + s) for s in ("_insert", "_edit", "_delete")
        }
        self.assertEqual(len(names), 3)
