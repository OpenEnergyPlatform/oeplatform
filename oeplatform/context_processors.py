"""
SPDX-FileCopyrightText: 2024 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.conf import settings


def allauth_settings(request):
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }


def external_urls(request):
    """Define hard coded external urls here.
    Use in templates like this: {{ EXTERNAL_URLS.<name_of_url> }}
    Also, you may want to add an icon indicating external links, e.g.
    """
    return {
        "EXTERNAL_URLS": settings.EXTERNAL_URLS,
        "CONTACT_ADDRESSES": settings.CONTACT_ADDRESSES,
    }
