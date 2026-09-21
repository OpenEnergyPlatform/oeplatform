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

from api.actions import _execute
from api.tests import APITestCaseWithTable
from dataedit.models import Table
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
