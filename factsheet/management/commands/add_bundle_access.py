# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 Christian Winger <Christian Winger@oeko.de>
#
# SPDX-License-Identifier: MIT

from django.core.management.base import BaseCommand

from factsheet.models import ScenarioBundleAccessControl
from login.models import myuser


class Command(BaseCommand):
    help = "Manually add a user to ScenarioBundleAccessControl model"

    def add_arguments(self, parser):
        # Add arguments for the command
        parser.add_argument("--username", type=str, help="Username of the user")
        parser.add_argument(
            "--bundle_id",
            type=str,
            help="Bundle UID like cc0b8298-9e18-9528-c894-0a62e0f19ff3",
        )

    def handle(self, *args, **kwargs):
        username = kwargs["username"]
        bundle_id = kwargs["bundle_id"]

        try:
            user = myuser.objects.get(name=username)
        except myuser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with username '{username}' does not exist")
            )
            return

        # Check if the entry already exists
        if ScenarioBundleAccessControl.objects.filter(
            owner_user=user, bundle_id=bundle_id
        ).exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Entry already exists for user '{username}' "
                    f"with bundle ID '{bundle_id}'"
                )
            )
            return

        # Create the entry
        access_control = ScenarioBundleAccessControl(
            owner_user=user, bundle_id=bundle_id
        )
        access_control.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"User '{username}' added to ScenarioBundleAccessControl "
                f"with bundle ID '{bundle_id}'"
            )
        )
