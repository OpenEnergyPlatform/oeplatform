"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The access drawer of the tables tab and the permission service behind it
(#2566, spec #2551, WF-08), as seen through HTTP: who holds which role, who
may change it, the rules every change goes through (roles from one list,
Admin to users only, Organizations capped and shared only by their members,
the last-admin guard ordered before the self-demotion confirmation), what
the list does afterwards, and the log line each change leaves.

Assertions are on what the user is offered and told, what the database
holds afterwards, which response headers came back and which log lines were
written; never on markup details or seconds.
"""  # noqa: 501

import json

from django.contrib.auth.models import Group
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from dataedit.models import Table
from login.models import (
    ADMIN_PERM,
    DELETE_PERM,
    NO_PERM,
    WRITE_PERM,
    GroupPermission,
    Membership,
    Organization,
    UserPermission,
)
from login.table_roles import LAST_ADMIN
from login.tests.helpers import HTMX, make_user
from login.tests.test_tables_tab import TablesTabTestCase
from modelview.tests.html import element_with_id

DRAWER = "login/partials/table_access_drawer.html"
LOGGER = "oeplatform.table_permissions"


class AccessTestCase(TablesTabTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.alice = make_user("AccessAlice")
        cls.bob = make_user("AccessBob")

    def access_path(self, name):
        return reverse(
            "login:table-access",
            kwargs={"user_id": self.user.pk, "table_name": name},
        )

    def drawer(self, name, status=200):
        response = self.client.get(self.access_path(name), **HTMX)
        self.assertEqual(response.status_code, status)
        return response

    def access(self, name):
        response = self.drawer(name)
        self.assertTemplateUsed(response, DRAWER)
        return response.context["access"]

    def send(self, table_name, /, current=None, **data):
        headers = dict(HTMX)
        if current is not None:
            headers["HTTP_HX_CURRENT_URL"] = f"http://testserver{self.path}{current}"
        return self.client.post(self.access_path(table_name), data, **headers)

    def grant(self, table, holder, level):
        if isinstance(holder, Group):
            return GroupPermission.objects.create(
                table=table, holder=holder, level=level
            )
        return UserPermission.objects.create(table=table, holder=holder, level=level)

    def member(self, organization, *users):
        for user in users:
            Membership.objects.create(user=user, group=organization)

    def users_of(self, table):
        return dict(
            UserPermission.objects.filter(table=table).values_list(
                "holder__name", "level"
            )
        )

    def organizations_of(self, table):
        return dict(
            GroupPermission.objects.filter(table=table).values_list(
                "holder__name", "level"
            )
        )

    def changed(self, response):
        """The ``tables-changed`` detail a done change sends."""
        self.assertEqual(response.status_code, 200, response.content)
        return json.loads(response["HX-Trigger"])["tables-changed"]

    def assertNothingSent(self, response):
        self.assertNotIn("HX-Trigger", response)


class DrawerTests(AccessTestCase):
    def test_it_lists_users_and_organizations_with_their_roles(self):
        table = self.table("t_holders")
        self.grant(table, self.alice, WRITE_PERM)
        organization = self.organization("Access Lab")
        self.member(organization, self.alice, self.bob)
        self.grant(table, organization, DELETE_PERM)

        access = self.access("t_holders")
        self.assertEqual(
            [(h.name, h.role) for h in access.users],
            [("TablesTabOwner", "Admin"), ("AccessAlice", "Data editor")],
        )
        self.assertEqual(
            [(h.name, h.role, h.members) for h in access.organizations],
            [("Access Lab", "Data maintainer", 3)],
        )

    def test_the_users_own_entries_are_marked(self):
        table = self.table("t_mine_marked")
        self.grant(table, self.alice, ADMIN_PERM)
        mine = self.organization("Access Mine")
        theirs = Organization.objects.create(name="Access Theirs")
        self.grant(table, mine, WRITE_PERM)
        self.grant(table, theirs, WRITE_PERM)

        access = self.access("t_mine_marked")
        self.assertEqual(
            {h.name for h in access.holders if h.you},
            {
                "TablesTabOwner",
                "Access Mine",
            },
        )

    def test_the_roles_come_from_the_model_minus_none(self):
        self.table("t_roles")
        response = self.drawer("t_roles")
        roles = response.context["roles"]
        self.assertEqual([role.level for role in roles], [4, 8, 12])
        self.assertEqual(
            [role.label for role in roles], ["Data editor", "Data maintainer", "Admin"]
        )
        for role in roles:
            self.assertTrue(role.description)
            self.assertContains(response, role.description)

    def test_it_links_to_the_tables_permission_page(self):
        self.table("t_link")
        self.assertContains(
            self.drawer("t_link"),
            reverse("dataedit:table-permission", kwargs={"table": "t_link"}),
        )

    def test_an_admin_is_offered_the_controls(self):
        table = self.table("t_admin_view")
        self.grant(table, self.alice, WRITE_PERM)
        html = self.drawer("t_admin_view").content.decode()
        self.assertNotEqual(element_with_id(html, "table-access-add-user"), "")
        self.assertNotEqual(
            element_with_id(html, f"access-role-user-{self.alice.pk}"), ""
        )
        self.assertNotEqual(
            element_with_id(html, f"access-remove-user-{self.alice.pk}"), ""
        )
        self.assertNotIn("Only Admins can change access", html)

    def test_below_admin_the_list_is_read_only_with_the_admins_as_avatars(self):
        for level in (WRITE_PERM, DELETE_PERM):
            Table.objects.all().delete()
            table = self.table(f"t_read_{level}", level=level)
            self.grant(table, self.alice, ADMIN_PERM)
            with self.subTest(level=level):
                response = self.drawer(table.name)
                html = response.content.decode()
                self.assertFalse(response.context["access"].can_manage)
                self.assertContains(response, "Only Admins can change access")
                self.assertEqual(element_with_id(html, "table-access-add-user"), "")
                self.assertEqual(
                    element_with_id(html, f"access-remove-user-{self.alice.pk}"), ""
                )
                avatar = element_with_id(html, f"access-admin-{self.alice.pk}")
                self.assertIn('role="img"', avatar)
                self.assertIn('tabindex="0"', avatar)
                self.assertIn('aria-label="AccessAlice, Admin"', avatar)

    def test_an_organization_holding_admin_from_before_can_only_be_lowered(self):
        table = self.table("t_old_org_admin")
        old = Organization.objects.create(name="Access Old Admins")
        self.grant(table, old, ADMIN_PERM)
        held = self.organization("Access Held")
        self.grant(table, held, WRITE_PERM)

        roles = {
            h.name: [r.level for r in h.roles]
            for h in self.access("t_old_org_admin").organizations
        }
        self.assertEqual(
            roles["Access Old Admins"], [WRITE_PERM, DELETE_PERM, ADMIN_PERM]
        )
        self.assertEqual(roles["Access Held"], [WRITE_PERM, DELETE_PERM])

    def test_only_the_users_own_organizations_not_yet_holding_are_shareable(self):
        table = self.table("t_shareable")
        held = self.organization("Access Already")
        self.grant(table, held, WRITE_PERM)
        self.organization("Access Free")
        Organization.objects.create(name="Access Foreign")
        self.assertEqual(
            [o.name for o in self.access("t_shareable").shareable], ["Access Free"]
        )

    def test_a_table_not_on_the_dashboard_answers_404(self):
        theirs = Table.objects.create(name="t_not_mine")
        self.grant(theirs, self.stranger, ADMIN_PERM)
        self.drawer("t_not_mine", status=404)
        self.drawer("t_does_not_exist", status=404)
        response = self.send(
            "t_not_mine", op="add", kind="user", name="AccessAlice", level=WRITE_PERM
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.users_of(theirs), {"TablesTabStranger": ADMIN_PERM})

    def test_the_owner_rule_holds(self):
        self.table("t_owner_rule")
        foreign = reverse(
            "login:table-access",
            kwargs={"user_id": self.stranger.pk, "table_name": "t_owner_rule"},
        )
        self.assertEqual(self.client.get(foreign, **HTMX).status_code, 404)
        self.client.logout()
        self.assertEqual(self.drawer("t_owner_rule", status=401).status_code, 401)

    def test_the_drawer_costs_the_same_whatever_the_number_of_holders(self):
        small = self.table("t_few")
        large = self.table("t_many")
        organization = self.organization("Access Many")
        self.grant(small, self.alice, WRITE_PERM)
        self.grant(small, organization, WRITE_PERM)
        for index in range(20):
            user = make_user(f"AccessMany{index}")
            self.grant(large, user, WRITE_PERM)
            self.member(organization, user)
            group = Organization.objects.create(name=f"Access Group {index}")
            self.member(group, user)
            self.grant(large, group, WRITE_PERM)
        self.drawer("t_few")

        def queries(name):
            with CaptureQueriesContext(connection) as captured:
                self.drawer(name)
            return len(captured)

        self.assertEqual(queries("t_few"), queries("t_many"))


class EntryPointTests(AccessTestCase):
    def test_the_access_cell_and_the_menu_open_the_drawer(self):
        table = self.table("t_openers", level=WRITE_PERM)
        html = self.get(htmx=True).content.decode()
        target = f'hx-get="{self.access_path("t_openers")}"'
        for opener in (f"acc-{table.pk}", f"menu-{table.pk}-access"):
            with self.subTest(opener=opener):
                element = element_with_id(html, opener)
                self.assertIn(target, element)
                self.assertIn('hx-target="#table-access-body"', element)

    def test_the_drawer_sits_outside_the_tab(self):
        """Its requests must not be synced with (or cancelled by) the
        list's: the tab carries ``hx-sync``, the drawer is not inside it."""
        self.table("t_outside")
        html = self.get().content.decode()
        tab = element_with_id(html, "tables-tab")
        self.assertNotIn('id="table-access"', tab)
        self.assertIn('id="table-access"', html)


class AddTests(AccessTestCase):
    def test_an_admin_adds_a_user_with_a_role_in_one_step(self):
        table = self.table("t_add_user")
        response = self.send(
            "t_add_user", op="add", kind="user", name="AccessAlice", level=DELETE_PERM
        )
        detail = self.changed(response)
        self.assertTrue(detail["stay"])
        self.assertEqual(
            detail["message"], "Gave AccessAlice Data maintainer on “t_add_user”."
        )
        self.assertTemplateUsed(response, DRAWER)
        self.assertEqual(self.users_of(table)["AccessAlice"], DELETE_PERM)
        self.assertIn("AccessAlice", [h.name for h in response.context["access"].users])

    def test_admin_may_be_given_to_a_user(self):
        table = self.table("t_co_admin")
        self.changed(
            self.send(
                "t_co_admin",
                op="add",
                kind="user",
                name="AccessAlice",
                level=ADMIN_PERM,
            )
        )
        self.assertEqual(self.users_of(table)["AccessAlice"], ADMIN_PERM)

    def test_an_admin_shares_with_their_own_organization(self):
        table = self.table("t_share")
        organization = self.organization("Access Share")
        detail = self.changed(
            self.send(
                "t_share",
                op="add",
                kind="org",
                organization=organization.pk,
                level=DELETE_PERM,
            )
        )
        self.assertEqual(
            detail["message"], "Shared “t_share” with Access Share as Data maintainer."
        )
        self.assertEqual(self.organizations_of(table), {"Access Share": DELETE_PERM})

    def test_a_role_outside_the_list_is_refused(self):
        table = self.table("t_bad_role")
        for level in (NO_PERM, 3, 99, "admin", ""):
            with self.subTest(level=level):
                response = self.send(
                    "t_bad_role", op="add", kind="user", name="AccessAlice", level=level
                )
                self.assertEqual(response.status_code, 400)
                self.assertNothingSent(response)
                self.assertIn("level", response.context["errors"])
        self.assertEqual(list(self.users_of(table)), ["TablesTabOwner"])

    def test_an_organization_is_never_given_admin(self):
        table = self.table("t_org_admin")
        organization = self.organization("Access No Admin")
        response = self.send(
            "t_org_admin",
            op="add",
            kind="org",
            organization=organization.pk,
            level=ADMIN_PERM,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Data maintainer at most", response.context["errors"]["level"])
        self.assertEqual(self.organizations_of(table), {})

    def test_sharing_with_an_organization_the_user_is_not_in_is_refused(self):
        table = self.table("t_foreign_org")
        foreign = Organization.objects.create(name="Access Not Mine")
        plain = Group.objects.create(name="Access Plain Group")
        Membership.objects.create(user=self.user, group=plain)
        for group in (foreign, plain):
            with self.subTest(group=group.name):
                response = self.send(
                    "t_foreign_org",
                    op="add",
                    kind="org",
                    organization=group.pk,
                    level=WRITE_PERM,
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("organization", response.context["errors"])
        self.assertEqual(self.organizations_of(table), {})

    def test_an_unknown_user_is_refused(self):
        table = self.table("t_nobody")
        response = self.send(
            "t_nobody", op="add", kind="user", name="NoSuchUser", level=WRITE_PERM
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("NoSuchUser", response.context["errors"]["name"])
        self.assertEqual(list(self.users_of(table)), ["TablesTabOwner"])

    def test_a_holder_is_not_added_twice(self):
        table = self.table("t_twice")
        self.grant(table, self.alice, ADMIN_PERM)
        response = self.send(
            "t_twice", op="add", kind="user", name="AccessAlice", level=WRITE_PERM
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.users_of(table)["AccessAlice"], ADMIN_PERM)

    def test_below_admin_nothing_can_be_changed(self):
        table = self.table("t_editor_only", level=DELETE_PERM)
        self.grant(table, self.alice, ADMIN_PERM)
        for data in (
            {"op": "add", "kind": "user", "name": "AccessBob", "level": WRITE_PERM},
            {"op": "change", "holder": f"user:{self.alice.pk}", "level": WRITE_PERM},
            {"op": "remove", "holder": f"user:{self.alice.pk}"},
        ):
            with self.subTest(op=data["op"]):
                response = self.send("t_editor_only", **data)
                self.assertEqual(response.status_code, 403)
                self.assertContains(
                    response, "Only Admins can change access", status_code=403
                )
                self.assertNothingSent(response)
        self.assertEqual(
            self.users_of(table),
            {"TablesTabOwner": DELETE_PERM, "AccessAlice": ADMIN_PERM},
        )

    def test_an_unknown_change_is_refused(self):
        self.table("t_unknown_op")
        self.assertEqual(self.send("t_unknown_op", op="rename").status_code, 400)


class ChangeAndRemoveTests(AccessTestCase):
    def test_an_admin_changes_a_users_role(self):
        table = self.table("t_change")
        self.grant(table, self.alice, WRITE_PERM)
        detail = self.changed(
            self.send(
                "t_change",
                op="change",
                holder=f"user:{self.alice.pk}",
                level=ADMIN_PERM,
            )
        )
        self.assertEqual(detail["message"], "AccessAlice is now Admin on “t_change”.")
        self.assertEqual(self.users_of(table)["AccessAlice"], ADMIN_PERM)

    def test_an_organization_cannot_be_raised_to_admin(self):
        table = self.table("t_raise_org")
        organization = self.organization("Access Raise")
        self.grant(table, organization, DELETE_PERM)
        response = self.send(
            "t_raise_org",
            op="change",
            holder=f"org:{organization.pk}",
            level=ADMIN_PERM,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.organizations_of(table), {"Access Raise": DELETE_PERM})

    def test_an_old_organization_admin_grant_can_be_lowered(self):
        """Changing or removing an Organization that already holds a role
        needs no membership: that is how an old grant gets cleaned up."""
        table = self.table("t_lower_org")
        old = Organization.objects.create(name="Access Lower")
        self.grant(table, old, ADMIN_PERM)
        self.changed(
            self.send(
                "t_lower_org", op="change", holder=f"org:{old.pk}", level=DELETE_PERM
            )
        )
        self.assertEqual(self.organizations_of(table), {"Access Lower": DELETE_PERM})

    def test_the_same_role_again_changes_nothing(self):
        table = self.table("t_same")
        self.grant(table, self.alice, WRITE_PERM)
        with self.assertNoLogs(LOGGER):
            response = self.send(
                "t_same", op="change", holder=f"user:{self.alice.pk}", level=WRITE_PERM
            )
        self.assertEqual(response.status_code, 200)
        self.assertNothingSent(response)

    def test_an_admin_removes_a_holder(self):
        table = self.table("t_remove")
        organization = self.organization("Access Remove")
        self.grant(table, organization, WRITE_PERM)
        self.grant(table, self.alice, WRITE_PERM)
        self.changed(self.send("t_remove", op="remove", holder=f"user:{self.alice.pk}"))
        detail = self.changed(
            self.send("t_remove", op="remove", holder=f"org:{organization.pk}")
        )
        self.assertEqual(detail["message"], "Removed Access Remove from “t_remove”.")
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})
        self.assertEqual(self.organizations_of(table), {})

    def test_a_co_admin_may_remove_the_uploader(self):
        """Every admin is equal: there is no owner."""
        table = Table.objects.create(name="t_uploaded_by_alice")
        self.grant(table, self.alice, ADMIN_PERM)
        self.grant(table, self.user, ADMIN_PERM)
        self.changed(
            self.send(
                "t_uploaded_by_alice", op="remove", holder=f"user:{self.alice.pk}"
            )
        )
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})

    def test_a_holder_that_is_not_one_is_refused(self):
        self.table("t_ghost")
        for holder in ("", "user:", "nobody:1", f"user:{self.bob.pk}", "org:999999"):
            with self.subTest(holder=holder):
                response = self.send("t_ghost", op="remove", holder=holder)
                self.assertEqual(response.status_code, 400)
                self.assertNothingSent(response)


