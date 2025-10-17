"""
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from oeplatform.settings import DEFAULT_FROM_EMAIL, URL


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
