from django.core.management.base import BaseCommand
from django.db import transaction
from dataedit.models import PeerReview, PeerReviewManager
from oeplatform.securitysettings import ONTOLOGY_FOLDER


class Command(BaseCommand):
    help = 'Clears PeerReview and PeerReviewManager entries'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Delete all entries')

    def handle(self, *args, **options):
        """
        Clears PeerReview and PeerReviewManager entries based on provided options.

        If the --all option is provided, all entries in both tables will be deleted
        after confirmation from the user. If no option is provided, the user will be
        prompted to enter the ID of the entry to delete, and that specific entry will
        be deleted after confirmation.

        Usage:
        python manage.py clear_peer_reviews --all  # Delete all entries
        python manage.py clear_peer_reviews        # Delete a single entry by ID
        """

        delete_all = options['all']

        if delete_all:
            confirm = input('Are you sure you want to delete all entries? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('Aborted.')
                return

            with transaction.atomic():
                self.stdout.write('Deleting all entries...')
                PeerReview.objects.all().delete()
                PeerReviewManager.objects.all().delete()
                self.stdout.write('All entries deleted.')

        else:
            entry_id = input('Enter the ID of the entry to delete: ')
            try:
                entry_id = int(entry_id)
            except ValueError:
                self.stdout.write('Invalid entry ID.')
                return

            try:
                with transaction.atomic():
                    peer_review = PeerReview.objects.get(id=entry_id)
                    manager = PeerReviewManager.objects.get(opr_id=entry_id)

                    confirm = input(f'Are you sure you want to delete the entry with ID {entry_id}? (yes/no): ')
                    if confirm.lower() != 'yes':
                        self.stdout.write('Aborted.')
                        return

                    peer_review.delete()
                    manager.delete()

                    self.stdout.write(f'Entry with ID {entry_id} deleted.')

            except (PeerReview.DoesNotExist, PeerReviewManager.DoesNotExist):
                self.stdout.write(f'Entry with ID {entry_id} does not exist.')

        self.stdout.write(self.style.SUCCESS('Operation completed.'))