class LastAdminGuardTests(AccessTestCase):
    def assertGuarded(self, response):
        """Refused with the guard's reason, BEFORE any confirmation."""
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.context["notice"], LAST_ADMIN)
        self.assertIsNone(response.context.get("confirm"))
        self.assertNothingSent(response)

    def test_the_last_admin_cannot_lower_their_own_admin(self):
        table = self.table("t_last_lower")
        response = self.send(
            "t_last_lower", op="change", holder=f"user:{self.user.pk}", level=WRITE_PERM
        )
        self.assertGuarded(response)
        self.assertContains(response, "Give someone else Admin first", status_code=409)
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})

    def test_the_last_admin_cannot_remove_or_leave(self):
        table = self.table("t_last_remove")
        self.assertGuarded(
            self.send("t_last_remove", op="remove", holder=f"user:{self.user.pk}")
        )
        self.assertGuarded(self.send("t_last_remove", op="leave"))
        self.assertGuarded(
            self.send(
                "t_last_remove",
                op="remove",
                holder=f"user:{self.user.pk}",
                confirm="yes",
            )
        )
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})

    def test_an_organization_holding_admin_does_not_count(self):
        """The guard keeps a USER with direct Admin; an old Organization
        grant at Admin is no way to manage a Table by name."""
        table = self.table("t_org_does_not_count")
        old = Organization.objects.create(name="Access Old")
        self.grant(table, old, ADMIN_PERM)
        self.assertGuarded(
            self.send(
                "t_org_does_not_count", op="remove", holder=f"user:{self.user.pk}"
            )
        )

    def test_an_admin_through_an_organization_cannot_remove_the_last_direct_admin(
        self,
    ):
        table = Table.objects.create(name="t_via_org")
        self.grant(table, self.alice, ADMIN_PERM)
        old = self.organization("Access Via")
        self.grant(table, old, ADMIN_PERM)
        self.assertGuarded(
            self.send("t_via_org", op="remove", holder=f"user:{self.alice.pk}")
        )
        self.assertEqual(self.users_of(table), {"AccessAlice": ADMIN_PERM})

    def test_an_organizations_admin_grant_that_is_the_only_admin_stays(self):
        """#2595: on a Table no user holds Admin on, removing or lowering
        the last Admin grant of any kind would leave it with no Admin at
        all, so it is refused like the last user's, before any question."""
        table = Table.objects.create(name="t_only_org_admin")
        old = self.organization("Access Only Admin")
        self.grant(table, old, ADMIN_PERM)
        for data in (
            {"op": "remove", "holder": f"org:{old.pk}"},
            {"op": "remove", "holder": f"org:{old.pk}", "confirm": "yes"},
            {"op": "change", "holder": f"org:{old.pk}", "level": DELETE_PERM},
        ):
            with self.subTest(**data):
                self.assertGuarded(self.send("t_only_org_admin", **data))
        self.assertEqual(
            self.organizations_of(table), {"Access Only Admin": ADMIN_PERM}
        )

    def test_with_another_admin_grant_it_can_go(self):
        table = Table.objects.create(name="t_two_org_admins")
        old = self.organization("Access Old One")
        other = self.organization("Access Old Two", member=False)
        self.grant(table, old, ADMIN_PERM)
        self.grant(table, other, ADMIN_PERM)
        self.changed(
            self.send(
                "t_two_org_admins",
                op="change",
                holder=f"org:{old.pk}",
                level=DELETE_PERM,
                confirm="yes",
            )
        )
        self.assertEqual(
            self.organizations_of(table),
            {"Access Old One": DELETE_PERM, "Access Old Two": ADMIN_PERM},
        )

    def test_a_table_without_a_direct_admin_is_not_made_worse(self):
        """Its only Admin is an old Organization grant: adding someone, or
        changing an ordinary holder, takes nobody's direct Admin away."""
        table = Table.objects.create(name="t_no_direct_admin")
        old = self.organization("Access Only Org")
        self.grant(table, old, ADMIN_PERM)
        self.changed(
            self.send(
                "t_no_direct_admin",
                op="add",
                kind="user",
                name="AccessAlice",
                level=WRITE_PERM,
            )
        )
        self.changed(
            self.send(
                "t_no_direct_admin",
                op="change",
                holder=f"user:{self.alice.pk}",
                level=DELETE_PERM,
            )
        )
        self.assertEqual(self.users_of(table), {"AccessAlice": DELETE_PERM})

    def test_with_a_second_admin_the_change_is_only_confirmed(self):
        table = self.table("t_two_admins")
        self.grant(table, self.alice, ADMIN_PERM)
        response = self.send(
            "t_two_admins", op="change", holder=f"user:{self.user.pk}", level=WRITE_PERM
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("no longer be able to manage", response.context["confirm"])
        self.assertNothingSent(response)
        self.assertEqual(self.users_of(table)["TablesTabOwner"], ADMIN_PERM)


class ConfirmationTests(AccessTestCase):
    def test_losing_your_own_admin_takes_one_confirmation(self):
        table = self.table("t_step_back")
        self.grant(table, self.alice, ADMIN_PERM)
        data = {"op": "change", "holder": f"user:{self.user.pk}", "level": WRITE_PERM}
        question = self.send("t_step_back", **data)
        self.assertEqual(question.context["pending"]["holder"], f"user:{self.user.pk}")
        response = self.send("t_step_back", confirm="yes", **data)
        self.changed(response)
        self.assertEqual(self.users_of(table)["TablesTabOwner"], WRITE_PERM)
        # the drawer stays open, now read-only
        self.assertFalse(response.context["access"].can_manage)

    def test_losing_the_table_takes_one_confirmation_and_the_row_leaves(self):
        table = self.table("t_hand_over")
        self.grant(table, self.alice, ADMIN_PERM)
        data = {"op": "remove", "holder": f"user:{self.user.pk}"}
        question = self.send("t_hand_over", **data)
        self.assertIn("disappear from your dashboard", question.context["confirm"])
        self.assertEqual(self.users_of(table)["TablesTabOwner"], ADMIN_PERM)

        response = self.send("t_hand_over", confirm="yes", **data)
        detail = self.changed(response)
        self.assertIn("You no longer have access to “t_hand_over”", detail["message"])
        self.assertTrue(response.context["gone"])
        self.assertNotIn("TablesTabOwner", self.users_of(table))
        self.assertNotIn("t_hand_over", self.names())

    def test_removing_the_organization_you_manage_through_is_confirmed(self):
        table = self.table("t_org_access", level=None)
        self.grant(table, self.alice, ADMIN_PERM)
        organization = self.organization("Access Lifeline")
        self.grant(table, organization, WRITE_PERM)
        # a Table admin through a second, older grant
        old = self.organization("Access Old Admin Grant")
        self.grant(table, old, ADMIN_PERM)
        data = {"op": "remove", "holder": f"org:{old.pk}"}
        self.assertIn(
            "no longer be able to manage",
            self.send("t_org_access", **data).context["confirm"],
        )
        self.changed(self.send("t_org_access", confirm="yes", **data))
        self.assertIn("t_org_access", self.names())


class LeaveTests(AccessTestCase):
    def test_any_direct_holder_may_leave_after_confirming(self):
        table = self.table("t_leave", level=WRITE_PERM)
        self.grant(table, self.alice, ADMIN_PERM)
        question = self.send("t_leave", op="leave")
        self.assertIn("disappear from your dashboard", question.context["confirm"])
        self.assertNothingSent(question)

        response = self.send("t_leave", op="leave", confirm="yes")
        detail = self.changed(response)
        self.assertEqual(
            detail["message"], "You left “t_leave” and no longer have access to it."
        )
        self.assertEqual(self.users_of(table), {"AccessAlice": ADMIN_PERM})
        self.assertNotIn("t_leave", self.names())

    def test_the_leave_button_is_offered_to_direct_holders_only(self):
        table = self.table("t_leave_button", level=WRITE_PERM)
        self.grant(table, self.alice, ADMIN_PERM)
        through = self.table("t_through_org", level=None)
        organization = self.organization("Access Through")
        self.grant(through, organization, WRITE_PERM)
        self.assertNotEqual(
            element_with_id(
                self.drawer("t_leave_button").content.decode(), "access-leave"
            ),
            "",
        )
        self.assertEqual(
            element_with_id(
                self.drawer("t_through_org").content.decode(), "access-leave"
            ),
            "",
        )

    def test_access_through_an_organization_is_not_left_per_table(self):
        table = self.table("t_org_only", level=None)
        organization = self.organization("Access Org Only")
        self.grant(table, organization, WRITE_PERM)
        response = self.send("t_org_only", op="leave", confirm="yes")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.organizations_of(table), {"Access Org Only": WRITE_PERM})

    def test_leaving_keeps_access_through_an_organization(self):
        # another Table of their own keeps "direct" an option of the Access
        # filter; without one the filter value would be stale, and ignored
        self.table("t_still_direct")
        table = self.table("t_keep", level=WRITE_PERM)
        self.grant(table, self.alice, ADMIN_PERM)
        organization = self.organization("Access Keep")
        self.grant(table, organization, WRITE_PERM)
        self.assertIn(
            "keep access through an organization",
            self.send("t_keep", op="leave").context["confirm"],
        )
        response = self.send(
            "t_keep", op="leave", confirm="yes", current="?access=direct"
        )
        detail = self.changed(response)
        self.assertIn("It is not shown under the current filter.", detail["message"])
        self.assertNotIn("no longer have access", detail["message"])
        self.assertIn("t_keep", self.names())
        self.assertNotIn("t_keep", self.names({"access": "direct"}))


