"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Organization writes are checked before they happen.

Every organization view requires a login, the caller's membership level is
checked before the form is saved or a membership is changed, and a refused
write leaves the database as it was. Refusal codes follow the views' own
convention: no membership is 404, a membership below the level an action
needs is 403, no login is the login redirect.
"""  # noqa: 501

from django.test import TestCase
from django.urls import reverse

from login.models import (
    ADMIN_PERM,
    DELETE_PERM,
    WRITE_PERM,
    Membership,
    Organization,
)
from login.tests.helpers import HTMX, act_as, make_user


class OrganizationFixture(TestCase):
    """One organization: an admin, a second admin, a Remove-level and an
    Invite-level member. The stranger is in no organization."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user("OrgCheckAdmin")
        cls.second_admin = make_user("OrgCheckSecondAdmin")
        cls.remover = make_user("OrgCheckRemover")
        cls.inviter = make_user("OrgCheckInviter")
        cls.stranger = make_user("OrgCheckStranger")
        cls.newcomer = make_user("OrgCheckNewcomer")
        cls.organization = Organization.objects.create(
            name="org_check_original", description="original description"
        )
        for user, level in (
            (cls.admin, ADMIN_PERM),
            (cls.second_admin, ADMIN_PERM),
            (cls.remover, DELETE_PERM),
            (cls.inviter, WRITE_PERM),
        ):
            Membership.objects.create(user=user, group=cls.organization, level=level)

    def level_of(self, user):
        membership = Membership.objects.filter(
            group=self.organization, user=user
        ).first()
        return membership.level if membership else None

    def own_organizations_page(self, user):
        return reverse("login:organizations", kwargs={"user_id": user.pk})

    def assert_redirects_to_own_page(self, response, user):
        """HX-Redirect to the caller's own organizations page, which the
        owner rule lets them open."""
        self.assertEqual(response["HX-Redirect"], self.own_organizations_page(user))
        self.assertEqual(self.client.get(response["HX-Redirect"]).status_code, 200)


class RenameIsCheckedBeforeSavingTests(OrganizationFixture):
    def edit_url(self):
        return reverse(
            "login:organization-edit",
            kwargs={"organization_id": self.organization.pk},
        )

    def rename_as(self, user):
        act_as(self.client, user)
        return self.client.post(
            self.edit_url(),
            {"name": "org_check_renamed", "description": "renamed"},
            **HTMX,
        )

    def assert_unchanged(self):
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "org_check_original")
        self.assertEqual(self.organization.description, "original description")

    def test_admin_renames(self):
        response = self.rename_as(self.admin)
        self.assertEqual(response.status_code, 200)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "org_check_renamed")

    def test_non_member_is_refused_and_nothing_changes(self):
        response = self.rename_as(self.stranger)
        self.assertEqual(response.status_code, 404)
        self.assert_unchanged()

    def test_member_below_admin_is_refused_and_nothing_changes(self):
        for member in (self.remover, self.inviter):
            with self.subTest(member=member.name):
                response = self.rename_as(member)
                self.assertEqual(response.status_code, 403)
                self.assert_unchanged()

    def test_anonymous_is_sent_to_login_and_nothing_changes(self):
        response = self.rename_as(None)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])
        self.assert_unchanged()

    def test_unknown_organization_is_404(self):
        act_as(self.client, self.admin)
        response = self.client.post(
            reverse("login:organization-edit", kwargs={"organization_id": 999999}),
            {"name": "org_check_renamed", "description": "renamed"},
            **HTMX,
        )
        self.assertEqual(response.status_code, 404)


