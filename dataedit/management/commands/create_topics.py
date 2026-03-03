"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the database with topics"

    def handle(self, *args, **options):
        # Call the loaddata command to load the fixture
        call_command("loaddata", "dataedit/fixtures/topics.json")
        self.stdout.write(
            self.style.SUCCESS("Successfully seeded the database with topics")
        )
