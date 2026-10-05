"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The Table's own permission page (#2567, spec #2551) through HTTP: it goes
through the same permission service as the dashboard's access drawer, so
the same rules hold here (a role chosen when adding, no "None" role,
Organizations capped at Data maintainer and shared only by their members,
the last-admin guard ordered before the self-demotion confirmation), and
every refusal is a message on the page rather than a server error or a
silent write. Four defects the page had before (WF-03 finding 7) each have
a test: an unknown user name was a 500, a level was never checked, the last
admin could remove themself, and adding took a second request to set a
role.

Assertions are on status, the messages shown, what the database holds
afterwards and the log line; never on markup details.
"""  # noqa: 501

from django.contrib.messages import get_messages
from django.urls import reverse

from dataedit.models import Table
from login.models import ADMIN_PERM, DELETE_PERM, NO_PERM, WRITE_PERM
from login.table_roles import LAST_ADMIN, ONLY_ADMINS
from login.tests.test_table_access import LOGGER, AccessTestCase

PAGE = "dataedit/table_permissions.html"


class PermissionPageTestCase(AccessTestCase):
    def page_path(self, name):
        return reverse("dataedit:table-permission", kwargs={"table": name})

    def page(self, name):
        response = self.client.get(self.page_path(name))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, PAGE)
        return response

    def post(self, table_name, /, **data):
        return self.client.post(self.page_path(table_name), data)

    def messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def assertDone(self, response, message):
        """Redirected back to the page, the change named in a message."""
        self.assertRedirects(
            response,
            self.page_path(response.wsgi_request.resolver_match.kwargs["table"]),
        )
        self.assertEqual(self.messages(response), [message])

    def assertRefused(self, response, status, message):
        """The page again, with the reason as a message; nothing asked."""
        self.assertEqual(response.status_code, status, response.content)
        self.assertTemplateUsed(response, PAGE)
        self.assertEqual(self.messages(response), [message])
        self.assertIsNone(response.context.get("confirm"))
        self.assertContains(response, message, status_code=status)
        self.assertContains(response, "alert-danger", status_code=status)

    def offered(self, response, holder_key):
        """The levels a Holder's role choice offers."""
        holder = response.context["access"].holder(holder_key)
        return [role.level for role in holder.roles]


class PageTests(PermissionPageTestCase):
    def test_anyone_may_read_who_holds_which_role(self):
        table = self.table("t_page_read")
        organization = self.organization("PageReadOrg")
        self.grant(table, self.alice, WRITE_PERM)
        self.grant(table, organization, DELETE_PERM)
        self.client.logout()
        response = self.page("t_page_read")
        access = response.context["access"]
        self.assertEqual(
            [(h.name, h.role) for h in access.holders],
            [
                ("TablesTabOwner", "Admin"),
                ("AccessAlice", "Data editor"),
                ("PageReadOrg", "Data maintainer"),
            ],
        )
        self.assertFalse(response.context["is_admin"])
        self.assertNotContains(response, 'name="mode"')

    def test_a_holder_below_admin_reads_and_changes_nothing(self):
        table = self.table("t_page_editor", level=WRITE_PERM)
        self.grant(table, self.alice, ADMIN_PERM)
        response = self.page("t_page_editor")
        self.assertFalse(response.context["is_admin"])
        self.assertNotContains(response, 'name="mode"')

    def test_no_none_role_is_offered(self):
        table = self.table("t_page_roles")
        organization = self.organization("PageRolesOrg")
        self.grant(table, self.alice, WRITE_PERM)
        self.grant(table, organization, WRITE_PERM)
        response = self.page("t_page_roles")
        self.assertEqual(
            self.offered(response, f"user:{self.alice.pk}"),
            [WRITE_PERM, DELETE_PERM, ADMIN_PERM],
        )
        self.assertEqual(
            [role.level for role in response.context["roles"]],
            [WRITE_PERM, DELETE_PERM, ADMIN_PERM],
        )
        self.assertNotContains(response, f'<option value="{NO_PERM}"')

    def test_the_organization_choice_stops_at_data_maintainer(self):
        table = self.table("t_page_org_roles")
        current = self.organization("PageOrgCurrent")
        old = self.organization("PageOrgOld")
        self.grant(table, current, WRITE_PERM)
        self.grant(table, old, ADMIN_PERM)
        response = self.page("t_page_org_roles")
        self.assertEqual(
            self.offered(response, f"org:{current.pk}"), [WRITE_PERM, DELETE_PERM]
        )
        # an Admin grant from before the rule shows what it holds, and can
        # only be lowered
        self.assertEqual(
            self.offered(response, f"org:{old.pk}"),
            [WRITE_PERM, DELETE_PERM, ADMIN_PERM],
        )
        self.assertEqual(
            [role.level for role in response.context["organization_roles"]],
            [WRITE_PERM, DELETE_PERM],
        )

    def test_only_own_organizations_not_yet_holding_are_offered_to_add(self):
        table = self.table("t_page_shareable")
        mine = self.organization("PageMine")
        holding = self.organization("PageHolding")
        self.organization("PageNotMine", member=False)
        self.grant(table, holding, WRITE_PERM)
        response = self.page("t_page_shareable")
        self.assertEqual(response.context["access"].shareable, [mine])
        self.assertContains(response, f'<option value="{mine.pk}">PageMine</option>')
        self.assertNotContains(response, "PageNotMine")


