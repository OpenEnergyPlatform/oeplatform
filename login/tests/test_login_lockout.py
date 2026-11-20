"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from allauth.account.models import EmailAddress
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from login.models import myuser as User

PASSWORD = "a-long-test-password"
NEW_PASSWORD = "another-long-test-password"
RESET_LINK = re.compile(r"https?://[^/\s]+(/accounts/password/reset/key/\S+)")


@override_settings(AXES_ENABLED=True, AXES_FAILURE_LIMIT=5)
class LoginLockoutTest(TestCase):
    def setUp(self):
        cache.clear()  # allauth's login rate limit lives in the cache
        self.user = User.objects.create_user(
            name="owner", email="owner@example.org", affiliation="Test"
        )
        self.user.set_password(PASSWORD)
        self.user.save()
        EmailAddress.objects.create(
            user=self.user, email="owner@example.org", verified=True, primary=True
        )

    def log_in(self, login, password):
        return self.client.post(
            reverse("account_login"), {"login": login, "password": password}
        )

    def lock_out(self, login):
        for _ in range(5):
            response = self.log_in(login, "wrong-password")
        return response

    def reset_password(self):
        self.client.post(
            reverse("account_reset_password"), {"email": "owner@example.org"}
        )
        path = RESET_LINK.search(mail.outbox[-1].body).group(1)
        form = self.client.get(path, follow=True).redirect_chain[-1][0]
        response = self.client.post(
            form, {"password1": NEW_PASSWORD, "password2": NEW_PASSWORD}
        )
        self.assertEqual(response.status_code, 302)

    def test_a_lockout_explains_itself_and_offers_the_reset(self):
        response = self.lock_out("owner")

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "account/lockout.html")
        self.assertContains(
            response, reverse("account_reset_password"), status_code=403
        )

    def test_the_right_password_stays_locked_without_a_reset(self):
        self.lock_out("owner")

        self.log_in("owner", PASSWORD)

        self.assertNotIn("_auth_user_id", self.client.session)

    def test_a_password_reset_lifts_the_lockout(self):
        self.lock_out("owner")

        self.reset_password()

        self.assertEqual(self.log_in("owner", NEW_PASSWORD).status_code, 302)

    def test_a_lockout_on_the_email_is_lifted_too(self):
        self.lock_out("owner@example.org")

        self.reset_password()

        self.assertEqual(
            self.log_in("owner@example.org", NEW_PASSWORD).status_code, 302
        )
