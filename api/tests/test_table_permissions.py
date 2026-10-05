"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

A Table's Holders through the REST API (#2570, spec #2551, WF-08 decision
12): list, add, change and remove under ``api/v0/tables/<t>/permissions/``.

Every write goes through ``login.table_roles``, the service the access drawer
and the Table's permission page use, so the rules themselves are tested once,
in ``login.tests.test_table_access``. What is tested here is the API's half:
that each rule reaches a client as the status and body this API promises
(``InvalidRequest`` 400, ``NotAllowed`` 403, ``LastAdmin`` and
``ConfirmationNeeded`` 409, told apart by ``code``), that a confirmation is
answered by sending the request again with ``confirm``, what the database
holds afterwards, and the log line with ``via=api``.

The Tables here are Django rows only. No OEDB table is created, so these tests
do not meet the shared sandbox schema other API tests collide in.
"""  # noqa: 501

from dataedit.models import Table
from login.models import (
    ADMIN_PERM,
    DELETE_PERM,
    WRITE_PERM,
    GroupPermission,
    Membership,
    Organization,
    UserPermission,
)
from login.table_roles import LAST_ADMIN
from login.tests.helpers import make_user

from . import APITestCase

LOGGER = "oeplatform.table_permissions"


class PermissionsAPITestCase(APITestCase):
    """``self.user`` (MrTest, token ``self.token``) is Admin on ``t_api``;
    ``self.other_user`` (NotMrTest, ``self.other_token``) holds nothing until
    a test gives it a role."""

    def setUp(self):
        super().setUp()
        self.table = Table.objects.create(name="t_api_permissions")
        self.grant(self.user, ADMIN_PERM)

    def grant(self, holder, level, table=None):
        model = GroupPermission if isinstance(holder, Organization) else UserPermission
        return model.objects.create(
            table=table or self.table, holder=holder, level=level
        )

    def organization(self, name, *members):
        organization = Organization.objects.create(name=name)
        for user in members:
            Membership.objects.create(user=user, group=organization)
        return organization

    def path(self, holder=None, query=""):
        path = f"/api/v0/tables/{self.table.name}/permissions/"
        if holder is not None:
            path += f"{holder}/"
        return path + query

    def call(self, method, holder=None, data=None, auth=True, query="", code=200):
        return self.api_req(
            method,
            url=self.path(holder, query),
            data=data,
            auth=auth,
            exp_code=code,
        )

    def users(self):
        return dict(
            UserPermission.objects.filter(table=self.table).values_list(
                "holder__name", "level"
            )
        )

    def organizations(self):
        return dict(
            GroupPermission.objects.filter(table=self.table).values_list(
                "holder__name", "level"
            )
        )


class ListTests(PermissionsAPITestCase):
    def test_it_lists_users_and_organizations_with_their_roles(self):
        self.grant(self.other_user, WRITE_PERM)
        lab = self.organization("API Lab", self.user, self.other_user)
        self.grant(lab, DELETE_PERM)

        body = self.call("get", auth=True)

        self.assertEqual(body["table"], self.table.name)
        self.assertTrue(body["can_manage"])
        self.assertEqual(
            [(h["holder"], h["name"], h["level"], h["role"]) for h in body["holders"]],
            [
                (f"user:{self.user.pk}", "MrTest", ADMIN_PERM, "Admin"),
                (f"user:{self.other_user.pk}", "NotMrTest", WRITE_PERM, "Data editor"),
                (f"org:{lab.pk}", "API Lab", DELETE_PERM, "Data maintainer"),
            ],
        )
        organization = body["holders"][2]
        self.assertEqual(organization["kind"], "org")
        self.assertEqual(organization["id"], lab.pk)
        self.assertEqual(organization["members"], 2)
        self.assertTrue(organization["you"])

    def test_the_roles_offered_come_from_the_service(self):
        lab = self.organization("API Lab", self.user)
        self.grant(lab, WRITE_PERM)

        body = self.call("get")

        self.assertEqual(
            [(r["level"], r["label"]) for r in body["roles"]],
            [
                (WRITE_PERM, "Data editor"),
                (DELETE_PERM, "Data maintainer"),
                (ADMIN_PERM, "Admin"),
            ],
        )
        user, organization = body["holders"]
        self.assertEqual(user["roles"], [WRITE_PERM, DELETE_PERM, ADMIN_PERM])
        self.assertEqual(organization["roles"], [WRITE_PERM, DELETE_PERM])

    def test_any_authenticated_user_may_read_but_not_manage(self):
        body = self.call("get", auth=self.other_token)

        self.assertFalse(body["can_manage"])
        self.assertEqual([h["name"] for h in body["holders"]], ["MrTest"])
        self.assertFalse(body["holders"][0]["you"])

    def test_reading_needs_a_login(self):
        body = self.call("get", auth=False, code=401)
        self.assertIn("reason", body)

    def test_an_unknown_table_answers_404(self):
        self.api_req(
            "get", url="/api/v0/tables/no_such_table/permissions/", exp_code=404
        )


class AddTests(PermissionsAPITestCase):
    def test_an_admin_adds_a_user_with_a_role(self):
        body = self.call(
            "post", data={"user": "NotMrTest", "level": DELETE_PERM}, code=201
        )

        self.assertEqual(self.users()["NotMrTest"], DELETE_PERM)
        self.assertEqual(body["holder"], f"user:{self.other_user.pk}")
        self.assertEqual(body["role"], "Data maintainer")

    def test_an_admin_shares_with_their_own_organization(self):
        lab = self.organization("API Lab", self.user)

        body = self.call(
            "post", data={"organization": lab.pk, "level": WRITE_PERM}, code=201
        )

        self.assertEqual(self.organizations(), {"API Lab": WRITE_PERM})
        self.assertEqual(body["holder"], f"org:{lab.pk}")
        self.assertEqual(body["members"], 1)

    def test_an_organization_the_admin_is_not_in_is_refused(self):
        lab = self.organization("Someone Else's Lab", self.other_user)

        body = self.call(
            "post", data={"organization": lab.pk, "level": WRITE_PERM}, code=400
        )

        self.assertEqual(body["field"], "organization")
        self.assertEqual(self.organizations(), {})

    def test_an_organization_is_never_given_admin(self):
        lab = self.organization("API Lab", self.user)

        body = self.call(
            "post", data={"organization": lab.pk, "level": ADMIN_PERM}, code=400
        )

        self.assertEqual(body["field"], "level")
        self.assertEqual(self.organizations(), {})

    def test_a_role_outside_the_list_is_refused(self):
        for level in (0, 5, "admin", None):
            with self.subTest(level=level):
                body = self.call(
                    "post", data={"user": "NotMrTest", "level": level}, code=400
                )
                self.assertEqual(body["field"], "level")
        self.assertNotIn("NotMrTest", self.users())

    def test_an_unknown_user_is_refused(self):
        body = self.call("post", data={"user": "Nobody", "level": WRITE_PERM}, code=400)
        self.assertEqual(body["field"], "name")

    def test_a_holder_is_not_added_twice(self):
        self.grant(self.other_user, WRITE_PERM)

        self.call("post", data={"user": "NotMrTest", "level": ADMIN_PERM}, code=400)

        self.assertEqual(self.users()["NotMrTest"], WRITE_PERM)

    def test_naming_both_a_user_and_an_organization_is_refused(self):
        lab = self.organization("API Lab", self.user)

        body = self.call(
            "post",
            data={"user": "NotMrTest", "organization": lab.pk, "level": WRITE_PERM},
            code=400,
        )

        self.assertEqual(body["field"], "kind")
        self.assertEqual((self.users(), self.organizations()), ({"MrTest": 12}, {}))

    def test_a_body_that_is_not_an_object_is_refused(self):
        response = self.client.post(
            self.path(),
            "[1, 2]",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_naming_neither_is_refused(self):
        body = self.call("post", data={"level": WRITE_PERM}, code=400)
        self.assertEqual(body["field"], "kind")

    def test_below_admin_nothing_can_be_added(self):
        self.grant(self.other_user, DELETE_PERM)
        make_user("ApiCarol")

        body = self.call(
            "post",
            data={"user": "ApiCarol", "level": WRITE_PERM},
            auth=self.other_token,
            code=403,
        )

        self.assertIn("reason", body)
        self.assertNotIn("ApiCarol", self.users())

    def test_writing_needs_a_login(self):
        self.call("post", data={"user": "NotMrTest", "level": 4}, auth=False, code=401)
        self.assertNotIn("NotMrTest", self.users())

    def test_a_platform_admin_manages_without_a_grant(self):
        """The service's rule for who is a Table admin, not the API's."""
        admin = make_user("ApiPlatformAdmin", is_admin=True)
        token = admin.auth_token.key

        self.call(
            "post",
            data={"user": "NotMrTest", "level": WRITE_PERM},
            auth=token,
            code=201,
        )

        self.assertEqual(self.users()["NotMrTest"], WRITE_PERM)


class ChangeTests(PermissionsAPITestCase):
    def test_an_admin_changes_a_users_role(self):
        self.grant(self.other_user, WRITE_PERM)

        body = self.call(
            "patch", f"user:{self.other_user.pk}", data={"level": ADMIN_PERM}
        )

        self.assertEqual(self.users()["NotMrTest"], ADMIN_PERM)
        self.assertEqual(body["role"], "Admin")

    def test_the_same_role_again_changes_nothing(self):
        self.grant(self.other_user, WRITE_PERM)

        with self.assertNoLogs(LOGGER), self.captureOnCommitCallbacks(execute=True):
            body = self.call(
                "patch", f"user:{self.other_user.pk}", data={"level": WRITE_PERM}
            )

        self.assertEqual(body["level"], WRITE_PERM)

    def test_an_organization_cannot_be_raised_to_admin(self):
        lab = self.organization("API Lab", self.user)
        self.grant(lab, WRITE_PERM)

        body = self.call("patch", f"org:{lab.pk}", data={"level": ADMIN_PERM}, code=400)

        self.assertEqual(body["field"], "level")
        self.assertEqual(self.organizations(), {"API Lab": WRITE_PERM})

    def test_below_admin_nothing_can_be_changed(self):
        self.grant(self.other_user, DELETE_PERM)

        self.call(
            "patch",
            f"user:{self.user.pk}",
            data={"level": WRITE_PERM},
            auth=self.other_token,
            code=403,
        )

        self.assertEqual(self.users()["MrTest"], ADMIN_PERM)


class RemoveTests(PermissionsAPITestCase):
    def test_an_admin_removes_a_holder(self):
        self.grant(self.other_user, DELETE_PERM)

        self.call("delete", f"user:{self.other_user.pk}", code=204)

        self.assertEqual(self.users(), {"MrTest": ADMIN_PERM})

    def test_an_admin_removes_an_organization(self):
        lab = self.organization("API Lab")
        self.grant(lab, DELETE_PERM)

        self.call("delete", f"org:{lab.pk}", code=204)

        self.assertEqual(self.organizations(), {})

    def test_a_holder_the_table_does_not_have_answers_404(self):
        """The URL names something that is not there, which a repeated
        delete meets too."""
        for key in (f"user:{self.other_user.pk}", "org:999999", "nobody", "user:x"):
            with self.subTest(key=key):
                body = self.call("delete", key, code=404)
                self.assertIn("reason", body)

    def test_below_admin_nothing_can_be_removed(self):
        self.grant(self.other_user, DELETE_PERM)

        self.call("delete", f"user:{self.user.pk}", auth=self.other_token, code=403)

        self.assertEqual(self.users()["MrTest"], ADMIN_PERM)


class LastAdminTests(PermissionsAPITestCase):
    """The last user holding direct Admin cannot lose it, confirmed or not,
    and the guard answers before any confirmation is asked for."""

    def test_the_last_admin_cannot_lower_their_own_admin(self):
        for confirm in (False, True):
            with self.subTest(confirm=confirm):
                body = self.call(
                    "patch",
                    f"user:{self.user.pk}",
                    data={"level": WRITE_PERM, "confirm": confirm},
                    code=409,
                )
                self.assertEqual(body["code"], "last_admin")
                self.assertEqual(body["reason"], LAST_ADMIN)
        self.assertEqual(self.users()["MrTest"], ADMIN_PERM)

    def test_the_last_admin_cannot_be_removed(self):
        body = self.call(
            "delete", f"user:{self.user.pk}", query="?confirm=true", code=409
        )

        self.assertEqual(body["code"], "last_admin")
        self.assertEqual(self.users()["MrTest"], ADMIN_PERM)


class ConfirmationTests(PermissionsAPITestCase):
    """No dialog in an API: the 409 says what would happen, and the client
    sends the same request again with ``confirm``.

    Documents: docs/oeplatform-code/web-api/oedb-rest-api/index.md
    """

    def setUp(self):
        super().setUp()
        self.grant(self.other_user, ADMIN_PERM)

    def test_losing_your_own_admin_is_answered_409_and_writes_nothing(self):
        body = self.call(
            "patch", f"user:{self.user.pk}", data={"level": WRITE_PERM}, code=409
        )

        self.assertEqual(body["code"], "confirmation_needed")
        self.assertIn("manage this table's access", body["reason"])
        self.assertEqual(self.users()["MrTest"], ADMIN_PERM)

    def test_sent_again_with_confirm_it_is_made(self):
        self.call(
            "patch",
            f"user:{self.user.pk}",
            data={"level": WRITE_PERM, "confirm": True},
        )

        self.assertEqual(self.users()["MrTest"], WRITE_PERM)

    def test_removing_yourself_is_confirmed_through_the_query(self):
        """A DELETE carries no body a client can rely on, so its confirmation
        is a query parameter."""
        body = self.call("delete", f"user:{self.user.pk}", code=409)
        self.assertEqual(body["code"], "confirmation_needed")
        self.assertIn("MrTest", self.users())

        self.call("delete", f"user:{self.user.pk}", query="?confirm=true", code=204)

        self.assertNotIn("MrTest", self.users())

    def test_only_true_confirms(self):
        for confirm in (False, "no", 0, None):
            with self.subTest(confirm=confirm):
                self.call(
                    "patch",
                    f"user:{self.user.pk}",
                    data={"level": WRITE_PERM, "confirm": confirm},
                    code=409,
                )
        self.assertEqual(self.users()["MrTest"], ADMIN_PERM)


class LoggingTests(PermissionsAPITestCase):
    def test_every_write_logs_one_line_with_via_api(self):
        lab = self.organization("API Lab", self.user)
        other = self.other_user.pk

        with self.assertLogs(LOGGER) as logs:
            with self.captureOnCommitCallbacks(execute=True):
                self.call(
                    "post", data={"user": "NotMrTest", "level": WRITE_PERM}, code=201
                )
                self.call("patch", f"user:{other}", data={"level": DELETE_PERM})
                self.call("delete", f"user:{other}", code=204)
                self.call(
                    "post", data={"organization": lab.pk, "level": WRITE_PERM}, code=201
                )

        name = self.table.name
        self.assertEqual(
            [record.getMessage() for record in logs.records],
            [
                f"table_permission_write table={name} holder=user:{other} "
                f"action=add before=- after=4 by={self.user.pk} via=api",
                f"table_permission_write table={name} holder=user:{other} "
                f"action=change before=4 after=8 by={self.user.pk} via=api",
                f"table_permission_write table={name} holder=user:{other} "
                f"action=remove before=8 after=- by={self.user.pk} via=api",
                f"table_permission_write table={name} holder=org:{lab.pk} "
                f"action=add before=- after=4 by={self.user.pk} via=api",
            ],
        )

    def test_a_refused_write_logs_nothing(self):
        with self.assertNoLogs(LOGGER):
            with self.captureOnCommitCallbacks(execute=True):
                self.call("patch", f"user:{self.user.pk}", data={"level": 4}, code=409)
                self.call("post", data={"user": "Nobody", "level": 4}, code=400)


class OrganizationOnlyAdminTests(PermissionsAPITestCase):
    def test_an_organizations_only_admin_grant_cannot_be_removed(self):
        """#2595: on a Table no user holds Admin on, the last Admin grant of
        any kind stays."""
        self.table = Table.objects.create(name="t_api_only_org")
        lab = self.organization("API Only Lab", self.user)
        self.grant(lab, ADMIN_PERM)
        body = self.call("delete", f"org:{lab.pk}", query="?confirm=true", code=409)
        self.assertEqual(body["code"], "last_admin")
        body = self.call(
            "patch", f"org:{lab.pk}", data={"level": DELETE_PERM}, code=409
        )
        self.assertEqual(body["code"], "last_admin")
        self.assertEqual(self.organizations(), {"API Only Lab": ADMIN_PERM})