class AddTests(PermissionPageTestCase):
    def test_a_user_is_added_with_a_role_in_one_request(self):
        """Defect 4: adding used to create a "None" grant, and setting the
        role took a second request."""
        table = self.table("t_page_add")
        response = self.post(
            "t_page_add", mode="add_user", name="AccessAlice", level=DELETE_PERM
        )
        self.assertDone(response, "Gave AccessAlice Data maintainer on “t_page_add”.")
        self.assertEqual(
            self.users_of(table),
            {"TablesTabOwner": ADMIN_PERM, "AccessAlice": DELETE_PERM},
        )

    def test_an_unknown_user_name_is_a_message_not_a_500(self):
        """Defect 1: ``get_or_create(holder=None)`` on a NOT NULL key."""
        table = self.table("t_page_unknown")
        response = self.post(
            "t_page_unknown", mode="add_user", name="Nobody", level=WRITE_PERM
        )
        self.assertRefused(response, 400, "There is no user named “Nobody”.")
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})

    def test_an_add_without_a_name_or_a_role_is_refused(self):
        table = self.table("t_page_add_blank")
        self.assertRefused(
            self.post("t_page_add_blank", mode="add_user", name="", level=WRITE_PERM),
            400,
            "Name the user to add.",
        )
        for level in ("", NO_PERM, "99", "admin"):
            with self.subTest(level=level):
                response = self.post(
                    "t_page_add_blank", mode="add_user", name="AccessAlice", level=level
                )
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})

    def test_a_holder_is_not_added_twice(self):
        table = self.table("t_page_twice")
        self.grant(table, self.alice, WRITE_PERM)
        self.assertRefused(
            self.post(
                "t_page_twice", mode="add_user", name="AccessAlice", level=ADMIN_PERM
            ),
            400,
            "AccessAlice already holds Data editor. "
            "Change their role in the list instead.",
        )
        self.assertEqual(self.users_of(table)["AccessAlice"], WRITE_PERM)

    def test_an_own_organization_is_added_with_a_role(self):
        table = self.table("t_page_share")
        organization = self.organization("PageShareOrg")
        response = self.post(
            "t_page_share",
            mode="add_group",
            organization=organization.pk,
            level=DELETE_PERM,
        )
        self.assertDone(
            response,
            "Shared “t_page_share” with PageShareOrg as Data maintainer.",
        )
        self.assertEqual(self.organizations_of(table), {"PageShareOrg": DELETE_PERM})

    def test_an_organization_is_never_given_admin(self):
        table = self.table("t_page_org_admin")
        organization = self.organization("PageOrgAdmin")
        self.assertRefused(
            self.post(
                "t_page_org_admin",
                mode="add_group",
                organization=organization.pk,
                level=ADMIN_PERM,
            ),
            400,
            "An organization can be given Data maintainer at most. "
            "Admin is given to users, by name.",
        )
        self.assertEqual(self.organizations_of(table), {})

    def test_an_organization_the_user_is_not_in_is_refused(self):
        table = self.table("t_page_foreign_org")
        foreign = self.organization("PageForeignOrg", member=False)
        for who in (foreign.pk, "PageForeignOrg", ""):
            with self.subTest(organization=who):
                self.assertRefused(
                    self.post(
                        "t_page_foreign_org",
                        mode="add_group",
                        organization=who,
                        level=WRITE_PERM,
                    ),
                    400,
                    "You can share a table only with organizations you are a "
                    "member of.",
                )
        self.assertEqual(self.organizations_of(table), {})


