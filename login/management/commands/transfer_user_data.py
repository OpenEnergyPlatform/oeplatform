"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from login.models import myuser
from login.user_transfer import transfer_user_ownership


class Command(BaseCommand):
    help = (
        "Transfer ownership and attribution data from one user to another. "
        "Use --dry-run to preview changes."
    )

    def add_arguments(self, parser):
        source_group = parser.add_argument_group("source user (required)")
        source_selector = source_group.add_mutually_exclusive_group(required=True)
        source_selector.add_argument("--source-id", type=int)
        source_selector.add_argument("--source-name", type=str)
        source_selector.add_argument("--source-email", type=str)

        target_group = parser.add_argument_group("target user (required)")
        target_selector = target_group.add_mutually_exclusive_group(required=True)
        target_selector.add_argument("--target-id", type=int)
        target_selector.add_argument("--target-name", type=str)
        target_selector.add_argument("--target-email", type=str)

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to the database.",
        )
        parser.add_argument(
            "--deactivate-source",
            action="store_true",
            help="Set is_active=False on the source user after transfer.",
        )
        parser.add_argument(
            "--rename-source",
            action="store_true",
            help=(
                "Rename source username/email to free unique constraints "
                "(only with --deactivate-source)."
            ),
        )
        parser.add_argument(
            "--skip-metadata",
            action="store_true",
            help="Skip table oemetadata contributor and factsheet email updates.",
        )
        parser.add_argument(
            "--skip-peer-reviews",
            action="store_true",
            help="Skip peer review and review round reassignment.",
        )
        parser.add_argument(
            "--skip-bundles",
            action="store_true",
            help="Skip scenario bundle ownership transfer.",
        )

    def handle(self, *args, **options):
        source = self._resolve_user(
            options["source_id"],
            options["source_name"],
            options["source_email"],
            label="source",
        )
        target = self._resolve_user(
            options["target_id"],
            options["target_name"],
            options["target_email"],
            label="target",
        )

        if source.pk == target.pk:
            raise CommandError("Source and target user must be different.")

        rename_source = options["rename_source"]
        if rename_source and not options["deactivate_source"]:
            raise CommandError("--rename-source requires --deactivate-source.")

        self.stdout.write(
            f"Transferring data from {source.name} <{source.email}> "
            f"to {target.name} <{target.email}>"
        )
        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING("Dry run only — no changes will be saved.")
            )

        try:
            stats = transfer_user_ownership(
                source,
                target,
                deactivate_source=options["deactivate_source"],
                rename_source=rename_source,
                skip_metadata=options["skip_metadata"],
                skip_peer_reviews=options["skip_peer_reviews"],
                skip_bundles=options["skip_bundles"],
                dry_run=options["dry_run"],
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        stats.report(self.stdout, self.style)
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run complete — no changes made."))
        else:
            self.stdout.write(self.style.SUCCESS("Transfer complete."))

    @staticmethod
    def _resolve_user(
        user_id: int | None,
        username: str | None,
        email: str | None,
        *,
        label: str,
    ) -> myuser:
        try:
            if user_id is not None:
                return myuser.objects.get(pk=user_id)
            if username:
                return myuser.objects.get(name=username)
            if email:
                return myuser.objects.get(email=email)
        except myuser.DoesNotExist as exc:
            raise CommandError(f"{label.title()} user not found: {exc}") from exc
        raise CommandError(f"No {label} user selector provided (should be unreachable).")
