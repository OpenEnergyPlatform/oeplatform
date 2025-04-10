# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

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
