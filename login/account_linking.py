"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""

from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from typing import TYPE_CHECKING

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from login.mail import send_social_account_link_mail
from login.models import SocialAccountLinkToken, myuser
from login.user_transfer import transfer_user_ownership

if TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin

logger = logging.getLogger("oeplatform")


class LinkChallengeError(Exception):
    """Raised when a social→legacy link challenge cannot proceed."""


def link_token_lifetime() -> timedelta:
    hours = getattr(settings, "SOCIAL_ACCOUNT_LINK_TOKEN_HOURS", 48)
    return timedelta(hours=hours)


def social_email(sociallogin: SocialLogin) -> str | None:
    for address in sociallogin.email_addresses:
        if address.email:
            return address.email.strip().lower()
    email = (getattr(sociallogin.user, "email", None) or "").strip().lower()
    return email or None


def find_legacy_candidate(email: str, *, provider: str) -> myuser | None:
    """Return a local user that can be claimed for this social provider."""
    email = (email or "").strip()
    if not email:
        return None
    try:
        user = myuser.objects.get(email__iexact=email)
    except myuser.DoesNotExist:
        return None
    if SocialAccount.objects.filter(user=user, provider=provider).exists():
        return None
    return user


def _new_token_value() -> str:
    return secrets.token_urlsafe(32)


def _invalidate_pending(provider: str, uid: str) -> None:
    SocialAccountLinkToken.objects.filter(
        provider=provider,
        uid=uid,
        used_at__isnull=True,
    ).delete()


def start_link_challenge_from_sociallogin(
    sociallogin: SocialLogin,
    legacy_user: myuser,
) -> SocialAccountLinkToken:
    """Store pending social login and email a confirmation link to the legacy address."""
    provider = sociallogin.account.provider
    uid = sociallogin.account.uid
    _invalidate_pending(provider, uid)

    link = SocialAccountLinkToken.objects.create(
        token=_new_token_value(),
        legacy_user=legacy_user,
        provider=provider,
        uid=uid,
        sociallogin_data={
            "provider": provider,
            "uid": uid,
            "extra_data": dict(sociallogin.account.extra_data or {}),
            "email": social_email(sociallogin),
        },
        throwaway_user=None,
        expires_at=timezone.now() + link_token_lifetime(),
    )
    send_social_account_link_mail(legacy_user.email, link.token, legacy_user.name)
    logger.info(
        "Started social link challenge provider=%s uid=%s legacy_user=%s",
        provider,
        uid,
        legacy_user.pk,
    )
    return link


def start_link_challenge_from_throwaway(
    throwaway_user: myuser,
    legacy_user: myuser,
    *,
    provider: str,
    uid: str,
) -> SocialAccountLinkToken:
    """Email-challenge linking when the social account already sits on a new user."""
    if throwaway_user.pk == legacy_user.pk:
        raise LinkChallengeError("Cannot link an account to itself.")
    if not SocialAccount.objects.filter(
        user=throwaway_user, provider=provider, uid=uid
    ).exists():
        raise LinkChallengeError("Social account not found on the current user.")
    if SocialAccount.objects.filter(user=legacy_user, provider=provider).exists():
        raise LinkChallengeError(
            "The legacy account already has this social provider linked."
        )

    _invalidate_pending(provider, uid)
    link = SocialAccountLinkToken.objects.create(
        token=_new_token_value(),
        legacy_user=legacy_user,
        provider=provider,
        uid=uid,
        sociallogin_data=None,
        throwaway_user=throwaway_user,
        expires_at=timezone.now() + link_token_lifetime(),
    )
    send_social_account_link_mail(legacy_user.email, link.token, legacy_user.name)
    logger.info(
        "Started claim link challenge provider=%s uid=%s throwaway=%s legacy=%s",
        provider,
        uid,
        throwaway_user.pk,
        legacy_user.pk,
    )
    return link


def get_valid_link_token(token: str) -> SocialAccountLinkToken:
    try:
        link = SocialAccountLinkToken.objects.select_related(
            "legacy_user", "throwaway_user"
        ).get(token=token)
    except SocialAccountLinkToken.DoesNotExist as exc:
        raise LinkChallengeError("Invalid or unknown confirmation link.") from exc
    if link.used_at is not None:
        raise LinkChallengeError("This confirmation link has already been used.")
    if link.expires_at <= timezone.now():
        raise LinkChallengeError("This confirmation link has expired.")
    return link


def complete_link_challenge(token: str, request) -> myuser:
    """Confirm ownership, attach social account to legacy user, and activate them."""
    link = get_valid_link_token(token)
    legacy = link.legacy_user

    with transaction.atomic():
        if link.throwaway_user_id:
            throwaway = link.throwaway_user
            if throwaway is None:
                raise LinkChallengeError("The temporary social account no longer exists.")
            social_account = SocialAccount.objects.select_for_update().get(
                user=throwaway,
                provider=link.provider,
                uid=link.uid,
            )
            transfer_user_ownership(
                throwaway,
                legacy,
                deactivate_source=True,
                rename_source=True,
            )
            social_account.user = legacy
            social_account.save(update_fields=["user"])
        elif link.sociallogin_data:
            _attach_social_account_from_pending(link, legacy)
        else:
            raise LinkChallengeError("Link challenge is missing social account data.")

        legacy.is_active = True
        legacy.is_native = False
        legacy.save(update_fields=["is_active", "is_native"])

        link.used_at = timezone.now()
        link.save(update_fields=["used_at"])

    login(
        request,
        legacy,
        backend="allauth.account.auth_backends.AuthenticationBackend",
    )
    return legacy


def _attach_social_account_from_pending(
    link: SocialAccountLinkToken, legacy: myuser
) -> SocialAccount:
    data = link.sociallogin_data or {}
    extra_data = data.get("extra_data") or {}
    account, created = SocialAccount.objects.get_or_create(
        provider=link.provider,
        uid=link.uid,
        defaults={"user": legacy, "extra_data": extra_data},
    )
    if not created:
        account.user = legacy
        if extra_data:
            account.extra_data = extra_data
        account.save(update_fields=["user", "extra_data"])
    return account


def claim_legacy_email_for_user(user: myuser, legacy_email: str) -> SocialAccountLinkToken:
    """Start a challenge for an authenticated social user claiming a legacy inbox."""
    social_accounts = list(SocialAccount.objects.filter(user=user))
    if not social_accounts:
        raise LinkChallengeError(
            "Your account has no linked social login to transfer."
        )
    if len(social_accounts) != 1:
        # Prefer a deterministic provider; take the first stable by provider name.
        social_accounts.sort(key=lambda sa: (sa.provider, sa.uid))
    social = social_accounts[0]

    legacy = find_legacy_candidate(legacy_email, provider=social.provider)
    if legacy is None:
        raise LinkChallengeError(
            "No claimable legacy account found for that email address."
        )
    if legacy.pk == user.pk:
        raise LinkChallengeError("That email already belongs to your current account.")

    return start_link_challenge_from_throwaway(
        user,
        legacy,
        provider=social.provider,
        uid=social.uid,
    )


def validate_claim_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise ValidationError("Enter a valid email address.")
    return email
