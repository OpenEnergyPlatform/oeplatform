"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from base.tests import TestViewsTestCase
from login.models import myuser as User
from modelview.helper import getClasses
from modelview.models import DELETE_GRACE_PERIOD, BasicFactsheet
from modelview.tests.corpus import seed_corpus

SHEETTYPES = ("model", "framework")


class FactsheetAuthorisationTestCase(TestViewsTestCase):
    """One corpus of each sheet type, plus an admin beside the inherited user.

    `TestViewsTestCase` provides `self.user`, a plain account -- which is the
    interesting one here, because the hole this closes is not a crafted
    request, it is a rendered button that every registered account could
    click.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_user(  # type: ignore
            name="admin", email="admin@test.test", affiliation="test"
        )
        cls.admin.is_admin = True
        cls.admin.save()

    @classmethod
    def tearDownClass(cls):
        cls.admin.delete()
        super().tearDownClass()

    def setUp(self):
        self.corpus = {
            t: seed_corpus(sheettype=t, factsheets=2, corrupted=0) for t in SHEETTYPES
        }

    def sheet(self, sheettype):
        return self.corpus[sheettype].factsheets[0]

    def age(self, sheet, days=30):
        """Push a factsheet's creation date out of the grace period.

        `.update()` rather than `.save()`: `created` is `auto_now_add`, so a
        save would leave it exactly where it is and the test would pass for
        the wrong reason.
        """
        BasicFactsheet.objects.filter(pk=sheet.pk).update(
            created=timezone.now() - timedelta(days=days)
        )
        sheet.refresh_from_db()
        return sheet

    def strip_created(self, sheet):
        """The state of the 339 factsheets that predate the column."""
        BasicFactsheet.objects.filter(pk=sheet.pk).update(created=None)
        sheet.refresh_from_db()
        return sheet

    def delete_as(self, user, sheettype, pk, expect_status=None):
        if user is None:
            self.client.logout()
        else:
            self.client.force_login(user)
        url = reverse(
            "modelview:delete-factsheet", kwargs={"sheettype": sheettype, "pk": pk}
        )
        resp = self.client.delete(url)
        if expect_status is not None:
            self.assertEqual(
                resp.status_code, expect_status, msg=f"{sheettype}: {resp}"
            )
        return resp

    def detail_html(self, user, sheettype, pk):
        if user is None:
            self.client.logout()
        else:
            self.client.force_login(user)
        url = reverse(
            "modelview:show-factsheet", kwargs={"sheettype": sheettype, "pk": pk}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200, msg=f"{sheettype}: {resp}")
        return resp


class TestDeleteOutsideTheGracePeriod(FactsheetAuthorisationTestCase):
    """Once a factsheet is older than the window, admins only.

    The view must refuse, not merely the template hide. `fs_delete_view`
    accepts only DELETE, so a browser cannot reach it by navigation -- but
    `hx-delete` issues a real DELETE, and so does `curl`. Hiding the button
    protects nothing on its own.

    (The anonymous case is asserted in `test_read_path.py`, where it also
    exercises the shared `delete()` seam.)
    """

    def test_a_logged_in_non_admin_is_refused(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                cls, _ = getClasses(sheettype)
                pk = self.age(self.sheet(sheettype)).pk

                self.delete_as(self.user, sheettype, pk, expect_status=403)

                self.assertTrue(cls.objects.filter(pk=pk).exists())

    def test_a_factsheet_predating_the_column_is_refused(self):
        """`created IS NULL` -- the 339 that existed before this shipped.

        They were deliberately not backfilled: a default of "now" would have
        opened every one of them to any account for a week after the deploy.
        """
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                cls, _ = getClasses(sheettype)
                pk = self.strip_created(self.sheet(sheettype)).pk

                self.delete_as(self.user, sheettype, pk, expect_status=403)

                self.assertTrue(cls.objects.filter(pk=pk).exists())

    def test_an_admin_can_delete(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                cls, _ = getClasses(sheettype)
                pk = self.age(self.sheet(sheettype)).pk

                self.delete_as(self.admin, sheettype, pk, expect_status=200)

                self.assertFalse(cls.objects.filter(pk=pk).exists())

    def test_a_successful_delete_is_logged(self):
        """The only record the operation will ever have: there is no audit model.

        That absence is exactly what made the tag corruption unrepairable, so
        the one line has to carry enough to reconstruct what happened --
        including how many tags went with it.
        """
        sheet = self.age(self.sheet("model"))

        with self.assertLogs("oeplatform", level="INFO") as captured:
            self.delete_as(self.admin, "model", sheet.pk, expect_status=200)

        lines = [m for m in captured.output if "factsheet_write" in m]
        self.assertEqual(len(lines), 1, msg=captured.output)
        line = lines[0]
        self.assertIn("sheettype=model", line)
        self.assertIn(f"pk={sheet.pk}", line)
        self.assertIn("action=delete", line)
        self.assertIn(f"user={self.admin.name}", line)
        self.assertIn("ok=1", line)

    def test_a_refused_delete_is_not_logged_as_a_write(self):
        """A refusal is not a write, so it must not leave a write line.

        `assertNoLogs` rather than `assertLogs`: the latter requires at least
        one record and so fails on silence, which is the thing being asserted.
        """
        sheet = self.age(self.sheet("model"))

        with self.assertNoLogs("oeplatform", level="INFO"):
            self.delete_as(self.user, "model", sheet.pk, expect_status=403)


class TestTheGracePeriod(FactsheetAuthorisationTestCase):
    """For a week after creation, any logged-in account may delete.

    A maintainer's decision (2026-09-08), taken with the objection recorded on
    `DELETE_GRACE_PERIOD`: the window is keyed to the factsheet's AGE and not
    to who is asking, so it does let one account delete another's new
    factsheet. What it buys is the practical case -- somebody who has just
    created a duplicate or a test entry removes it without finding an admin.

    These tests pin both halves of that trade, so neither can be lost by
    accident: the window opens, and it closes.
    """

    def test_a_logged_in_non_admin_can_delete_a_new_factsheet(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                cls, _ = getClasses(sheettype)
                pk = self.sheet(sheettype).pk

                self.delete_as(self.user, sheettype, pk, expect_status=200)

                self.assertFalse(cls.objects.filter(pk=pk).exists())

    def test_the_window_is_open_right_up_to_its_edge(self):
        sheet = self.age(self.sheet("model"), days=0)
        BasicFactsheet.objects.filter(pk=sheet.pk).update(
            created=timezone.now() - DELETE_GRACE_PERIOD + timedelta(minutes=1)
        )

        self.delete_as(self.user, "model", sheet.pk, expect_status=200)

    def test_the_window_is_shut_just_past_it(self):
        sheet = self.sheet("model")
        BasicFactsheet.objects.filter(pk=sheet.pk).update(
            created=timezone.now() - DELETE_GRACE_PERIOD - timedelta(minutes=1)
        )

        self.delete_as(self.user, "model", sheet.pk, expect_status=403)

    def test_an_anonymous_caller_is_refused_inside_the_window_too(self):
        """The window widens *who among the logged in*, and nothing further.

        `@login_required` answers first, so this is a redirect rather than a
        403 -- what matters is that the factsheet is still there.
        """
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                cls, _ = getClasses(sheettype)
                pk = self.sheet(sheettype).pk

                self.delete_as(None, sheettype, pk, expect_status=302)

                self.assertTrue(cls.objects.filter(pk=pk).exists())

    def test_a_delete_inside_the_window_is_logged_like_any_other(self):
        """The log line is the only trace either way, so the cheap path must
        not be the quiet one."""
        sheet = self.sheet("model")

        with self.assertLogs("oeplatform", level="INFO") as captured:
            self.delete_as(self.user, "model", sheet.pk, expect_status=200)

        lines = [m for m in captured.output if "factsheet_write" in m]
        self.assertEqual(len(lines), 1, msg=captured.output)
        self.assertIn("action=delete", lines[0])
        self.assertIn(f"user={self.user.name}", lines[0])

    def test_a_new_factsheet_offers_a_non_admin_the_button(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                pk = self.sheet(sheettype).pk
                resp = self.detail_html(self.user, sheettype, pk)

                self.assertContains(
                    resp,
                    reverse(
                        "modelview:delete-factsheet",
                        kwargs={"sheettype": sheettype, "pk": pk},
                    ),
                )


class TestDetailPageActions(FactsheetAuthorisationTestCase):
    """What the detail page offers, to whom.

    Verified on production before this change: the Delete button and the Edit
    link were in the HTML of every factsheet page, fetched anonymously, in no
    `{% if %}` at all -- so all 339 factsheets were one click away for any
    registered account.
    """

    def delete_url(self, sheettype, pk):
        return reverse(
            "modelview:delete-factsheet", kwargs={"sheettype": sheettype, "pk": pk}
        )

    def edit_url(self, sheettype, pk):
        return reverse("modelview:edit", kwargs={"sheettype": sheettype, "pk": pk})

    def test_an_admin_is_offered_delete(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                pk = self.age(self.sheet(sheettype)).pk
                resp = self.detail_html(self.admin, sheettype, pk)

                self.assertContains(resp, self.delete_url(sheettype, pk))

    def test_a_non_admin_is_not_offered_delete_once_it_is_old(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                pk = self.age(self.sheet(sheettype)).pk
                resp = self.detail_html(self.user, sheettype, pk)

                self.assertNotContains(resp, self.delete_url(sheettype, pk))

    def test_a_non_admin_is_still_offered_edit(self):
        """Editing stays open to any account. That is stated policy, not an
        oversight -- community contribution is the intent."""
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                pk = self.sheet(sheettype).pk
                resp = self.detail_html(self.user, sheettype, pk)

                self.assertContains(resp, self.edit_url(sheettype, pk))

    def test_an_anonymous_visitor_is_offered_neither(self):
        """Both are affordances that cannot work for a visitor who is not
        logged in: Delete is refused and Edit only leads to a login form.

        Asserted on a BRAND NEW factsheet on purpose -- inside the grace
        period, which is the one state where the window could leak the button
        to someone who is not logged in at all.
        """
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                pk = self.sheet(sheettype).pk
                resp = self.detail_html(None, sheettype, pk)

                self.assertNotContains(resp, self.delete_url(sheettype, pk))
                self.assertNotContains(resp, self.edit_url(sheettype, pk))


class TestEditingStaysOpen(FactsheetAuthorisationTestCase):
    """Guard against over-tightening: only delete was meant to close."""

    def test_a_non_admin_can_open_the_edit_form(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.get(
                    "modelview:edit",
                    kwargs={"sheettype": sheettype, "pk": self.sheet(sheettype).pk},
                    logged_in=True,
                )

    def test_a_non_admin_can_open_the_add_form(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                self.get(
                    "modelview:modeladd",
                    kwargs={"sheettype": sheettype},
                    logged_in=True,
                )
