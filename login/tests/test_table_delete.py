"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Delete from the tables tab (#2562, spec #2551), through the row's ⋯ menu and
the table action service, as seen through HTTP: the role gate, the
consequences the dialog states, the typed confirmation the server enforces,
the ceiling, the order of work across the two databases, and the failed
drop reported as a lasting warning.

Assertions are on what the user is offered and told, what both databases
hold afterwards, which response headers came back and which log lines were
written; never on seconds.
"""  # noqa: 501

import uuid
from datetime import timedelta
from unittest import mock

from django.db import connection, models
from django.utils import timezone
from psycopg2.errorcodes import LOCK_NOT_AVAILABLE
from sqlalchemy.exc import OperationalError

from api.services import table_actions
from dataedit.models import (
    Dataset,
    Embargo,
    PeerReview,
    PeerReviewManager,
    ReviewRound,
    Table,
)
from login.models import DELETE_PERM, WRITE_PERM, UserPermission
from login.tests.test_table_actions import DIALOG, ActionTestCase
from modelview.tests.html import element_with_id
from oedb.connection import _get_engine
from oedb.utils import OedbTableProxy


class DeleteTestCase(ActionTestCase):
    def oedb_table(self, title=None, name=None):
        """A sandbox Table with a real OEDB table behind it, on a name no
        other session uses (the OEDB is shared even with an isolated test
        database). Dropped at the end whatever the test did."""
        name = name or f"t_2562_{uuid.uuid4().hex[:10]}"
        table = Table.create_with_oedb_table(
            name=name,
            is_sandbox=True,
            user=self.user,
            column_definitions=[],
            constraints_definitions=[],
        )
        if title:
            Table.objects.filter(pk=table.pk).update(human_readable_name=title)
        self.addCleanup(self.proxy(name).drop_if_exists)
        return table

    def proxy(self, name):
        return OedbTableProxy(
            validated_table_name=name,
            schema_name=Table.get_oedb_schema(is_sandbox=True),
            permission_level=DELETE_PERM,
        )

    def in_oedb(self, name):
        return self.proxy(name).exists()

    def exists(self, *names):
        return set(Table.objects.filter(name__in=names).values_list("name", flat=True))

    def html(self, response):
        return response.content.decode()

    def review(self, name, finished):
        PeerReview.objects.create(
            table=name,
            contributor=self.user,
            reviewer=self.stranger,
            is_finished=finished,
            review={"badge": "Gold"},
        )


class DeleteMenuTests(DeleteTestCase):
    def menu_entry(self, table):
        return element_with_id(
            self.html(self.get(htmx=True)), f"menu-{table.pk}-delete"
        )

    def test_a_data_maintainer_is_offered_delete_on_drafts_and_published(self):
        for published in (False, True):
            Table.objects.all().delete()
            table = self.draft(
                f"t_menu_{int(published)}", level=DELETE_PERM, published=published
            )
            with self.subTest(published=published):
                entry = self.menu_entry(table)
                self.assertIn(
                    f'hx-get="{self.action_path("delete")}?table={table.name}"',
                    entry,
                )
                self.assertNotIn("aria-disabled", entry)

    def test_a_data_editor_sees_it_disabled_with_the_reason(self):
        table = self.draft("t_menu_editor", level=WRITE_PERM)
        response = self.get(htmx=True)
        entry = element_with_id(self.html(response), f"menu-{table.pk}-delete")
        self.assertIn('aria-disabled="true"', entry)
        self.assertNotIn("hx-get", entry)
        self.assertContains(
            response, "Only Data maintainers and Table admins can delete"
        )


class DeletePreflightTests(DeleteTestCase):
    def test_a_draft_asks_for_a_plain_confirmation(self):
        self.draft("t_plain", title="Plain")
        response = self.preflight("delete", "t_plain")
        check = response.context["preflight"]
        self.assertEqual(check.names, ["t_plain"])
        self.assertEqual(check.confirmation, "")
        self.assertFalse(check.consequences["knowledge_graph"])
        html = self.html(response)
        self.assertEqual(element_with_id(html, "action-confirm"), "")
        self.assertNotEqual(element_with_id(html, "table-action-confirm"), "")

    def test_a_platform_admin_is_not_told_of_a_strangers_draft(self):
        # deleting strips the Table from the draft; the dialog stays silent
        # about it, for an admin too (only the operator log names it)
        self.user.is_admin = True
        self.user.save()
        table = self.draft("t_in_a_draft", title="In a draft", published=True)
        Dataset.objects.create(
            name="ds_their_draft",
            creator=self.stranger,
            metadata={"title": "Secret plan"},
        ).tables.add(table)
        response = self.preflight("delete", "t_in_a_draft")
        self.assertEqual(
            response.context["preflight"].consequences["others_datasets"], []
        )
        self.assertNotIn("Secret plan", self.html(response))

    def test_a_published_table_states_what_deleting_breaks(self):
        table = self.draft("t_cited", title="Cited", published=True)
        Dataset.objects.create(
            name="ds_mine", creator=self.user, metadata={"title": "Wind atlas"}
        ).tables.add(table)
        Dataset.objects.create(
            name="ds_theirs",
            creator=self.stranger,
            metadata={"title": "Grid study"},
            published_at=timezone.now(),
        ).tables.add(table)
        # a stranger's draft holding the Table is never named or counted
        Dataset.objects.create(
            name="ds_their_draft",
            creator=self.stranger,
            metadata={"title": "Secret plan"},
        ).tables.add(table)
        self.review("t_cited", finished=True)
        Embargo.objects.create(table=table, duration="6_months")
        response = self.preflight("delete", "t_cited")
        c = response.context["preflight"].consequences
        self.assertEqual(c["published"], [table])
        self.assertEqual(c["own_datasets"], [("Wind atlas", 1)])
        self.assertEqual(c["others_datasets"], [(self.stranger.name, "Grid study", 1)])
        self.assertEqual(c["reviewed"], [(table, "Reviewed")])
        self.assertEqual([t for t, _ in c["embargoed"]], [table])
        self.assertTrue(c["knowledge_graph"])
        html = self.html(response)
        self.assertNotIn("Secret plan", html)
        for element in (
            "table-action-published",
            "table-action-own-datasets",
            "table-action-datasets",
            "table-action-knowledge-graph",
        ):
            with self.subTest(element=element):
                self.assertNotEqual(element_with_id(html, element), "")

    def test_an_open_review_and_an_ended_embargo(self):
        table = self.draft("t_open", published=True)
        self.review("t_open", finished=False)
        embargo = Embargo.objects.create(table=table, duration="6_months")
        # save() derives the end from the duration; an ended one is set past it
        Embargo.objects.filter(pk=embargo.pk).update(
            date_ended=timezone.now() - timedelta(days=1)
        )
        c = self.check("delete", "t_open").consequences
        self.assertEqual(c["reviewed"], [(table, "In review")])
        self.assertEqual(c["embargoed"], [])

    def test_one_published_table_is_confirmed_by_typing_its_name(self):
        self.draft("t_by_name", title="By name", published=True)
        response = self.preflight("delete", "t_by_name")
        self.assertEqual(response.context["preflight"].confirmation, "t_by_name")
        self.assertNotEqual(element_with_id(self.html(response), "action-confirm"), "")

    def test_a_batch_is_confirmed_by_typing_its_count(self):
        for name in ("t_b0", "t_b1", "t_b2"):
            self.draft(name)
        self.assertEqual(self.check("delete", "t_b0", "t_b1").confirmation, "")
        self.draft("t_b_pub", published=True)
        self.assertEqual(self.check("delete", "t_b0", "t_b_pub").confirmation, "2")
        many = [f"t_many_{i}" for i in range(table_actions.TYPED_COUNT_ABOVE + 1)]
        for name in many:
            self.draft(name)
        self.assertEqual(self.check("delete", *many).confirmation, str(len(many)))
        at_limit = many[: table_actions.TYPED_COUNT_ABOVE]
        self.assertEqual(self.check("delete", *at_limit).confirmation, "")

    def test_below_data_maintainer_is_left_out(self):
        self.draft("t_ok")
        self.draft("t_editor", level=WRITE_PERM)
        check = self.check("delete", "t_ok", "t_editor")
        self.assertEqual(check.names, ["t_ok"])
        self.assertEqual(
            {group.reason: group.names for group in check.left_out},
            {"Only Data maintainers and Table admins can delete": ["t_editor"]},
        )

    def test_the_ceiling_is_stated_and_nothing_can_be_confirmed_over_it(self):
        for name in ("t_c0", "t_c1", "t_c2"):
            self.draft(name)
        with mock.patch.dict(table_actions.CEILINGS, {"delete": 2}):
            response = self.preflight("delete", "t_c0", "t_c1", "t_c2")
        check = response.context["preflight"]
        self.assertEqual(check.ceiling, 2)
        self.assertTrue(check.over_ceiling)
        self.assertContains(
            response, "Delete takes at most 2 tables at a time; you selected 3."
        )
        self.assertEqual(
            element_with_id(self.html(response), "table-action-confirm"), ""
        )

    def test_the_ceiling_is_set(self):
        self.assertGreater(table_actions.CEILINGS["delete"], 1)

    def test_a_preflight_deletes_nothing(self):
        self.draft("t_kept")
        self.check("delete", "t_kept")
        self.assertEqual(self.exists("t_kept"), {"t_kept"})


class DeleteTests(DeleteTestCase):
    def test_a_draft_goes_from_both_databases(self):
        table = self.oedb_table(title="Gone")
        Dataset.objects.create(name="ds_left", creator=self.user).tables.add(table)
        self.assertTrue(self.in_oedb(table.name))
        response = self.run_action("delete", table.name)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.exists(table.name), set())
        self.assertFalse(UserPermission.objects.filter(table_id=table.pk).exists())
        self.assertFalse(Dataset.objects.get(name="ds_left").tables.exists())
        self.assertFalse(self.in_oedb(table.name))
        detail = self.trigger(response, "tables-changed")
        # ``gone`` lets the bulk selection drop it (#2564)
        self.assertEqual(detail, {"message": "Deleted “Gone”.", "gone": [table.name]})

    def test_every_dataset_it_leaves_is_stamped_without_a_word_of_it(self):
        """Losing a member is a Modification of the Dataset (#2619), whoever
        made the Dataset: a stranger's draft included, which the deleter is
        never told of. A Dataset the Table was not in keeps its stamp."""
        table = self.draft("t_stamping_delete", published=True)
        long_ago = timezone.now() - timedelta(days=2000)
        mine = Dataset.objects.create(name="ds_stamp_mine", creator=self.user)
        their_draft = Dataset.objects.create(
            name="ds_stamp_secret", creator=self.stranger, metadata={"title": "Secret"}
        )
        Dataset.objects.create(name="ds_stamp_other", creator=self.user)
        mine.tables.add(table)
        their_draft.tables.add(table)
        Dataset.objects.update(modified_at=long_ago)
        before = timezone.now()
        response = self.run_action("delete", table.name, confirm=table.name)
        self.assertEqual(response.status_code, 204)
        stamps = dict(Dataset.objects.values_list("name", "modified_at"))
        self.assertGreaterEqual(stamps["ds_stamp_mine"], before)
        self.assertGreaterEqual(stamps["ds_stamp_secret"], before)
        self.assertEqual(stamps["ds_stamp_other"], long_ago)
        said = response["HX-Trigger"]
        for word in ("ds_stamp_secret", "Secret"):
            self.assertNotIn(word, said)

    def test_a_published_table_without_its_name_typed_is_kept(self):
        table = self.oedb_table(title="Typed")
        Table.objects.filter(pk=table.pk).update(is_publish=True)
        for confirm in ("", "Typed", "t_2562", " wrong "):
            with self.subTest(confirm=confirm):
                response = self.run_action("delete", table.name, confirm=confirm)
                self.assertEqual(response.status_code, 400)
                self.assertTemplateUsed(response, DIALOG)
                self.assertIn("confirm", response.context["errors"])
                # the dialog's own input: no toast
                self.assertNotIn("HX-Trigger", response)
                self.assertEqual(self.exists(table.name), {table.name})
                self.assertTrue(self.in_oedb(table.name))

    def test_a_published_table_with_its_name_typed_goes(self):
        table = self.oedb_table()
        Table.objects.filter(pk=table.pk).update(is_publish=True)
        response = self.run_action("delete", table.name, confirm=f" {table.name} ")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.exists(table.name), set())
        self.assertFalse(self.in_oedb(table.name))

    def test_a_batch_needs_its_count_typed(self):
        self.draft("t_n0")
        self.draft("t_n1", published=True)
        response = self.run_action("delete", "t_n0", "t_n1", confirm="t_n1")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.exists("t_n0", "t_n1"), {"t_n0", "t_n1"})
        response = self.run_action("delete", "t_n0", "t_n1", confirm="2")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.exists("t_n0", "t_n1"), set())
        self.assertEqual(
            self.trigger(response, "tables-changed")["message"], "Deleted 2 tables."
        )

    def test_a_draft_published_since_the_dialog_now_needs_its_name(self):
        """What has to be typed is decided on the Tables as they are when
        the request runs, not as the dialog showed them."""
        self.draft("t_since")
        Table.objects.filter(name="t_since").update(is_publish=True)
        response = self.run_action("delete", "t_since")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.context["preflight"].confirmation, "t_since")
        self.assertEqual(self.exists("t_since"), {"t_since"})

    def test_a_table_no_longer_allowed_refuses_the_whole_request(self):
        self.draft("t_fine")
        demoted = self.draft("t_demoted")
        UserPermission.objects.filter(table=demoted).update(level=WRITE_PERM)
        response = self.run_action("delete", "t_fine", "t_demoted")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.exists("t_fine", "t_demoted"), {"t_fine", "t_demoted"})
        message = self.trigger(response, "tables-refused")["message"]
        self.assertTrue(message.startswith("Nothing was changed:"), message)

    def test_over_the_ceiling_nothing_is_deleted(self):
        for name in ("t_o0", "t_o1", "t_o2"):
            self.draft(name)
        with mock.patch.dict(table_actions.CEILINGS, {"delete": 2}):
            response = self.run_action("delete", "t_o0", "t_o1", "t_o2", confirm="3")
        self.assertEqual(response.status_code, 400)
        self.assertIn("at most 2 tables", response.context["errors"]["table"])
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(self.exists("t_o0", "t_o1", "t_o2"), {"t_o0", "t_o1", "t_o2"})

    def test_the_oedb_table_is_dropped_after_the_rows_have_committed(self):
        """The drop runs once ``execute``'s transaction is left, so when it
        runs the Django rows are already gone, and no transaction of the
        service's own is open around it."""
        table = self.oedb_table()
        outside = len(connection.atomic_blocks)
        seen = []
        real = Table.drop_oedb_table

        def observe(instance, lock_timeout=None):
            seen.append(
                (
                    Table.objects.filter(name=instance.name).exists(),
                    len(connection.atomic_blocks),
                )
            )
            real(instance)

        with mock.patch.object(Table, "drop_oedb_table", observe):
            response = self.run_action("delete", table.name)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(seen, [(False, outside)])
        self.assertFalse(self.in_oedb(table.name))

    def test_a_failed_drop_is_a_lasting_warning_naming_the_table(self):
        stuck = self.oedb_table(title="Stuck")
        fine = self.oedb_table(title="Fine")
        Table.objects.filter(pk=fine.pk).update(is_publish=True)
        real = Table.drop_oedb_table

        def fail_on_stuck(instance, lock_timeout=None):
            if instance.name == stuck.name:
                raise RuntimeError("the OEDB went away")
            real(instance)

        with mock.patch.object(Table, "drop_oedb_table", fail_on_stuck):
            with self.assertLogs("oeplatform.table_actions", "INFO") as logs:
                response = self.run_action("delete", stuck.name, fine.name, confirm="2")
        self.assertEqual(response.status_code, 204)
        # the rows of both are gone; only the stuck one's data is left
        self.assertEqual(self.exists(stuck.name, fine.name), set())
        self.assertTrue(self.in_oedb(stuck.name))
        self.assertFalse(self.in_oedb(fine.name))
        detail = self.trigger(response, "tables-changed")
        self.assertIs(detail["warning"], True)
        self.assertTrue(detail["message"].startswith("Deleted 2 tables."))
        self.assertIn(f"“Stuck” ({stuck.name}) could not be removed", detail["message"])
        self.assertNotIn("Fine", detail["message"])
        by_table = {record.getMessage().split()[1]: record for record in logs.records}
        self.assertEqual(by_table[f"table={stuck.name}"].levelname, "WARNING")
        self.assertIsNotNone(by_table[f"table={stuck.name}"].exc_info)
        self.assertTrue(
            by_table[f"table={stuck.name}"]
            .getMessage()
            .endswith("published=no drop=failed")
        )
        self.assertTrue(by_table[f"table={fine.name}"].getMessage().endswith("drop=ok"))

    def test_after_deleting_the_re_fetch_no_longer_lists_it(self):
        self.draft("t_listed")
        self.draft("t_other")
        self.run_action("delete", "t_listed")
        page = self.page(htmx=True, HTTP_HX_TRIGGER="tables-results")
        self.assertEqual([row.table.name for row in page.rows], ["t_other"])
        self.assertEqual(page.counts["all"], 1)


class DeleteLogTests(DeleteTestCase):
    def test_one_line_per_table_with_datasets_status_and_drop(self):
        a = self.draft("t_log_a", published=True)
        self.draft("t_log_b")
        Dataset.objects.create(name="ds_x", creator=self.user).tables.add(a)
        Dataset.objects.create(name="ds_y", creator=self.stranger).tables.add(a)
        with self.assertLogs("oeplatform.table_actions", "INFO") as logs:
            self.run_action("delete", "t_log_a", "t_log_b", confirm="2")
        lines = [record.getMessage() for record in logs.records]
        batch = lines[0].split("batch=")[1].split()[0]
        self.assertNotEqual(batch, "-")
        self.assertEqual(
            lines,
            [
                f"table_action table=t_log_a action=delete by={self.user.pk} "
                f"via=dashboard batch={batch} datasets=ds_x,ds_y published=yes "
                f"drop=ok",
                f"table_action table=t_log_b action=delete by={self.user.pk} "
                f"via=dashboard batch={batch} datasets=- published=no drop=ok",
            ],
        )

    def test_a_refused_delete_logs_nothing(self):
        self.draft("t_log_refused", published=True)
        with self.assertNoLogs("oeplatform.table_actions", "INFO"):
            self.run_action("delete", "t_log_refused", confirm="nope")
        self.assertEqual(self.exists("t_log_refused"), {"t_log_refused"})


class BlockedDropTests(DeleteTestCase):
    """A drop queued behind another session's lock gives up after
    ``table_actions.DROP_LOCK_TIMEOUT`` in a request and is reported as a
    failed drop (#2597)."""

    def hold_lock(self, name):
        """Open a second OEDB session that holds a lock on ``name``'s main
        table until the test ends: a reader inside an open transaction.

        If the drop did not give up, the test would wait on its own lock
        for ever; the session therefore ends itself once it has sat idle in
        its transaction for a while, which lets the drop through and fails
        the test on the table being gone instead of hanging it."""
        holder = _get_engine().connect()
        self.addCleanup(holder.invalidate)
        holder.execute("SET idle_in_transaction_session_timeout = '30s'")
        holder.execute("BEGIN")
        schema = Table.get_oedb_schema(is_sandbox=True)
        holder.execute(f'LOCK TABLE "{schema}"."{name}" IN ACCESS SHARE MODE')

    def test_a_blocked_drop_gives_up_with_a_lock_timeout(self):
        table = self.oedb_table()
        self.hold_lock(table.name)
        with self.assertRaises(OperationalError) as raised:
            table.drop_oedb_table(lock_timeout="100ms")
        self.assertEqual(raised.exception.orig.pgcode, LOCK_NOT_AVAILABLE)
        self.assertTrue(self.in_oedb(table.name))

    def test_a_blocked_drop_is_a_lasting_warning_and_the_rows_are_gone(self):
        stuck = self.oedb_table(title="Stuck")
        fine = self.oedb_table(title="Fine")
        self.hold_lock(stuck.name)
        with mock.patch.object(table_actions, "DROP_LOCK_TIMEOUT", "100ms"):
            with self.assertLogs("oeplatform.table_actions", "INFO") as logs:
                response = self.run_action("delete", stuck.name, fine.name, confirm="2")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.exists(stuck.name, fine.name), set())
        self.assertTrue(self.in_oedb(stuck.name))
        self.assertFalse(self.in_oedb(fine.name))
        detail = self.trigger(response, "tables-changed")
        self.assertIs(detail["warning"], True)
        self.assertIn(f"“Stuck” ({stuck.name}) could not be removed", detail["message"])
        self.assertNotIn("Fine", detail["message"])
        by_table = {record.getMessage().split()[1]: record for record in logs.records}
        self.assertTrue(
            by_table[f"table={stuck.name}"].getMessage().endswith("drop=failed")
        )
        self.assertTrue(by_table[f"table={fine.name}"].getMessage().endswith("drop=ok"))

    def test_only_a_request_bounds_the_wait(self):
        """A delete through the dashboard passes ``DROP_LOCK_TIMEOUT``;
        ``Table.delete()``, which ``clear_sandbox`` calls outside any
        request, waits as long as it takes."""
        dashboard, command = self.oedb_table(), self.oedb_table()
        with mock.patch.object(OedbTableProxy, "drop_if_exists") as drop:
            self.assertEqual(self.run_action("delete", dashboard.name).status_code, 204)
            command.delete()
        self.assertEqual(
            [call.kwargs["lock_timeout"] for call in drop.call_args_list],
            [table_actions.DROP_LOCK_TIMEOUT, None],
        )

    def test_the_lock_timeout_is_left_on_no_session(self):
        """``SET LOCAL``: it lasts for the drop's transaction only, so the
        pooled session goes back with the server's default."""
        engine = _get_engine()
        with engine.connect() as probe:
            default = probe.execute("SHOW lock_timeout").scalar()
        table = self.oedb_table()
        table.drop_oedb_table(lock_timeout="123ms")
        self.assertFalse(self.in_oedb(table.name))
        # every session the pool holds, not only the one handed out next
        sessions = [engine.connect() for _ in range(engine.pool.checkedin())]
        try:
            for session in sessions:
                self.assertEqual(session.execute("SHOW lock_timeout").scalar(), default)
        finally:
            for session in sessions:
                session.close()


