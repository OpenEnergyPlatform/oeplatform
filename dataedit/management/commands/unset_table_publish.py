# SPDX-FileCopyrightText: 2023 Jonas Huber <jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2024 Christian Winger <c.winger>
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT


from django.core.management.base import BaseCommand
from django.db import transaction

from dataedit.models import Table


class Command(BaseCommand):
    help = "Sets is_publish to False for Table entries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all", action="store_true", help="Set is_publish to False for all entries"
        )

    def handle(self, *args, **options):
        """
        Sets is_publish to False for Table entries based on provided options.

        If the --all option is provided, is_publish will be set to False for all entries
        after confirmation from the user. If no option is provided, the user will be
        prompted to enter the ID of the entry to update, and that specific entry's
        is_publish field will be set to False after confirmation.

        Usage:
        python manage.py unset_table_publish --all
            # Set is_publish to False for all entries
        python manage.py unset_table_publish
            # Set is_publish to False for a single entry by ID
        """

        set_all = options["all"]

        if set_all:
            confirm = input(
                "Are you sure you want to set is_publish to False for all entries? "
                "(yes/no): "
            )
            if confirm.lower() != "yes":
                self.stdout.write("Aborted.")
                return

            with transaction.atomic():
                self.stdout.write("Setting is_publish to False for all entries...")
                Table.objects.all().update(is_publish=False)
                self.stdout.write("All entries updated.")

        else:
            entry_id = input("Enter the ID of the entry to update: ")
            try:
                entry_id = int(entry_id)
            except ValueError:
                self.stdout.write("Invalid entry ID.")
                return

            try:
                with transaction.atomic():
                    table = Table.objects.get(id=entry_id)
                    confirm = input(
                        f"Are you sure you want to set is_publish to False for the "
                        f"entry with ID {entry_id}? (yes/no): "
                    )
                    if confirm.lower() != "yes":
                        self.stdout.write("Aborted.")
                        return

                    table.is_publish = False
                    table.save()
                    self.stdout.write(
                        f"is_publish set to False for entry with ID {entry_id}."
                    )

            except Table.DoesNotExist:
                self.stdout.write(f"Entry with ID {entry_id} does not exist.")

        self.stdout.write(self.style.SUCCESS("Operation completed."))
