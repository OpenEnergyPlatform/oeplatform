"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

``manage.py check_catalogue``: is the component catalogue complete, and does it
render?

It fails when a house component (a partial in ``theming/scss/components/`` or an
include in ``base/templates/components/``) has no catalogue entry of the same
name, when an entry lacks its when-to-use note, when the token table and the
stylesheets disagree about which tokens exist, or when ``/styleguide/`` does not
answer 200 with every entry in either token mode.

It runs in the catalogue workflow (``.github/workflows/catalogue.yaml``), not in
``manage.py test``: it guards the catalogue, and a missing entry should show as
the catalogue's own failing status rather than as a broken test suite.
"""  # noqa: 501

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse

from base.styleguide import TOKEN_MODES, catalogue_problems, entry_files


def _host():
    """A host name this deployment's ALLOWED_HOSTS accepts."""
    for host in settings.ALLOWED_HOSTS:
        if host == "*":
            break
        if not host.startswith("."):
            return host
    return "localhost"


def rendering_problems():
    client = Client(HTTP_HOST=_host())
    names = entry_files()
    problems = []
    for mode in TOKEN_MODES:
        url = f"{reverse('base:styleguide')}?tokens={mode}"
        response = client.get(url)
        if response.status_code != 200:
            problems.append(f"{url} answers {response.status_code}, not 200")
            continue
        page = response.content.decode()
        for name in names:
            if f'data-entry="{name}"' not in page:
                problems.append(f"{url} does not render the entry {name}")
    return problems


class Command(BaseCommand):
    help = (
        "Fail when a house component has no catalogue entry, or when the "
        "catalogue does not render in either token mode."
    )

    def handle(self, *args, **options):
        problems = catalogue_problems() + rendering_problems()
        if problems:
            raise CommandError(
                "The component catalogue is incomplete:\n"
                + "\n".join(f"- {problem}" for problem in problems)
            )
        count = len(entry_files())
        self.stdout.write(
            self.style.SUCCESS(
                f"The component catalogue is complete: {count} "
                f"{'entry' if count == 1 else 'entries'}, rendered in both "
                "token modes."
            )
        )
