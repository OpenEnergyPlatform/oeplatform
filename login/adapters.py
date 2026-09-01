"""
SPDX-FileCopyrightText: 2024 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from __future__ import annotations

import typing

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import redirect

from login.account_linking import (
    find_legacy_candidate,
    social_email,
    start_link_challenge_from_sociallogin,
)

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin

    from login.models import myuser as User


class AccountAdapter(DefaultAccountAdapter):
    """
    Handles default logins
    """

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return settings.ACCOUNT_ALLOW_REGISTRATION


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Handles logins via 3rd party organizations like ORCID / RegApp.
    """

    def is_open_for_signup(
        self, request: HttpRequest, sociallogin: SocialLogin
    ) -> bool:
        return settings.ACCOUNT_ALLOW_REGISTRATION

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populates user information from social provider info.

        See: https://django-allauth.readthedocs.io/en/latest/advanced.html?#creating-and-populating-user-instances # noqa
        """
        provider = sociallogin.account.provider

        # Specific modifications for the RegApp context data.
        # Provider name must be the same as in securitysettings.
        if provider == "RegApp":
            name = data.get(
                "name"
            )  # NOTE: Consider to add random user name if not available
            first_name = data.get("given_name")
            last_name = data.get("given_name")
            new_data = data
            new_data["username"] = name
            new_data["first_name"] = first_name
            new_data["last_name"] = last_name

        return super().populate_user(request, sociallogin, data)

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        """
        If the social email matches a legacy local account, require email
        confirmation to that legacy address before linking.
        """
        if sociallogin.is_existing:
            user = sociallogin.user
            if user is not None and not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
            return

        email = social_email(sociallogin)
        if not email:
            return

        legacy = find_legacy_candidate(email, provider=sociallogin.account.provider)
        if legacy is None:
            return

        start_link_challenge_from_sociallogin(sociallogin, legacy)
        raise ImmediateHttpResponse(redirect("login:social-link-pending"))
