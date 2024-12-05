from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin

    from login.models import myuser as User


class AccountAdapter(DefaultAccountAdapter):
    """
    Handles default logins
    """

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Handles logins via 3rd party organizations like ORCID.
    """

    def is_open_for_signup(
        self, request: HttpRequest, sociallogin: SocialLogin
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

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
