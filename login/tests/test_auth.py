"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase

from login.models import myuser as User


class AuthTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            name="testuser",
            email="test123@mail.com",
            affiliation="Test",
        )

        self.user.set_password("password")
        self.user.save()
        # self.factory = RequestFactory()

        self.credentials = {"name": self.user.name, "password": "password"}
