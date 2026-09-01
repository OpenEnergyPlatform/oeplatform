"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_GET

from login.account_linking import (
    LinkChallengeError,
    claim_legacy_email_for_user,
    complete_link_challenge,
    validate_claim_email,
)


@require_GET
def social_link_pending_view(request):
    return render(request, "login/social_link_pending.html")


@require_GET
def social_link_confirm_view(request, token: str):
    try:
        legacy = complete_link_challenge(token, request)
    except LinkChallengeError as exc:
        messages.error(request, str(exc))
        return render(
            request,
            "login/social_link_confirm_failed.html",
            {"error": str(exc)},
            status=400,
        )

    messages.success(
        request,
        "Your social login is now linked to your existing account. Welcome back.",
    )
    return redirect("login:profile", user_id=legacy.pk)


class ClaimLegacyAccountView(LoginRequiredMixin, View):
    template_name = "login/claim_legacy_account.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        raw_email = request.POST.get("legacy_email", "")
        try:
            email = validate_claim_email(raw_email)
            claim_legacy_email_for_user(request.user, email)
        except (ValidationError, LinkChallengeError) as exc:
            messages.error(request, str(exc))
            return render(
                request,
                self.template_name,
                {"legacy_email": raw_email},
                status=400,
            )

        messages.info(
            request,
            "We sent a confirmation link to the legacy account email. "
            "Open that message to finish linking.",
        )
        return redirect("login:social-link-pending")


claim_legacy_account_view = ClaimLegacyAccountView.as_view()