class CreateAlwaysHasAnOwnerTests(OrganizationFixture):
    url = reverse("login:organization-create")

    def test_anonymous_create_leaves_no_organization(self):
        before = Organization.objects.count()
        for headers in ({}, HTMX):
            with self.subTest(htmx=bool(headers)):
                response = self.client.post(
                    self.url,
                    {"name": "org_check_ownerless", "description": "d"},
                    **headers,
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(Organization.objects.count(), before)
        self.assertFalse(
            Organization.objects.filter(name="org_check_ownerless").exists()
        )

    def test_logged_in_create_makes_the_caller_its_admin(self):
        act_as(self.client, self.stranger)
        response = self.client.post(
            self.url, {"name": "org_check_new", "description": "d"}, **HTMX
        )
        organization = Organization.objects.get(name="org_check_new")
        self.assertEqual(
            Membership.objects.get(group=organization, user=self.stranger).level,
            ADMIN_PERM,
        )
        self.assert_redirects_to_own_page(response, self.stranger)


class LeaveAndDeleteRedirectTests(OrganizationFixture):
    """Leave and delete send the caller to their own organizations page.

    WF-09 found these redirects hard-coded to user 1's page, so the caller
    used here is deliberately one whose pk is not 1.
    """

    def caller_other_than_user_one(self, *candidates):
        callers = [user for user in candidates if user.pk != 1]
        self.assertTrue(callers, "every candidate caller has pk 1")
        return callers[0]

    def test_leave_redirects_to_own_page(self):
        caller = self.caller_other_than_user_one(self.inviter, self.remover)
        act_as(self.client, caller)
        response = self.client.post(
            reverse(
                "login:organization-leave",
                kwargs={"organization_id": self.organization.pk},
            ),
            **HTMX,
        )
        self.assertIsNone(self.level_of(caller))
        self.assert_redirects_to_own_page(response, caller)

    def test_delete_redirects_to_own_page(self):
        caller = self.caller_other_than_user_one(self.admin, self.second_admin)
        act_as(self.client, caller)
        response = self.client.post(
            reverse(
                "login:organization-delete",
                kwargs={"organization_id": self.organization.pk},
            ),
            **HTMX,
        )
        self.assertFalse(Organization.objects.filter(pk=self.organization.pk).exists())
        self.assert_redirects_to_own_page(response, caller)


class MemberChangesAreCheckedFirstTests(OrganizationFixture):
    def members_url(self):
        return reverse(
            "login:partial-organization-membership",
            kwargs={"organization_id": self.organization.pk},
        )

    def post_as(self, user, data):
        act_as(self.client, user)
        return self.client.post(self.members_url(), data, **HTMX)

    def test_member_list_needs_a_membership(self):
        act_as(self.client, self.inviter)
        self.assertContains(
            self.client.get(self.members_url(), **HTMX), "OrgCheckAdmin"
        )

        act_as(self.client, self.stranger)
        response = self.client.get(self.members_url(), **HTMX)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("OrgCheckAdmin", response.content.decode())

        act_as(self.client, None)
        response = self.client.get(self.members_url(), **HTMX)
        self.assertEqual(response.status_code, 302)

    def test_add_user_refused_for_non_member_and_anonymous(self):
        for user, status in ((self.stranger, 404), (None, 302)):
            with self.subTest(user=getattr(user, "name", "anonymous")):
                response = self.post_as(
                    user, {"mode": "add_user", "name": self.newcomer.name}
                )
                self.assertEqual(response.status_code, status)
                self.assertIsNone(self.level_of(self.newcomer))

    def test_add_user_by_an_inviter(self):
        response = self.post_as(
            self.inviter, {"mode": "add_user", "name": self.newcomer.name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.level_of(self.newcomer))

    def test_remove_refused_below_remove_level(self):
        response = self.post_as(
            self.inviter, {"mode": "remove_user", "user_id": self.remover.pk}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.level_of(self.remover), DELETE_PERM)

    def test_remove_of_a_higher_level_is_refused_and_kept(self):
        response = self.post_as(
            self.remover, {"mode": "remove_user", "user_id": self.admin.pk}
        )
        self.assertContains(response, "higher permission level")
        self.assertEqual(self.level_of(self.admin), ADMIN_PERM)

    def test_removing_yourself_is_refused_and_kept(self):
        response = self.post_as(
            self.remover, {"mode": "remove_user", "user_id": self.remover.pk}
        )
        self.assertContains(response, "leave the organization")
        self.assertEqual(self.level_of(self.remover), DELETE_PERM)

    def test_remove_at_or_below_own_level(self):
        response = self.post_as(
            self.remover, {"mode": "remove_user", "user_id": self.inviter.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.level_of(self.inviter))

    def test_level_change_refused_below_admin(self):
        response = self.post_as(
            self.remover,
            {
                "mode": "alter_user",
                "user_id": self.inviter.pk,
                "selected_value": ADMIN_PERM,
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.level_of(self.inviter), WRITE_PERM)
