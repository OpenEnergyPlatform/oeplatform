"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from termsandconditions.models import TermsAndConditions


class Command(BaseCommand):
    help = "Create default site terms and conditions if none are active yet."

    def handle(self, *args, **options):
        slug = getattr(settings, "DEFAULT_TERMS_SLUG", "site-terms")
        if TermsAndConditions.objects.filter(
            slug=slug, date_active__isnull=False
        ).exists():
            self.stdout.write(
                self.style.WARNING(f"Active terms for '{slug}' already exist. Skipping.")
            )
            return

        TermsAndConditions.objects.create(
            slug=slug,
            name="Open Energy Platform Terms and Conditions",
            version_number=1.0,
            text=(
                "<p>Welcome to the Open Energy Platform.</p>"
                "<p>By continuing to use this platform you agree to comply with "
                "applicable laws, respect data licenses, and use the service "
                "responsibly.</p>"
                "<p>Please replace this placeholder text with your official terms "
                "in the Django admin under <em>Terms and Conditions</em>.</p>"
            ),
            info="Initial platform terms and conditions.",
            date_active=timezone.now(),
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created default active terms for slug '{slug}'.")
        )
