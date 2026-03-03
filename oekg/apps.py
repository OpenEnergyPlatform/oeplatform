"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.apps import AppConfig


class SparqlQueryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "oekg"
