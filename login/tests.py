# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# from django.contrib.auth import authenticate, login, logout
from django.test import TestCase

from login.models import myuser as User


# @override_settings(
#     AUTHENTICATION_BACKENDS=[
#         "axes.backends.AxesBackend",  # Use Axes backend explicitly for testing
#         "django.contrib.auth.backends.ModelBackend",
#     ]
# )
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

    # def test_authenticate_valid_credentials(self):
    #     user = authenticate(
    #         request=self.factory.request, name="testuser", password="password"
    #     )
    #     self.assertIsNotNone(user)
    #     print(user.name)
    #     self.assertEqual(user.name, "testuser")

    # def test_authenticate_invalid_credentials(self):
    #     user = authenticate(name="testuser", password="wrongpassword")
    #     self.assertIsNone(user)

    # def test_authenticate_nonexistent_user(self):
    #     user = authenticate(name="nonexistent", password="password")
    #     self.assertIsNone(user)

    # def test_login_method(self):
    #     response = self.client.post("/user/login/", self.credentials, follow=True)

    #     self.assertEqual(response.context["user"].name, self.user.name)
    #     self.assertTrue(response.wsgi_request.user.is_authenticated)

    # def test_logout_method(self):
    #     request = self.client.post("/user/logout/", follow=True)

    #     self.assertFalse(request.context["user"].is_authenticated)

    # def test_login_view(self):
    #     response = self.client.post("/user/login/", self.credentials)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue(response.context["user"].is_authenticated)

    # def test_logout_view(self):

    #     response = self.client.post("/user/logout/", self.credentials, follow=True)
    #     self.assertFalse(response.context["user"].is_authenticated)
