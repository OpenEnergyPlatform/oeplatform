"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Many Tables, one Organization, through the REST API (#2595, spec #2551,
WF-08 decision 12): ``api/v0/organizations/<id>/table-permissions/share/``
and ``…/remove/``.

Both call the permission service's bulk writes, which the dashboard's bulk
bar uses too, so the rules are tested in ``login.tests``; what is tested here
is the API's half: each refusal as the status and body this API promises,
all or nothing, ``changed`` and ``unchanged``, an idempotent removal, the
ceiling, and one log line per Table with ``via=api``.

Django rows only: no OEDB table is created.
"""  # noqa: 501

from unittest import mock

from api.services import table_actions
from dataedit.models import Table
from login.models import ADMIN_PERM, DELETE_PERM, WRITE_PERM, UserPermission
from login.table_roles import LAST_ADMIN

from .test_table_permissions import LOGGER, PermissionsAPITestCase


class BulkTestCase(PermissionsAPITestCase):
    """``self.user`` is Admin on ``t_bulk_a`` and ``t_bulk_b`` and a member
    of ``self.lab`` (two members)."""

    def setUp(self):
        super().setUp()
        self.a = Table.objects.create(name="t_bulk_a")
        self.b = Table.objects.create(name="t_bulk_b")
        for table in (self.a, self.b):
            self.grant(self.user, ADMIN_PERM, table)
        self.lab = self.organization("Bulk Lab", self.user, self.other_user)

    def bulk(self, op, data, code=200, organization=None, auth=True):
        organization = organization or self.lab.pk
        return self.api_req(
            "post",
            url=f"/api/v0/organizations/{organization}/table-permissions/{op}/",
            data=data,
            auth=auth,
            exp_code=code,
        )

    def held(self, *tables):
        return {
            table.name: self.lab.table_permissions.filter(table=table)
            .values_list("level", flat=True)
            .first()
            for table in tables
        }


class ShareTests(BulkTestCase):
    def test_it_shares_raise_only_and_names_what_it_left(self):
        self.grant(self.lab, DELETE_PERM, self.b)
        with self.assertLogs(LOGGER, "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                body = self.bulk(
                    "share", {"tables": ["t_bulk_a", "t_bulk_b"], "level": WRITE_PERM}
                )
        self.assertEqual(
            body["organization"], {"id": self.lab.pk, "name": "Bulk Lab", "members": 2}
        )
        self.assertEqual(
            body["changed"],
            [{"table": "t_bulk_a", "before": None, "after": WRITE_PERM}],
        )
        self.assertEqual(body["unchanged"], ["t_bulk_b"])
        self.assertEqual(
            self.held(self.a, self.b), {"t_bulk_a": WRITE_PERM, "t_bulk_b": DELETE_PERM}
        )
        self.assertEqual(len(logs.records), 1)
        self.assertRegex(
            logs.records[0].getMessage(),
            rf"table=t_bulk_a holder=org:{self.lab.pk} action=add before=- "
            rf"after={WRITE_PERM} by={self.user.pk} via=api$",
        )

    def test_a_table_without_table_admin_refuses_the_whole_request(self):
        c = Table.objects.create(name="t_bulk_c")
        self.grant(self.user, DELETE_PERM, c)
        body = self.bulk(
            "share",
            {"tables": ["t_bulk_a", "t_bulk_c"], "level": WRITE_PERM},
            code=403,
        )
        self.assertEqual(body["tables"], ["t_bulk_c"])
        self.assertEqual(self.held(self.a, c), {"t_bulk_a": None, "t_bulk_c": None})

    def test_unusable_requests_are_400_and_write_nothing(self):
        stranger = self.organization("Bulk Stranger", self.other_user)
        for organization, data, field in (
            (None, {"tables": ["t_bulk_a"], "level": ADMIN_PERM}, "level"),
            (None, {"tables": ["t_bulk_a"]}, "level"),
            (None, {"tables": "t_bulk_a", "level": WRITE_PERM}, "tables"),
            (None, {"tables": [], "level": WRITE_PERM}, "tables"),
            (
                stranger.pk,
                {"tables": ["t_bulk_a"], "level": WRITE_PERM},
                "organization",
            ),
        ):
            with self.subTest(data=data, organization=organization):
                body = self.bulk("share", data, code=400, organization=organization)
                self.assertEqual(body["field"], field)
        self.assertEqual(self.held(self.a), {"t_bulk_a": None})

    def test_an_unknown_table_or_organization_is_404(self):
        body = self.bulk(
            "share", {"tables": ["t_bulk_a", "t_nope"], "level": WRITE_PERM}, code=404
        )
        self.assertEqual(body["tables"], ["t_nope"])
        self.bulk(
            "share",
            {"tables": ["t_bulk_a"], "level": WRITE_PERM},
            code=404,
            organization=987654,
        )
        self.assertEqual(self.held(self.a), {"t_bulk_a": None})

    def test_more_tables_than_the_ceiling_is_refused_before_anything_is_read(self):
        with mock.patch.dict(table_actions.CEILINGS, {"organization_share": 1}):
            body = self.bulk(
                "share",
                {"tables": ["t_bulk_a", "t_bulk_b"], "level": WRITE_PERM},
                code=400,
            )
        self.assertEqual(body["field"], "tables")
        self.assertIn("at most 1 tables", body["reason"])

    def test_anonymous_is_401(self):
        self.bulk(
            "share", {"tables": ["t_bulk_a"], "level": WRITE_PERM}, code=401, auth=False
        )


class RemoveTests(BulkTestCase):
    def test_it_removes_and_a_repeat_changes_nothing(self):
        self.grant(self.lab, WRITE_PERM, self.a)
        with self.assertLogs(LOGGER, "INFO") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                body = self.bulk("remove", {"tables": ["t_bulk_a", "t_bulk_b"]})
        self.assertEqual(
            body["changed"],
            [{"table": "t_bulk_a", "before": WRITE_PERM, "after": None}],
        )
        self.assertEqual(body["unchanged"], ["t_bulk_b"])
        self.assertIn("action=remove", logs.records[0].getMessage())
        again = self.bulk("remove", {"tables": ["t_bulk_a", "t_bulk_b"]})
        self.assertEqual(again["changed"], [])
        self.assertEqual(again["unchanged"], ["t_bulk_a", "t_bulk_b"])

    def test_its_only_admin_grant_is_409_last_admin(self):
        only = Table.objects.create(name="t_bulk_only")
        self.grant(self.lab, ADMIN_PERM, only)
        self.grant(self.lab, WRITE_PERM, self.a)
        body = self.bulk(
            "remove", {"tables": ["t_bulk_a", "t_bulk_only"], "confirm": True}, code=409
        )
        self.assertEqual(body["code"], "last_admin")
        self.assertEqual(body["tables"], ["t_bulk_only"])
        self.assertNotEqual(body["reason"], LAST_ADMIN)  # names the Tables
        self.assertEqual(
            self.held(self.a, only), {"t_bulk_a": WRITE_PERM, "t_bulk_only": ADMIN_PERM}
        )

    def test_losing_my_own_access_asks_first(self):
        """The caller is a Table admin on ``t_bulk_mine`` only through the
        Organization's old Admin grant; another user holds direct Admin."""
        mine = Table.objects.create(name="t_bulk_mine")
        self.grant(self.lab, ADMIN_PERM, mine)
        UserPermission.objects.create(
            holder=self.other_user, table=mine, level=ADMIN_PERM
        )
        body = self.bulk("remove", {"tables": ["t_bulk_mine"]}, code=409)
        self.assertEqual(body["code"], "confirmation_needed")
        self.assertEqual(body["tables"], ["t_bulk_mine"])
        self.assertEqual(self.held(mine), {"t_bulk_mine": ADMIN_PERM})
        body = self.bulk("remove", {"tables": ["t_bulk_mine"], "confirm": True})
        self.assertEqual([c["table"] for c in body["changed"]], ["t_bulk_mine"])
        self.assertEqual(self.held(mine), {"t_bulk_mine": None})

    def test_no_membership_is_needed_but_table_admin_is(self):
        outside = self.organization("Bulk Outside", self.other_user)
        self.grant(outside, WRITE_PERM, self.a)
        body = self.bulk("remove", {"tables": ["t_bulk_a"]}, organization=outside.pk)
        self.assertEqual(len(body["changed"]), 1)
        theirs = Table.objects.create(name="t_bulk_theirs")
        self.grant(outside, WRITE_PERM, theirs)
        body = self.bulk(
            "remove", {"tables": ["t_bulk_theirs"]}, code=403, organization=outside.pk
        )
        self.assertEqual(body["tables"], ["t_bulk_theirs"])
