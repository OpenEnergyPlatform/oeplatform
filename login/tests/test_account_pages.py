"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from pathlib import Path

from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress
from django.template.loader import get_template
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from login.forms import CreateUserForm
from login.models import myuser as User

PASSWORD = "a-long-test-password"
LOGIN_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

# allauth's own layout lists these in a bare menu on every page it renders.
ALLAUTH_MENU = "Menu:"
OEP_ACCOUNT_COLUMN = 'class="login__wrap"'


class AccountPageTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            name="owner", email="owner@example.org", affiliation="Test"
        )
        self.user.set_password(PASSWORD)
        self.user.save()
        EmailAddress.objects.create(
            user=self.user, email="owner@example.org", verified=True, primary=True
        )

    def assertOepPage(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, OEP_ACCOUNT_COLUMN)
        self.assertNotContains(response, ALLAUTH_MENU)


class AllauthPagesUseTheOepLayoutTest(AccountPageTestCase):
    def test_the_allauth_layout_is_the_oep_one(self):
        """Any allauth page the OEP does not write itself still gets the OEP shell."""
        origin = Path(get_template("allauth/layouts/base.html").origin.name)

        self.assertEqual(origin.parent.parent.parent, LOGIN_TEMPLATES)

    def test_the_email_page(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("account_email"))

        self.assertOepPage(response)
        self.assertTemplateUsed(response, "account/email_change.html")
        self.assertContains(response, "owner@example.org")

    def test_the_email_page_shows_a_pending_change(self):
        EmailAddress.objects.create(
            user=self.user, email="new@example.org", verified=False, primary=False
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("account_email"))

        self.assertContains(response, "new@example.org")
        self.assertContains(response, 'name="action_remove"')

    def test_the_email_page_shows_why_an_address_is_refused(self):
        self.client.force_login(self.user)
        self.client.post(reverse("account_reauthenticate"), {"password": PASSWORD})

        response = self.client.post(
            reverse("account_email"), {"action_add": "", "email": "not-an-address"}
        )

        self.assertOepPage(response)
        self.assertContains(response, "invalid-feedback")

    def test_the_password_prompt(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("account_reauthenticate"))

        self.assertOepPage(response)
        self.assertContains(response, 'name="password"')

    def test_a_wrong_password_is_said_so(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("account_reauthenticate"), {"password": "wrong"}
        )

        self.assertOepPage(response)
        self.assertContains(response, "invalid-feedback")

    def test_the_connected_accounts_page(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("socialaccount_connections"))

        self.assertOepPage(response)
        self.assertNotContains(response, reverse("account_set_password"))

    def test_an_account_without_a_password_is_told_how_to_get_one(self):
        self.user.set_unusable_password()
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse("socialaccount_connections"))

        self.assertContains(response, reverse("account_set_password"))

    def test_the_inactive_page(self):
        response = self.client.get(reverse("account_inactive"))

        self.assertOepPage(response)
        self.assertContains(response, reverse("base:contact"))

    def test_the_cancelled_sign_in_page(self):
        response = self.client.get(reverse("socialaccount_login_cancelled"))

        self.assertOepPage(response)
        self.assertContains(response, reverse("account_login"))


class TheSettingsPageLinksTheAccountPagesTest(AccountPageTestCase):
    def settings_page(self):
        self.client.force_login(self.user)
        return self.client.get(reverse("login:settings", args=[self.user.id]))

    def test_it_links_the_email_page_and_the_connected_accounts(self):
        response = self.settings_page()

        self.assertContains(response, reverse("account_email"))
        self.assertContains(response, reverse("socialaccount_connections"))
        self.assertContains(response, reverse("account_change_password"))

    def test_an_account_without_a_password_is_offered_to_set_one(self):
        self.user.set_unusable_password()
        self.user.save()

        response = self.settings_page()

        self.assertContains(response, reverse("account_set_password"))
        self.assertNotContains(response, reverse("account_change_password"))


class TheSecondPasswordResetIsGoneTest(TestCase):
    """allauth's reset at /accounts/password/reset/ is the one the login page links."""

    def test_its_routes_are_gone(self):
        for name in (
            "password_reset",
            "password_reset_done",
            "password_reset_confirm",
            "password_reset_complete",
        ):
            with self.subTest(name=name), self.assertRaises(NoReverseMatch):
                reverse(f"login:{name}")

    def test_its_address_answers_404(self):
        self.assertEqual(self.client.get("/user/password_reset/").status_code, 404)

    def test_the_allauth_reset_still_works(self):
        self.assertEqual(
            self.client.get(reverse("account_reset_password")).status_code, 200
        )


class SignupRequiresAnEmailTest(TestCase):
    """ACCOUNT_SIGNUP_FIELDS keeps the fields ACCOUNT_EMAIL_REQUIRED used to require."""

    def test_the_signup_form_requires_email_username_and_both_passwords(self):
        form = CreateUserForm()

        self.assertTrue(issubclass(CreateUserForm, SignupForm))
        for name in ("email", "username", "password1", "password2"):
            with self.subTest(field=name):
                self.assertIn(name, form.fields)
                self.assertTrue(form.fields[name].required)

    def test_a_signup_without_an_email_is_refused(self):
        form = CreateUserForm(
            data={
                "username": "newcomer",
                "password1": PASSWORD,
                "password2": PASSWORD,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
