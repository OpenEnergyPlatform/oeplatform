"""
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from oeplatform.settings import DEFAULT_FROM_EMAIL, URL

logger = logging.getLogger("oeplatform")


def send_verification_mail(recipient, token):
    veri_url = "https://{host}/user/activate/{token}".format(host=URL, token=token)
    html_content = render_to_string(
        "mails/verification_mail.html", {"url": veri_url, "site_name": URL}
    )
    send_mail(
        "OEP account - E-Mail validation",
        strip_tags(html_content),
        DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
        html_message=html_content,
    )


def send_social_account_link_mail(recipient: str, token: str, username: str) -> None:
    confirm_path = reverse("login:social-link-confirm", kwargs={"token": token})
    confirm_url = f"https://{URL}{confirm_path}"
    html_content = render_to_string(
        "mails/social_account_link_mail.html",
        {
            "url": confirm_url,
            "site_name": URL,
            "username": username,
        },
    )
    try:
        send_mail(
            "OEP account - Confirm social login link",
            strip_tags(html_content),
            DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
            html_message=html_content,
        )
    except Exception:
        logger.exception("Failed to send social account link mail to %s", recipient)
        raise
