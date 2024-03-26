from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Seed the database with topics"

    def handle(self, *args, **options):
        # Call the loaddata command to load the fixture
        call_command("loaddata", "dataedit/fixtures/topics.json")
        self.stdout.write(
            self.style.SUCCESS("Successfully seeded the database with topics")
        )