class ChangeAndRemoveTests(PermissionPageTestCase):
    def test_an_admin_changes_and_removes_a_user(self):
        table = self.table("t_page_change")
        self.grant(table, self.alice, WRITE_PERM)
        self.assertDone(
            self.post(
                "t_page_change",
                mode="alter_user",
                user_id=self.alice.pk,
                level=ADMIN_PERM,
            ),
            "AccessAlice is now Admin on “t_page_change”.",
        )
        self.assertEqual(self.users_of(table)["AccessAlice"], ADMIN_PERM)
        self.assertDone(
            self.post("t_page_change", mode="remove_user", user_id=self.alice.pk),
            "Removed AccessAlice from “t_page_change”.",
        )
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})

    def test_an_unvalidated_level_is_refused(self):
        """Defect 2: ``int(level)`` was stored unchecked."""
        table = self.table("t_page_level")
        organization = self.organization("PageLevelOrg")
        self.grant(table, self.alice, WRITE_PERM)
        self.grant(table, organization, WRITE_PERM)
        for level in (NO_PERM, 5, 99, "x", ""):
            with self.subTest(level=level):
                self.assertRefused(
                    self.post(
                        "t_page_level",
                        mode="alter_user",
                        user_id=self.alice.pk,
                        level=level,
                    ),
                    400,
                    "Choose one of the roles: Data editor, Data maintainer, Admin.",
                )
        self.assertRefused(
            self.post(
                "t_page_level",
                mode="alter_group",
                group_id=organization.pk,
                level=ADMIN_PERM,
            ),
            400,
            "An organization can be given Data maintainer at most. "
            "Admin is given to users, by name.",
        )
        self.assertEqual(self.users_of(table)["AccessAlice"], WRITE_PERM)
        self.assertEqual(self.organizations_of(table), {"PageLevelOrg": WRITE_PERM})

    def test_an_old_organization_admin_grant_can_be_lowered_and_removed(self):
        table = self.table("t_page_old_org")
        organization = self.organization("PageOldOrg", member=False)
        self.grant(table, organization, ADMIN_PERM)
        self.assertDone(
            self.post(
                "t_page_old_org",
                mode="alter_group",
                group_id=organization.pk,
                level=DELETE_PERM,
            ),
            "PageOldOrg is now Data maintainer on “t_page_old_org”.",
        )
        self.assertDone(
            self.post("t_page_old_org", mode="remove_group", group_id=organization.pk),
            "Removed PageOldOrg from “t_page_old_org”.",
        )
        self.assertEqual(self.organizations_of(table), {})

    def test_the_same_role_again_changes_nothing(self):
        table = self.table("t_page_same")
        self.grant(table, self.alice, WRITE_PERM)
        with self.assertNoLogs(LOGGER):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.post(
                    "t_page_same",
                    mode="alter_user",
                    user_id=self.alice.pk,
                    level=WRITE_PERM,
                )
        self.assertDone(response, "Nothing changed: they already hold that role.")

    def test_a_holder_that_is_not_one_is_refused(self):
        self.table("t_page_not_holder")
        for data in (
            {"mode": "alter_user", "user_id": self.bob.pk, "level": WRITE_PERM},
            {"mode": "remove_user", "user_id": self.bob.pk},
            {"mode": "remove_user"},
            {"mode": "remove_group", "group_id": "x"},
        ):
            with self.subTest(**data):
                self.assertEqual(
                    self.post("t_page_not_holder", **data).status_code, 400
                )

    def test_an_unknown_or_missing_mode_is_refused_not_a_500(self):
        table = self.table("t_page_mode")
        for data in ({"mode": "make_admin"}, {}):
            with self.subTest(**data):
                self.assertRefused(
                    self.post("t_page_mode", **data), 400, "Choose a change to make."
                )
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})


class WhoMayChangeTests(PermissionPageTestCase):
    def test_below_admin_every_change_is_refused_on_the_page(self):
        table = self.table("t_page_not_admin", level=DELETE_PERM)
        self.grant(table, self.alice, ADMIN_PERM)
        for data in (
            {"mode": "add_user", "name": "AccessBob", "level": WRITE_PERM},
            {"mode": "alter_user", "user_id": self.alice.pk, "level": WRITE_PERM},
            {"mode": "remove_user", "user_id": self.alice.pk},
        ):
            with self.subTest(mode=data["mode"]):
                self.assertRefused(
                    self.post("t_page_not_admin", **data), 403, ONLY_ADMINS
                )
        self.assertEqual(
            self.users_of(table),
            {"TablesTabOwner": DELETE_PERM, "AccessAlice": ADMIN_PERM},
        )

    def test_an_anonymous_change_is_forbidden(self):
        table = self.table("t_page_anonymous")
        self.client.logout()
        response = self.post(
            "t_page_anonymous", mode="add_user", name="AccessAlice", level=WRITE_PERM
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})


