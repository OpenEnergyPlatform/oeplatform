"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Field errors on the account forms are shown as errors.

Sign-up, set-password and reset-password used to put every field error in a
green "success" alert, and the reset form looked for errors on a field it does
not have (`login` instead of `email`), so its errors were never shown at all.
"""  # noqa: 501

from django.test import TestCase
from django.urls import reverse

from login.models import myuser as User


class AccountErrorAlertTest(TestCase):
    def assert_error_shown_as_error(self, response):
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("login__alert--danger", html)
        self.assertNotIn("login__alert--success", html)

    def test_sign_up(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "",
                "email": "not-an-email",
                "password1": "a",
                "password2": "b",
            },
        )
        self.assert_error_shown_as_error(response)

    def test_reset_password(self):
        response = self.client.post(
            reverse("account_reset_password"), {"email": "not-an-email"}
        )
        self.assert_error_shown_as_error(response)
        self.assertIn("valid email", response.content.decode().lower())

    def test_set_password(self):
        user = User.objects.create_user(  # type: ignore
            name="no_password", email="no_password@test.test", affiliation="test"
        )
        user.set_unusable_password()
        user.save()
        self.client.force_login(user)
        response = self.client.post(
            reverse("account_set_password"),
            {"password1": "Correct-horse-1", "password2": "different-2"},
        )
        self.assert_error_shown_as_error(response)
