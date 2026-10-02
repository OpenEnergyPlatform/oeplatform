"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The saved views of a table (`dataedit.models.View`), issue #2217.

Before the fix the table page inserted a fresh "default" view on every visit, so
production collected ~195,000 of them. These tests pin that a visit is a read, that
the dedupe migration keeps the right row, and that the two endpoints which change
views no longer do so from a GET.
"""  # noqa: 501

import importlib

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from base.tests import TestViewsTestCase
from dataedit.models import Filter, Table
from dataedit.models import View as DBView

migration_0054 = importlib.import_module(
    "dataedit.migrations.0054_view_unique_table_type_name"
)


class TablePageViewsTest(TestViewsTestCase):
    table_name = "test_table_page_views"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.table = Table.create_with_oedb_table(
            is_sandbox=True,
            name=cls.table_name,
            user=cls.user,
            column_definitions=[],
            constraints_definitions=[],
        )

    @classmethod
    def tearDownClass(cls):
        cls.table.delete()
        super().tearDownClass()

    def page(self, **query):
        return self.client.get(
            reverse("dataedit:view", kwargs={"table": self.table_name}), query
        )

    def views(self):
        return DBView.objects.filter(table=self.table_name)

    def test_repeated_visits_create_one_default_view(self):
        for _ in range(3):
            self.assertEqual(self.page().status_code, 200)
        self.assertEqual(self.views().count(), 1)
        view = self.views().get()
        self.assertEqual(
            (view.name, view.type, view.is_default), ("default", "table", True)
        )

    def test_a_visit_after_the_first_writes_nothing(self):
        self.page()
        with CaptureQueriesContext(connection) as queries:
            self.page()
        writes = [
            q["sql"]
            for q in queries.captured_queries
            if "dataedit_view" in q["sql"]
            and q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
        ]
        self.assertEqual(writes, [])

    def test_a_view_named_default_but_not_marked_is_marked_once(self):
        DBView.objects.create(table=self.table_name, type="table", name="default")
        self.page()
        self.assertEqual(self.views().count(), 1)
        self.assertTrue(self.views().get().is_default)

    def test_the_requested_view_is_shown(self):
        graph = DBView.objects.create(table=self.table_name, type="graph", name="g")
        response = self.page(view=graph.pk)
        self.assertEqual(response.context["current_view"].pk, graph.pk)

    def test_an_unknown_or_malformed_view_falls_back_to_the_default(self):
        for value in ("999999", "default", "not-a-number"):
            with self.subTest(view=value):
                response = self.page(view=value)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["current_view"].name, "default")


class ViewEndpointsTest(TestViewsTestCase):
    """set-default and delete change data, so a GET (a crawler) must not reach them."""

    table_name = "test_table_view_endpoints"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.table = Table.create_with_oedb_table(
            is_sandbox=True,
            name=cls.table_name,
            user=cls.user,
            column_definitions=[],
            constraints_definitions=[],
        )

    @classmethod
    def tearDownClass(cls):
        cls.table.delete()
        super().tearDownClass()

    def setUp(self):
        self.default = DBView.objects.create(
            table=self.table_name, type="table", name="default", is_default=True
        )
        self.other = DBView.objects.create(
            table=self.table_name, type="graph", name="other"
        )

    def url(self, name, view):
        # a real table name, with underscores: the routes used to accept digits only
        return reverse(name, kwargs={"table": self.table_name, "view_id": view.pk})

    def test_get_is_refused(self):
        for name in (
            "dataedit:table-view-set-default",
            "dataedit:table-view-delete-default",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.get(self.url(name, self.other)).status_code, 405
                )
        self.assertTrue(DBView.objects.filter(pk=self.other.pk).exists())
        self.default.refresh_from_db()
        self.assertTrue(self.default.is_default)

    def test_set_default_moves_the_flag(self):
        response = self.client.post(
            self.url("dataedit:table-view-set-default", self.other)
        )
        self.assertEqual(response.status_code, 302)
        self.default.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(
            (self.default.is_default, self.other.is_default), (False, True)
        )

    def test_delete_removes_the_view(self):
        response = self.client.post(
            self.url("dataedit:table-view-delete-default", self.other)
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(DBView.objects.filter(pk=self.other.pk).exists())

    def test_a_view_of_another_table_is_not_found(self):
        stranger = DBView.objects.create(
            table="some_other_table", type="graph", name="x"
        )
        for name in (
            "dataedit:table-view-set-default",
            "dataedit:table-view-delete-default",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.post(self.url(name, stranger)).status_code, 404
                )
        self.assertTrue(DBView.objects.filter(pk=stranger.pk).exists())


class RemoveDuplicateViewsMigrationTest(TestCase):
    """Runs the exact SQL of migration 0054 against duplicates it must clean up.

    The unique constraint the migration adds is dropped inside the test's
    transaction so duplicates can exist; the rollback at the end restores it.
    """

    def setUp(self):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, DBView._meta.db_table
            )
            (name,) = [
                n
                for n, c in constraints.items()
                if c["unique"] and set(c["columns"]) == {"table", "type", "name"}
            ]
            cursor.execute(
                f'ALTER TABLE {DBView._meta.db_table} DROP CONSTRAINT "{name}"'
            )

    def dedupe(self):
        with connection.cursor() as cursor:
            for statement in migration_0054.REMOVE_DUPLICATE_VIEWS:
                cursor.execute(statement)

    def test_the_constraint_can_be_added_in_the_same_transaction(self):
        # The migration deletes, then adds the constraint, in one transaction.
        # Django's foreign keys are DEFERRABLE INITIALLY DEFERRED, so deleting a
        # view leaves FK checks pending, and Postgres refuses to ALTER a table
        # with pending trigger events. An empty table hides this; deleted rows
        # that a filter pointed at do not.
        doomed = DBView.objects.create(table="t", type="table", name="default")
        DBView.objects.create(table="t", type="table", name="default")
        Filter.objects.create(column="c", type="equal", value=1, view=doomed)

        self.dedupe()
        with connection.schema_editor() as editor:
            editor.alter_unique_together(DBView, [], [("table", "type", "name")])

    def test_keeps_the_newest_of_unmarked_duplicates_and_their_filters_go(self):
        older = [
            DBView.objects.create(table="t", type="table", name="default")
            for _ in range(3)
        ]
        newest = DBView.objects.create(table="t", type="table", name="default")
        Filter.objects.create(column="c", type="equal", value=1, view=older[0])
        kept_filter = Filter.objects.create(
            column="c", type="equal", value=2, view=newest
        )

        self.dedupe()

        self.assertEqual(list(DBView.objects.filter(table="t")), [newest])
        self.assertEqual(list(Filter.objects.all()), [kept_filter])

    def test_prefers_the_view_marked_default_over_a_newer_one(self):
        marked = DBView.objects.create(
            table="t", type="table", name="default", is_default=True
        )
        DBView.objects.create(table="t", type="table", name="default")

        self.dedupe()

        self.assertEqual(list(DBView.objects.filter(table="t")), [marked])

    def test_leaves_distinct_views_alone(self):
        distinct = [
            DBView.objects.create(table="t", type="table", name="default"),
            DBView.objects.create(table="t", type="graph", name="default"),
            DBView.objects.create(table="t", type="table", name="mine"),
            DBView.objects.create(table="u", type="table", name="default"),
        ]

        self.dedupe()

        self.assertCountEqual(list(DBView.objects.all()), distinct)