class DeleteReviewTests(DeleteTestCase):
    """A Table's peer reviews go with it (#2597): ``PeerReview.table`` is a
    name, so they would otherwise pass to the next Table of that name."""

    def reviewed(self, name):
        review = PeerReview.objects.create(
            table=name,
            contributor=self.user,
            reviewer=self.stranger,
            is_finished=True,
            review={"badge": "Gold"},
        )
        PeerReviewManager.objects.create(opr=review)
        ReviewRound.objects.create(
            opr=review, sequence=1, role="reviewer", action="finished"
        )
        return review

    def reviews(self, *names):
        return (
            PeerReview.objects.filter(table__in=names).count(),
            PeerReviewManager.objects.filter(opr__table__in=names).count(),
            ReviewRound.objects.filter(opr__table__in=names).count(),
        )

    def test_deleting_removes_the_reviews_and_a_new_table_has_none(self):
        table = self.oedb_table()
        self.reviewed(table.name)
        self.reviewed(table.name)
        self.draft("t_kept")
        self.reviewed("t_kept")
        response = self.run_action("delete", table.name)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.reviews(table.name), (0, 0, 0))
        self.assertEqual(self.reviews("t_kept"), (1, 1, 1))
        again = self.oedb_table(name=table.name)
        self.assertIsNone(PeerReview.load(again.name))

    def test_a_batch_that_fails_keeps_every_review(self):
        """The reviews go in the delete's transaction: a batch refused
        half-way through leaves both Tables and all their reviews."""
        self.draft("t_rev_a")
        self.draft("t_rev_b")
        self.reviewed("t_rev_a")
        self.reviewed("t_rev_b")
        real = models.Model.delete

        def fail_on_b(instance, *args, **kwargs):
            if isinstance(instance, Table) and instance.name == "t_rev_b":
                raise RuntimeError("the database went away")
            return real(instance, *args, **kwargs)

        with mock.patch.object(models.Model, "delete", fail_on_b):
            with self.assertRaises(RuntimeError):
                self.run_action("delete", "t_rev_a", "t_rev_b", confirm="2")
        self.assertEqual(self.exists("t_rev_a", "t_rev_b"), {"t_rev_a", "t_rev_b"})
        self.assertEqual(self.reviews("t_rev_a", "t_rev_b"), (2, 2, 2))

    def test_table_delete_removes_them_too(self):
        table = self.oedb_table()
        self.reviewed(table.name)
        table.delete()
        self.assertEqual(self.reviews(table.name), (0, 0, 0))
        self.assertFalse(self.in_oedb(table.name))
