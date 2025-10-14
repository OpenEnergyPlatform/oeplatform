# SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.core.management.base import BaseCommand
from django.db import transaction

from dataedit.models import PeerReview, PeerReviewManager, Table


class Command(BaseCommand):
    help = "Clears PeerReview and PeerReviewManager entries"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Delete all entries")

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

        delete_all = options["all"]

        if delete_all:
            confirm = input("Are you sure you want to delete all entries? (yes/no): ")
            if confirm.lower() != "yes":
                self.stdout.write("Aborted.")
                return

            with transaction.atomic():
                self.stdout.write("Deleting all entries...")
                PeerReview.objects.all().delete()
                PeerReviewManager.objects.all().delete()
                self.stdout.write("All entries deleted.")

            try:
                # Update all rows to set is_reviewed to False
                Table.objects.update(is_reviewed=False)

                self.stdout.write(
                    self.style.SUCCESS("Successfully reset is_reviewed for all rows!")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))

        else:
            entry_id = input("Enter the ID of the entry to delete: ")
            try:
                entry_id = int(entry_id)
            except ValueError:
                self.stdout.write("Invalid entry ID.")
                return

            try:
                with transaction.atomic():
                    peer_review = PeerReview.objects.get(id=entry_id)
                    manager = PeerReviewManager.objects.get(opr_id=entry_id)

                    confirm = input(
                        "Are you sure you want to delete the entry with "
                        f"ID {entry_id}? (yes/no): "
                    )
                    if confirm.lower() != "yes":
                        self.stdout.write("Aborted.")
                        return

                    peer_review.delete()
                    manager.delete()

                    self.stdout.write(f"Entry with ID {entry_id} deleted.")

            except (PeerReview.DoesNotExist, PeerReviewManager.DoesNotExist):
                self.stdout.write(f"Entry with ID {entry_id} does not exist.")

            peer_review = PeerReview.objects.get(id=entry_id)
            table_id = Table.load(
                schema_name=peer_review.schema, table_name=peer_review.table
            )

            try:
                # Update the specific row by ID to set is_reviewed to False
                table = Table.objects.get(id=table_id)
                table.is_reviewed = False
                table.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully updated is_reviewed for table ID {table_id}"
                    )
                )
            except Table.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Table with ID {table_id} does not exist")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("Operation completed."))
