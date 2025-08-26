# SPDX-FileCopyrightText: 2024 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut  # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.conf import settings


def allauth_settings(request):
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }
