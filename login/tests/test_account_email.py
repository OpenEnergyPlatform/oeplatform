"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from login.models import myuser as User

PASSWORD = "a-long-test-password"


class AccountEmailTestCase(TestCase):
    """The account's email address, managed at /accounts/email/.

    `force_login` leaves no authentication record in the session, which is
    what a session looks like once the reauthentication window has passed.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            name="owner", email="owner@example.org", affiliation="Test"
        )
        self.user.set_password(PASSWORD)
        self.user.save()
        EmailAddress.objects.create(
            user=self.user, email="owner@example.org", verified=True, primary=True
        )
        self.client.force_login(self.user)
        self.url = reverse("account_email")

    def add(self, email):
        return self.client.post(self.url, {"action_add": "", "email": email})

    def reauthenticate(self):
        return self.client.post(
            reverse("account_reauthenticate"), {"password": PASSWORD}
        )

    def addresses(self):
        return set(
            EmailAddress.objects.filter(user=self.user).values_list("email", flat=True)
        )


class ChangingTheAddressAsksForThePasswordTest(AccountEmailTestCase):
    def test_adding_an_address_asks_for_the_password_first(self):
        response = self.add("new@example.org")

        self.assertRedirects(
            response,
            reverse("account_reauthenticate") + "?next=" + self.url,
            fetch_redirect_response=False,
        )
        self.assertEqual(self.addresses(), {"owner@example.org"})
        self.assertEqual(mail.outbox, [])

    def test_making_another_address_primary_asks_for_the_password_first(self):
        EmailAddress.objects.create(
            user=self.user, email="other@example.org", verified=True, primary=False
        )

        response = self.client.post(
            self.url, {"action_primary": "", "email": "other@example.org"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response["Location"].startswith(reverse("account_reauthenticate"))
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "owner@example.org")

    def test_removing_an_address_asks_for_the_password_first(self):
        EmailAddress.objects.create(
            user=self.user, email="other@example.org", verified=True, primary=False
        )

        response = self.client.post(
            self.url, {"action_remove": "", "email": "other@example.org"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response["Location"].startswith(reverse("account_reauthenticate"))
        )
        self.assertEqual(self.addresses(), {"owner@example.org", "other@example.org"})

    def test_a_wrong_password_does_not_open_the_page(self):
        self.client.post(reverse("account_reauthenticate"), {"password": "wrong"})

        response = self.add("new@example.org")

        self.assertTrue(
            response["Location"].startswith(reverse("account_reauthenticate"))
        )
        self.assertEqual(self.addresses(), {"owner@example.org"})

    def test_after_the_password_the_address_can_be_added(self):
        self.reauthenticate()

        self.add("new@example.org")

        self.assertEqual(self.addresses(), {"owner@example.org", "new@example.org"})
        self.assertFalse(EmailAddress.objects.get(email="new@example.org").verified)


class AConfirmedChangeReplacesTheAddressTest(AccountEmailTestCase):
    def change_to(self, email):
        self.reauthenticate()
        self.add(email)
        mail.outbox.clear()
        address = EmailAddress.objects.get(user=self.user, email=email)
        key = EmailConfirmationHMAC(address).key
        self.client.post(reverse("account_confirm_email", args=[key]))

    def test_the_new_address_replaces_the_old_one(self):
        self.change_to("new@example.org")

        self.assertEqual(self.addresses(), {"new@example.org"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.org")

    def test_the_previous_address_is_told(self):
        self.change_to("new@example.org")

        told = [m for m in mail.outbox if m.to == ["owner@example.org"]]
        self.assertEqual(len(told), 1)
        self.assertIn("new@example.org", told[0].body)

    def test_an_account_keeps_one_pending_address_at_most(self):
        self.reauthenticate()

        self.add("first@example.org")
        self.add("second@example.org")

        self.assertEqual(self.addresses(), {"owner@example.org", "second@example.org"})
