"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""

from allauth.socialaccount.models import SocialAccount
from django.core.management.base import BaseCommand

from login.models import myuser


class Command(BaseCommand):
    help = (
        "Set is_active=False for users who signed up via normal login "
        "(username/password), identified by having no linked social account."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List affected users without changing the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        user_ids_with_social = SocialAccount.objects.values_list("user_id", flat=True)
        users = myuser.objects.filter(is_active=True).exclude(
            pk__in=user_ids_with_social
        )

        user_list = list(users.order_by("name"))
        if not user_list:
            self.stdout.write(self.style.SUCCESS("No matching active users found."))
            return

        self.stdout.write(
            f"Found {len(user_list)} active user(s) to deactivate (no social account):"
        )
        for user in user_list:
            self.stdout.write(f"  - {user.name} <{user.email}>")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run only — no changes made."))
            return

        updated = myuser.objects.filter(pk__in=[user.pk for user in user_list]).update(
            is_active=False
        )
        self.stdout.write(self.style.SUCCESS(f"Deactivated {updated} user(s)."))
