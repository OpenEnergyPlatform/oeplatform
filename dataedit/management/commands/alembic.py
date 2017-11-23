from django.core.management.base import BaseCommand, CommandError
from alembic.config import main

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('commands', nargs='+')

    def handle(self, *args, **options):
        main(argv=options['commands'])