class LastAdminAndConfirmationTests(PermissionPageTestCase):
    def test_the_last_admin_cannot_remove_or_lower_themself(self):
        """Defect 3, refused before any confirmation is asked."""
        table = self.table("t_page_last")
        own = {"user_id": self.user.pk}
        for data in (
            {"mode": "remove_user", **own},
            {"mode": "remove_user", "confirm": "yes", **own},
            {"mode": "alter_user", "level": DELETE_PERM, **own},
        ):
            with self.subTest(**data):
                self.assertRefused(self.post("t_page_last", **data), 409, LAST_ADMIN)
        self.assertEqual(self.users_of(table), {"TablesTabOwner": ADMIN_PERM})

    def test_an_organization_holding_admin_does_not_count_as_the_last_admin(self):
        table = self.table("t_page_last_org")
        organization = self.organization("PageLastOrg")
        self.grant(table, organization, ADMIN_PERM)
        self.assertRefused(
            self.post("t_page_last_org", mode="remove_user", user_id=self.user.pk),
            409,
            LAST_ADMIN,
        )

    def test_an_organizations_only_admin_grant_cannot_be_removed(self):
        """#2595: the Table would be left with no Admin at all."""
        table = Table.objects.create(name="t_page_only_org")
        organization = self.organization("PageOnlyOrg")
        self.grant(table, organization, ADMIN_PERM)
        for data in (
            {"mode": "remove_group", "group_id": organization.pk},
            {"mode": "alter_group", "group_id": organization.pk, "level": WRITE_PERM},
        ):
            with self.subTest(**data):
                self.assertRefused(
                    self.post("t_page_only_org", **data), 409, LAST_ADMIN
                )
        self.assertEqual(self.organizations_of(table), {"PageOnlyOrg": ADMIN_PERM})

    def test_losing_your_own_admin_takes_one_confirmation(self):
        table = self.table("t_page_confirm")
        self.grant(table, self.alice, ADMIN_PERM)
        data = {"mode": "alter_user", "user_id": self.user.pk, "level": DELETE_PERM}
        response = self.post("t_page_confirm", **data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["confirm"],
            "You will no longer be able to manage this table's access.",
        )
        # the question carries the change, to be sent again with confirm=yes
        self.assertEqual(
            {k: v for k, v in response.context["pending"].items() if v},
            {k: str(v) for k, v in data.items()},
        )
        self.assertContains(response, 'name="confirm" value="yes"')
        self.assertEqual(self.users_of(table)["TablesTabOwner"], ADMIN_PERM)
        self.assertDone(
            self.post("t_page_confirm", confirm="yes", **data),
            "TablesTabOwner is now Data maintainer on “t_page_confirm”.",
        )
        self.assertEqual(self.users_of(table)["TablesTabOwner"], DELETE_PERM)

    def test_removing_yourself_is_confirmed_then_done(self):
        table = self.table("t_page_leave")
        self.grant(table, self.alice, ADMIN_PERM)
        data = {"mode": "remove_user", "user_id": self.user.pk}
        response = self.post("t_page_leave", **data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("disappear from your dashboard", response.context["confirm"])
        self.assertIn("TablesTabOwner", self.users_of(table))
        self.post("t_page_leave", confirm="yes", **data)
        self.assertEqual(self.users_of(table), {"AccessAlice": ADMIN_PERM})


class LoggingTests(PermissionPageTestCase):
    def test_each_change_logs_one_line_via_the_table_page(self):
        table = self.table("t_page_logged")
        organization = self.organization("PageLoggedOrg")
        cases = (
            (
                {"mode": "add_user", "name": "AccessAlice", "level": WRITE_PERM},
                f"holder=user:{self.alice.pk} action=add before=- after={WRITE_PERM}",
            ),
            (
                {"mode": "alter_user", "user_id": self.alice.pk, "level": ADMIN_PERM},
                f"holder=user:{self.alice.pk} action=change before={WRITE_PERM} "
                f"after={ADMIN_PERM}",
            ),
            (
                {
                    "mode": "add_group",
                    "organization": organization.pk,
                    "level": DELETE_PERM,
                },
                f"holder=org:{organization.pk} action=add before=- "
                f"after={DELETE_PERM}",
            ),
            (
                {"mode": "remove_group", "group_id": organization.pk},
                f"holder=org:{organization.pk} action=remove before={DELETE_PERM} "
                "after=-",
            ),
        )
        for data, expected in cases:
            with self.subTest(mode=data["mode"]):
                with self.assertLogs(LOGGER, "INFO") as logs:
                    with self.captureOnCommitCallbacks(execute=True):
                        self.assertEqual(
                            self.post("t_page_logged", **data).status_code, 302
                        )
                self.assertEqual(
                    logs.output,
                    [
                        f"INFO:{LOGGER}:table_permission_write table=t_page_logged "
                        f"{expected} by={self.user.pk} via=table-page"
                    ],
                )
        self.assertEqual(len(self.users_of(table)), 2)

    def test_a_refused_change_logs_nothing(self):
        self.table("t_page_quiet")
        with self.assertNoLogs(LOGGER):
            with self.captureOnCommitCallbacks(execute=True):
                self.post("t_page_quiet", mode="remove_user", user_id=self.user.pk)
                self.post(
                    "t_page_quiet", mode="add_user", name="Nobody", level=WRITE_PERM
                )
