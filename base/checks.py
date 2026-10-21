"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

System checks for the instance theming contract (#2637).

A stylesheet in ``INSTANCE_STYLESHEETS`` that no finder has is linked from every
page, and with ``DEBUG`` off the static storage refuses its name, so every page
fails. Said at start-up, and by ``collectstatic``, rather than by the first
visitor.
"""  # noqa: 501

import os

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.checks import Error, Tags, Warning, register


@register(Tags.staticfiles)
def check_instance_stylesheets(app_configs, **kwargs):
    return [
        Error(
            f"INSTANCE_STYLESHEETS names {path!r}, which no static files finder has.",
            hint=(
                "Put the file in a directory of STATICFILES_DIRS, or correct the "
                "path: it is a static path, as {% static %} takes it."
            ),
            id="base.E001",
        )
        for path in settings.INSTANCE_STYLESHEETS
        if not finders.find(path)
    ]


@register(Tags.templates)
def check_instance_template_dirs(app_configs, **kwargs):
    return [
        Warning(
            f"INSTANCE_TEMPLATE_DIRS names {directory!r}, which is not a directory.",
            hint="No template in it can replace the platform's.",
            id="base.W001",
        )
        for directory in settings.INSTANCE_TEMPLATE_DIRS
        if not os.path.isdir(directory)
    ]
