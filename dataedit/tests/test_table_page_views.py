"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The saved views of a table (`dataedit.models.View`), issue #2217.

Before the fix the table page inserted a fresh "default" view on every visit, so
production collected ~195,000 of them. These tests pin that a visit is a read,
that a view name can be taken only once per table and type, that the dedupe
migration removes the empty copies without losing anything a user saved, and
that the two endpoints which change views no longer do so from a GET.
"""  # noqa: 501

import importlib

from django.contrib.messages import get_messages
from django.db import OperationalError, connection
from django.test import TestCase
from django.urls import reverse

from base.tests import TestViewsTestCase
from dataedit.models import Filter, Table
from dataedit.models import View as DBView
from login.models import myuser as User

migration_0054 = importlib.import_module(
    "dataedit.migrations.0054_view_unique_table_type_name"
)


class WithTable(TestViewsTestCase):
    """A sandbox table named after the test class, created once per class."""

    table_name: str

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


class TablePageViewsTest(WithTable):
    table_name = "test_table_page_views"

    def test_repeated_visits_create_one_default_view(self):
        for _ in range(3):
            self.assertEqual(self.page().status_code, 200)
        view = self.views().get()
        self.assertEqual(
            (view.name, view.type, view.is_default), ("default", "table", True)
        )

    def test_a_visit_after_the_first_changes_nothing(self):
        self.page()
        before = list(self.views().values_list("pk", "name", "is_default"))
        self.page()
        self.assertEqual(
            list(self.views().values_list("pk", "name", "is_default")), before
        )

    def test_a_view_named_default_but_not_marked_is_marked_once(self):
        DBView.objects.create(table=self.table_name, type="table", name="default")
        self.page()
        self.assertTrue(self.views().get().is_default)

    def test_a_graph_marked_default_does_not_replace_the_table(self):
        # The graph form offers an is_default checkbox. The page's default is
        # the table view, so a default graph must not take over the Table tab.
        DBView.objects.create(
            table=self.table_name, type="graph", name="g", is_default=True
        )
        current = self.page().context["current_view"]
        self.assertEqual((current.type, current.name), ("table", "default"))

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


class ViewNamesTest(WithTable):
    """A name is unique per table and type; reusing one is refused, not a 500."""

    table_name = "test_table_view_names"

    def setUp(self):
        self.client.force_login(self.user)  # the table's creator may write
        self.taken = DBView.objects.create(
            table=self.table_name, type="graph", name="taken"
        )

    def assert_refused_as_taken(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"?view={self.taken.pk}", response.url)
        texts = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('"taken"' in text for text in texts), texts)

    def save(self, **data):
        return self.client.post(
            reverse("dataedit:table-view-save", kwargs={"table": self.table_name}),
            data,
        )

    def test_saving_a_new_view_under_a_taken_name(self):
        response = self.save(name="taken", type="graph")
        self.assert_refused_as_taken(response)
        self.assertEqual(self.views().count(), 1)

    def test_renaming_a_view_onto_a_taken_name(self):
        other = DBView.objects.create(table=self.table_name, type="graph", name="b")
        response = self.save(id=other.pk, name="taken", type="graph")
        self.assert_refused_as_taken(response)
        other.refresh_from_db()
        self.assertEqual(other.name, "b")

    def test_creating_a_graph_under_a_taken_name(self):
        response = self.client.post(
            reverse("dataedit:table-graph", kwargs={"table": self.table_name}),
            {"name": "taken", "column_x": "id", "column_y": "id"},
        )
        self.assert_refused_as_taken(response)
        self.assertEqual(self.views().count(), 1)

    def test_the_same_name_is_fine_for_another_type(self):
        response = self.save(name="taken", type="map")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.views().count(), 2)


class ViewEndpointsTest(WithTable):
    """set-default and delete change data, so a GET (a crawler) must not reach them."""

    table_name = "test_table_view_endpoints"

    def setUp(self):
        self.client.force_login(self.user)  # the table's creator may write
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


def unique_constraint_names(cursor):
    constraints = connection.introspection.get_constraints(
        cursor, DBView._meta.db_table
    )
    return [
        name
        for name, c in constraints.items()
        if c["unique"] and set(c["columns"]) == {"table", "type", "name"}
    ]


class RemoveDuplicateViewsMigrationTest(TestCase):
    """Runs the exact SQL of migration 0054 against duplicates it must clean up.

    The unique constraint the migration adds is dropped inside the test's
    transaction so duplicates can exist; the rollback at the end restores it.
    """

    def setUp(self):
        with connection.cursor() as cursor:
            (name,) = unique_constraint_names(cursor)
            cursor.execute(
                f'ALTER TABLE {DBView._meta.db_table} DROP CONSTRAINT "{name}"'
            )

    def dedupe(self):
        with connection.cursor() as cursor:
            for statement in migration_0054.REMOVE_DUPLICATE_VIEWS:
                cursor.execute(statement)

    def view(self, name="default", type="table", **fields):
        return DBView.objects.create(table="t", type=type, name=name, **fields)

    def remaining(self):
        return DBView.objects.filter(table="t").order_by("pk")

    def test_of_empty_copies_the_newest_stays(self):
        self.view()
        self.view()
        newest = self.view()
        self.dedupe()
        self.assertEqual(list(self.remaining()), [newest])

    def test_of_empty_copies_the_one_marked_default_stays(self):
        marked = self.view(is_default=True)
        self.view()
        self.dedupe()
        self.assertEqual(list(self.remaining()), [marked])

    def test_a_view_with_filters_beats_newer_empty_copies(self):
        saved = self.view()
        kept_filter = Filter.objects.create(
            column="c", type="equal", value=1, view=saved
        )
        self.view(is_default=True)
        self.view()
        self.dedupe()
        self.assertEqual(list(self.remaining()), [saved])
        self.assertEqual(list(Filter.objects.all()), [kept_filter])

    def test_a_view_with_options_counts_as_content(self):
        saved = self.view(name="chart", type="graph", options={"x_axis": "year"})
        self.view(name="chart", type="graph")
        self.dedupe()
        self.assertEqual(list(self.remaining()), [saved])

    def test_two_views_with_content_are_both_kept_one_renamed(self):
        older = self.view(name="chart", type="graph", options={"x_axis": "a"})
        newer = self.view(name="chart", type="graph", options={"x_axis": "b"})
        Filter.objects.create(column="c", type="equal", value=1, view=older)
        self.dedupe()
        older.refresh_from_db()
        newer.refresh_from_db()
        self.assertEqual(newer.name, "chart")
        self.assertEqual(older.name, f"chart ({older.pk})")
        self.assertEqual(older.filter.count(), 1)

    def test_a_renamed_long_name_still_fits(self):
        long_name = "x" * 50
        older = self.view(name=long_name, type="graph", options={"x_axis": "a"})
        self.view(name=long_name, type="graph", options={"x_axis": "b"})
        self.dedupe()
        older.refresh_from_db()
        self.assertLessEqual(len(older.name), 50)
        self.assertTrue(older.name.endswith(f" ({older.pk})"))

    def test_leaves_distinct_views_alone(self):
        distinct = [
            self.view(),
            self.view(type="graph"),
            self.view(name="mine"),
            DBView.objects.create(table="u", type="table", name="default"),
        ]
        self.dedupe()
        self.assertCountEqual(
            list(DBView.objects.filter(table__in=("t", "u"))), distinct
        )

    def test_the_constraint_can_be_added_in_the_same_transaction(self):
        # The migration cleans up, then adds the constraint, in one transaction.
        # Django's foreign keys are DEFERRABLE INITIALLY DEFERRED, so deleting a
        # view leaves FK checks pending, and Postgres refuses to ALTER a table
        # with pending trigger events. An empty table hides this.
        self.view()
        self.view()
        self.view(name="chart", type="graph", options={"x_axis": "a"})
        self.view(name="chart", type="graph", options={"x_axis": "b"})

        self.dedupe()
        with connection.schema_editor() as editor:
            editor.alter_unique_together(DBView, [], [("table", "type", "name")])

        with connection.cursor() as cursor:
            self.assertEqual(len(unique_constraint_names(cursor)), 1)


class MigrationLockTest(TestCase):
    """The cleanup must keep the old code from inserting while it runs.

    The deploy migrates while the previous release still serves pages, and
    that release inserts a "default" view on every visit. One inserted between
    the cleanup and the ALTER would make the unique index fail and roll the
    whole migration back.
    """

    def test_writes_from_another_connection_wait_for_the_migration(self):
        with connection.cursor() as cursor:
            for statement in migration_0054.REMOVE_DUPLICATE_VIEWS:
                cursor.execute(statement)

        other = connection.copy()
        try:
            with other.cursor() as cursor:
                cursor.execute("SET lock_timeout = '200ms'")
                try:
                    cursor.execute(
                        f"INSERT INTO {DBView._meta.db_table} "
                        '(name, "table", type, options, is_default) '
                        "VALUES ('default', 'lock_probe', 'table', '{}', false) "
                        "RETURNING id"
                    )
                except OperationalError:
                    return  # blocked by the migration's lock, as it must be
                # it got through and, autocommitted, is now in the database
                cursor.execute(
                    f"DELETE FROM {DBView._meta.db_table} WHERE id = %s",
                    [cursor.fetchone()[0]],
                )
                self.fail("another connection could insert during the migration")
        finally:
            other.close()


class ViewPermissionTest(WithTable):
    """Changing a table's saved views needs login and write permission on it.

    The views are shown to everyone who opens the table, so changing them is
    changing the table's page.
    """

    table_name = "test_table_view_permissions"

    def setUp(self):
        self.graph = DBView.objects.create(
            table=self.table_name, type="graph", name="g"
        )
        self.reader = User.objects.create_user(  # type: ignore
            name="reader", email="reader@test.test", affiliation="test"
        )

    def requests(self):
        table = {"table": self.table_name}
        view = {"table": self.table_name, "view_id": self.graph.pk}
        yield "post", reverse("dataedit:table-view-save", kwargs=table), {
            "name": "new",
            "type": "graph",
        }
        yield "post", reverse("dataedit:table-view-set-default", kwargs=view), {}
        yield "post", reverse("dataedit:table-view-delete-default", kwargs=view), {}
        yield "get", reverse("dataedit:table-graph", kwargs=table), {}
        yield "post", reverse("dataedit:table-graph", kwargs=table), {"name": "x"}
        yield "get", reverse(
            "dataedit:table-map", kwargs={**table, "maptype": "latlon"}
        ), {}

    def test_an_anonymous_caller_is_sent_to_log_in(self):
        before = self.snapshot()
        for method, url, data in self.requests():
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, data)
                self.assertEqual(response.status_code, 302)
                self.assertIn("login", response.url)
        self.assertEqual(self.snapshot(), before)

    def test_a_logged_in_caller_without_write_permission_is_refused(self):
        self.client.force_login(self.reader)
        before = self.snapshot()
        for method, url, data in self.requests():
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, data)
                self.assertEqual(response.status_code, 403)
        self.assertEqual(self.snapshot(), before)

    def test_saving_reaches_only_a_view_of_the_same_table(self):
        stranger = DBView.objects.create(
            table="some_other_table", type="graph", name="theirs"
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dataedit:table-view-save", kwargs={"table": self.table_name}),
            {"id": stranger.pk, "name": "mine now", "type": "graph"},
        )
        self.assertEqual(response.status_code, 404)
        stranger.refresh_from_db()
        self.assertEqual(stranger.name, "theirs")

    def test_only_a_writer_is_offered_to_add_views(self):
        add_graph = reverse("dataedit:table-graph", kwargs={"table": self.table_name})
        self.assertNotContains(self.page(), add_graph)
        self.client.force_login(self.reader)
        self.assertNotContains(self.page(), add_graph)
        self.client.force_login(self.user)
        self.assertContains(self.page(), add_graph)

    def snapshot(self):
        return list(self.views().order_by("pk").values_list("pk", "name", "is_default"))
