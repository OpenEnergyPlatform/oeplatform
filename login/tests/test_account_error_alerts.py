"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Field errors on the account forms are shown as errors.

Sign-up, set-password and reset-password used to put every field error in a
green "success" alert, and the reset form looked for errors on a field it does
not have (`login` instead of `email`), so its errors were never shown at all.
Each test posts input that fails exactly one field and checks that this
field's own message appears inside a red alert.
"""  # noqa: 501

import re

from captcha.models import CaptchaStore
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from login.tests.helpers import make_user

DANGER_ALERT = re.compile(
    r'<div class="login__alert login__alert--danger[^"]*">(.*?)</div>', re.S
)


class AccountErrorAlertTest(TestCase):
    def assert_field_error_shown_as_error(self, response, field):
        self.assertEqual(response.status_code, 200)
        errors = response.context["form"].errors
        self.assertIn(field, errors, f"expected an error on {field!r}: {errors}")
        alerts = DANGER_ALERT.findall(response.content.decode())
        for message in errors[field]:
            self.assertTrue(
                any(escape(message) in alert for alert in alerts),
                f"{message!r} is not inside a red alert: {alerts}",
            )
        self.assertNotIn("login__alert--success", response.content.decode())

    def solved_captcha(self):
        key = CaptchaStore.generate_key()
        return {
            "captcha_0": key,
            "captcha_1": CaptchaStore.objects.get(hashkey=key).response,
        }

    def test_sign_up(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "username": "new_user",
                "email": "not-an-email",
                "password1": "Correct-horse-battery-1",
                "password2": "Correct-horse-battery-1",
                **self.solved_captcha(),
            },
        )
        self.assert_field_error_shown_as_error(response, "email")

    def test_reset_password(self):
        response = self.client.post(
            reverse("account_reset_password"), {"email": "not-an-email"}
        )
        self.assert_field_error_shown_as_error(response, "email")

    def test_set_password(self):
        user = make_user("no_password")
        user.set_unusable_password()
        user.save()
        self.client.force_login(user)
        response = self.client.post(
            reverse("account_set_password"),
            {"password1": "Correct-horse-battery-1", "password2": "different-2"},
        )
        self.assert_field_error_shown_as_error(response, "password2")