class LoggingTests(AccessTestCase):
    def test_one_line_per_change_with_before_and_after(self):
        table = self.table("t_logged")
        self.grant(table, self.alice, WRITE_PERM)
        cases = (
            (
                {
                    "op": "add",
                    "kind": "user",
                    "name": "AccessBob",
                    "level": DELETE_PERM,
                },
                f"holder=user:{self.bob.pk} action=add before=- after={DELETE_PERM}",
            ),
            (
                {
                    "op": "change",
                    "holder": f"user:{self.alice.pk}",
                    "level": ADMIN_PERM,
                },
                f"holder=user:{self.alice.pk} action=change before={WRITE_PERM} "
                f"after={ADMIN_PERM}",
            ),
            (
                {"op": "remove", "holder": f"user:{self.bob.pk}"},
                f"holder=user:{self.bob.pk} action=remove before={DELETE_PERM} after=-",
            ),
            (
                {"op": "leave", "confirm": "yes"},
                f"holder=user:{self.user.pk} action=leave before={ADMIN_PERM} after=-",
            ),
        )
        for data, expected in cases:
            with self.subTest(op=data["op"]):
                # the line is written once the change has committed
                with self.assertLogs(LOGGER, "INFO") as logs:
                    with self.captureOnCommitCallbacks(execute=True):
                        self.changed(self.send("t_logged", **data))
                self.assertEqual(
                    logs.output,
                    [
                        f"INFO:{LOGGER}:table_permission_write table=t_logged "
                        f"{expected} by={self.user.pk} via=dashboard"
                    ],
                )

    def test_a_refused_change_logs_nothing(self):
        self.table("t_not_logged")
        with self.assertNoLogs(LOGGER):
            with self.captureOnCommitCallbacks(execute=True):
                self.send("t_not_logged", op="leave", confirm="yes")
                self.send(
                    "t_not_logged",
                    op="add",
                    kind="user",
                    name="AccessAlice",
                    level=NO_PERM,
                )
