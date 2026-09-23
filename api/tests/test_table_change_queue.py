"""Who may queue a structural change to a table, and what a value may contain.

`POST /api/v0/tables/<name>/` queues a column or constraint change into the
review queue. It had **no permission check at all**: an anonymous request
reached it and answered `200`. That is what these tests exist for, and the
first of them is the one that would have caught it.

The second half is the sharper one. Both queue writers built their `INSERT` by
interpolating the payload's values into the statement text, and nothing between
the request and the database validated them -- `get_or_403` fetches a key and
checks nothing. So a value carrying a quote did not fail, it *changed the
statement*. The values are bound now, and
`test_a_quote_in_a_value_is_stored_rather_than_executed` is what says so.

**These read the queue with their own `SELECT`, for two reasons**, both found
by writing them:

- **`get_column_changes` raises on any row it finds.** It selects `*` and then
  reads `column.exception`, a column `public.api_columns` does not have. It is
  only ever seen returning `[]` because of the next point.
- **The OEDB is not reset between test runs.** These tables live in the OEDB,
  which Django's test runner does not create or drop, so rows from previous
  runs are still there. Each test therefore marks its own row with a fresh
  identifier and looks for exactly that, never for a count.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

from uuid import uuid4

from django.urls import reverse

from api.actions import _execute
from api.tests import APITestCaseWithTable
from dataedit.models import Table
from login.models import myuser
from oedb.connection import _create_oedb_session

COLUMN_CHANGE = {
    "type": "column",
    "name": "name",
    "data_type": "character varying",
    "character_maximum_length": 60,
}

CONSTRAINT_CHANGE = {
    "type": "constraint",
    "action": "ADD",
    "constraint_type": "UNIQUE",
    "constraint_parameter": "name",
    "reference_table": None,
    "reference_column": None,
}


class ChangeQueueTestCase(APITestCaseWithTable):
    """A marked change, and a way to ask whether it landed."""

    def setUp(self):
        super().setUp()
        self.marker = f"probe-{uuid4().hex[:12]}"

    def column_change(self, **overrides):
        return {**COLUMN_CHANGE, "new_name": self.marker, **overrides}

    def constraint_change(self, **overrides):
        return {**CONSTRAINT_CHANGE, "constraint_name": self.marker, **overrides}

    def queued_columns(self):
        return self.rows(
            "SELECT new_name, not_null, reviewed FROM public.api_columns "
            "WHERE c_table = :table AND new_name = :marker"
        )

    def queued_constraints(self):
        return self.rows(
            "SELECT constraint_name, reference_table FROM public.api_constraints "
            "WHERE c_table = :table AND constraint_name = :marker"
        )

    def rows(self, sql):
        session = _create_oedb_session()
        try:
            return [
                dict(row)
                for row in _execute(
                    session,
                    sql,
                    {"table": self.test_table, "marker": self.marker},
                )
            ]
        finally:
            session.close()

    def table_obj(self):
        return Table.objects.get(name=self.test_table)


class QueueChangePermissionTest(ChangeQueueTestCase):
    """Only somebody who may write to the table may queue a change to it."""

    def test_an_anonymous_request_cannot_queue_a_column_change(self):
        # The regression this module was written for. It answered 200.
        self.api_req("post", data=self.column_change(), auth=False, exp_code=(401, 403))

        self.assertEqual([], self.queued_columns())

    def test_an_anonymous_request_cannot_queue_a_constraint_change(self):
        self.api_req(
            "post", data=self.constraint_change(), auth=False, exp_code=(401, 403)
        )

        self.assertEqual([], self.queued_constraints())

    def test_another_account_cannot_queue_a_change_to_someone_elses_table(self):
        # Authenticated is not enough: the queue is the table owner's to
        # review, so filing into it is a write to their table.
        self.api_req(
            "post", data=self.column_change(), auth=self.other_token, exp_code=403
        )

        self.assertEqual([], self.queued_columns())

    def test_the_owner_can_queue_a_column_change(self):
        self.api_req("post", data=self.column_change(), exp_code=200)

        self.assertEqual(1, len(self.queued_columns()))

    def test_the_owner_can_queue_a_constraint_change(self):
        self.api_req("post", data=self.constraint_change(), exp_code=200)

        self.assertEqual(1, len(self.queued_constraints()))


class QueuedValueTest(ChangeQueueTestCase):
    """A payload value is data. It was statement text."""

    def test_a_quote_in_a_value_is_stored_rather_than_executed(self):
        # The shape an injection takes: close the quote, end the statement,
        # start another. Interpolated, this ran. Bound, it is a name. Kept
        # unique like every other marker here -- the OEDB carries yesterday's
        # rows -- and inside the column's 50 characters.
        self.marker = f"{uuid4().hex[:8]}'); DROP TABLE public.api_columns; --"

        self.api_req("post", data=self.column_change(), exp_code=200)

        queued = self.queued_columns()
        self.assertEqual(1, len(queued))
        # Stored whole -- and the table an injection would have dropped is
        # still there to be read, which the query above just proved.
        self.assertEqual(self.marker, queued[0]["new_name"])

    def test_a_missing_optional_value_is_still_null(self):
        # The old statement wrote the string "NULL" and then rewrote `'NULL'`
        # into a bare NULL with a text replacement on the finished SQL.
        # Binding None does it directly; this says the outcome did not change.
        self.api_req(
            "post", data=self.constraint_change(reference_table=None), exp_code=200
        )

        self.assertIsNone(self.queued_constraints()[0]["reference_table"])

    def test_a_boolean_is_still_stored_as_one(self):
        # `not_null` is a Boolean column that used to be written as the quoted
        # string 'False' and coerced by Postgres. Bound, it arrives as a bool.
        self.api_req("post", data=self.column_change(is_nullable=False), exp_code=200)

        self.assertIs(False, self.queued_columns()[0]["not_null"])

    def test_a_queued_change_is_never_marked_reviewed(self):
        """Characterisation, and it is what bounds the reach of the old hole.

        `reviewed` comes out NULL: the column's `default=False` is
        SQLAlchemy's, applied when the ORM builds a row, and these writers use
        a raw `INSERT`. The review page asks for `reviewed = false`, which does
        not match NULL, so a change queued through this endpoint never reaches
        the page meant to show it and the rows accumulate where nothing reads
        them.

        That does not make the missing permission check harmless -- the rows
        were written by anyone, and the statement they were written with was
        theirs to shape -- but a queued change was never one click from being
        applied. Pinned rather than fixed: it is a separate defect and this
        branch is the security patch.
        """
        self.api_req("post", data=self.column_change(), exp_code=200)

        self.assertIsNone(self.queued_columns()[0]["reviewed"])


class ReviewQueueAccessTest(ChangeQueueTestCase):
    """Applying or denying a queued change is an admin's, and the id is data.

    `admin_column_view` and `admin_constraints_view` carried `@require_POST`
    and nothing else, and handed the posted `id` to statements that
    interpolated it (#2490). CSRF does not help: an anonymous visitor gets a
    token from any page. Admin-only is the interim rule while the issue
    decides whether the queue is deleted or repaired; the table owner is
    refused too, on purpose, until that decision says otherwise.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user, _ = myuser.objects.get_or_create(
            name="MrAdminTest", email="mradmintest@test.com", did_agree=True
        )
        cls.admin_user.is_admin = True
        cls.admin_user.save()

    def queued_column_id(self):
        self.api_req("post", data=self.column_change(), exp_code=200)
        [row] = self.rows(
            "SELECT id FROM public.api_columns "
            "WHERE c_table = :table AND new_name = :marker"
        )
        return row["id"]

    def reviewed(self):
        [row] = self.queued_columns()
        return row["reviewed"]

    def deny(self, change_id, url="dataedit:admin-columns"):
        return self.client.post(
            reverse(url),
            {"action": "deny", "id": change_id, "table": self.test_table},
        )

    def tearDown(self):
        self.client.logout()
        super().tearDown()

    def test_an_anonymous_request_cannot_deny_a_change(self):
        change_id = self.queued_column_id()

        response = self.deny(change_id)

        self.assertIn(response.status_code, (302, 403))
        self.assertIsNone(self.reviewed())

    def test_an_anonymous_request_cannot_touch_the_constraint_queue(self):
        response = self.deny(1, url="dataedit:admin-contraints")

        self.assertIn(response.status_code, (302, 403))

    def test_a_logged_in_account_that_is_not_an_admin_is_refused(self):
        change_id = self.queued_column_id()
        self.client.force_login(self.other_user)

        self.assertEqual(403, self.deny(change_id).status_code)
        self.assertIsNone(self.reviewed())

    def test_the_table_owner_is_refused_too_for_now(self):
        change_id = self.queued_column_id()
        self.client.force_login(self.user)

        self.assertEqual(403, self.deny(change_id).status_code)
        self.assertIsNone(self.reviewed())

    def test_an_admin_can_deny_a_change(self):
        change_id = self.queued_column_id()
        self.client.force_login(self.admin_user)

        self.assertEqual(302, self.deny(change_id).status_code)
        self.assertIs(True, self.reviewed())

    def test_an_id_that_is_not_a_number_is_refused_before_any_statement(self):
        # The shape the injection took: the id closed the quote and went on.
        # It is refused as a bad request, and the row it aimed at is untouched.
        change_id = self.queued_column_id()
        self.client.force_login(self.admin_user)

        response = self.deny(f"{change_id}' OR '1'='1")

        self.assertEqual(400, response.status_code)
        self.assertIsNone(self.reviewed())

    def test_an_unknown_action_is_a_bad_request_not_a_server_error(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("dataedit:admin-columns"),
            {"action": "drop", "id": 1, "table": self.test_table},
        )

        self.assertEqual(400, response.status_code)
