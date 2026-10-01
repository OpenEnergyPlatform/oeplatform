"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Small helpers shared by the profile and organization access tests.

``base.tests.TestViewsTestCase`` is not used for these: it creates one fixed
user in ``setUpClass``, while every access test needs several users in
distinct roles (owner, stranger, admin, members at each level).
"""  # noqa: 501

from login.models import myuser

HTMX = {"HTTP_HX_REQUEST": "true"}


def make_user(name, **extra):
    user, _ = myuser.objects.get_or_create(
        name=name,
        email=f"{name.lower()}@test.com",
        did_agree=True,
        is_mail_verified=True,
        **extra,
    )
    return user


def act_as(client, user):
    """Log the test client in as ``user``, or leave it anonymous for None."""
    client.logout()
    if user is not None:
        client.force_login(user)
