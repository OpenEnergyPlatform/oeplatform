"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""

from __future__ import annotations

from dataclasses import dataclass, field

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rest_framework.authtoken.models import Token

from dataedit.models import PeerReview, ReviewRound, Table
from factsheet.models import OEKG_Modifications, ScenarioBundleAccessControl
from login.models import ActivationToken, GroupMembership, UserPermission, myuser
from modelview.models import BasicFactsheet


@dataclass
class TransferStats:
    table_permissions_merged: int = 0
    table_permissions_transferred: int = 0
    group_memberships_merged: int = 0
    group_memberships_transferred: int = 0
    bundle_access_transferred: int = 0
    bundle_access_deduplicated: int = 0
    peer_reviews_reviewer: int = 0
    peer_reviews_contributor: int = 0
    peer_reviews_skipped: int = 0
    review_rounds: int = 0
    oekg_modifications: int = 0
    table_metadata: int = 0
    factsheet_emails: int = 0
    activation_tokens_deleted: int = 0
    auth_tokens_deleted: int = 0
    warnings: list[str] = field(default_factory=list)

    def report(self, stdout, style) -> None:
        stdout.write(style.SUCCESS("\nTransfer summary:"))
        stdout.write(
            f"  Table permissions: {self.table_permissions_transferred} transferred, "
            f"{self.table_permissions_merged} merged"
        )
        stdout.write(
            f"  Group memberships: {self.group_memberships_transferred} transferred, "
            f"{self.group_memberships_merged} merged"
        )
        stdout.write(
            f"  Bundle access: {self.bundle_access_transferred} transferred, "
            f"{self.bundle_access_deduplicated} deduplicated"
        )
        stdout.write(
            f"  Peer reviews: {self.peer_reviews_reviewer} reviewer, "
            f"{self.peer_reviews_contributor} contributor, "
            f"{self.peer_reviews_skipped} skipped"
        )
        stdout.write(f"  Review rounds: {self.review_rounds}")
        stdout.write(f"  OEKG modifications: {self.oekg_modifications}")
        stdout.write(f"  Table metadata contributors: {self.table_metadata}")
        stdout.write(f"  Factsheet contact emails: {self.factsheet_emails}")
        stdout.write(
            f"  Cleanup: {self.activation_tokens_deleted} activation tokens, "
            f"{self.auth_tokens_deleted} API tokens deleted"
        )
        for warning in self.warnings:
            stdout.write(style.WARNING(f"  Warning: {warning}"))


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

        dry_run = options["dry_run"]
        rename_source = options["rename_source"]
        if rename_source and not options["deactivate_source"]:
            raise CommandError("--rename-source requires --deactivate-source.")

        self.stdout.write(
            f"Transferring data from {source.name} <{source.email}> "
            f"to {target.name} <{target.email}>"
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run only — no changes will be saved."))

        stats = TransferStats()

        with transaction.atomic():
            self._transfer_table_permissions(source, target, stats)
            self._transfer_group_memberships(source, target, stats)
            if not options["skip_bundles"]:
                self._transfer_bundle_access(source, target, stats)
            if not options["skip_peer_reviews"]:
                self._transfer_peer_reviews(source, target, stats)
                self._transfer_review_rounds(source, target, stats)
            self._transfer_oekg_modifications(source, target, stats)
            if not options["skip_metadata"]:
                self._transfer_table_metadata(source, target, stats)
                self._transfer_factsheet_emails(source, target, stats)
            self._cleanup_source_tokens(source, stats)
            if options["deactivate_source"]:
                self._deactivate_source(source, rename_source, stats)

            if dry_run:
                transaction.set_rollback(True)

        stats.report(self.stdout, self.style)
        if dry_run:
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

    @staticmethod
    def _transfer_table_permissions(
        source: myuser, target: myuser, stats: TransferStats
    ) -> None:
        for perm in UserPermission.objects.filter(holder=source).select_related("table"):
            existing = UserPermission.objects.filter(
                table=perm.table, holder=target
            ).first()
            if existing:
                if perm.level > existing.level:
                    existing.level = perm.level
                    existing.save(update_fields=["level"])
                perm.delete()
                stats.table_permissions_merged += 1
            else:
                perm.holder = target
                perm.save(update_fields=["holder"])
                stats.table_permissions_transferred += 1

    @staticmethod
    def _transfer_group_memberships(
        source: myuser, target: myuser, stats: TransferStats
    ) -> None:
        for membership in GroupMembership.objects.filter(user=source).select_related(
            "group"
        ):
            existing = GroupMembership.objects.filter(
                user=target, group=membership.group
            ).first()
            if existing:
                if membership.level > existing.level:
                    existing.level = membership.level
                    existing.save(update_fields=["level"])
                membership.delete()
                stats.group_memberships_merged += 1
            else:
                membership.user = target
                membership.save(update_fields=["user"])
                stats.group_memberships_transferred += 1

    @staticmethod
    def _transfer_bundle_access(
        source: myuser, target: myuser, stats: TransferStats
    ) -> None:
        for access in ScenarioBundleAccessControl.objects.filter(owner_user=source):
            if ScenarioBundleAccessControl.objects.filter(
                owner_user=target, bundle_id=access.bundle_id
            ).exists():
                access.delete()
                stats.bundle_access_deduplicated += 1
            else:
                access.owner_user = target
                access.save(update_fields=["owner_user"])
                stats.bundle_access_transferred += 1

    @staticmethod
    def _transfer_peer_reviews(
        source: myuser, target: myuser, stats: TransferStats
    ) -> None:
        for review in PeerReview.objects.filter(reviewer=source):
            other_role = review.contributor_id
            if other_role == target.pk:
                stats.peer_reviews_skipped += 1
                stats.warnings.append(
                    f"PeerReview {review.pk} ({review.table}): "
                    "reviewer transfer would equal contributor — skipped"
                )
                continue
            review.reviewer = target
            review.save(update_fields=["reviewer"])
            stats.peer_reviews_reviewer += 1

        for review in PeerReview.objects.filter(contributor=source):
            other_role = review.reviewer_id
            if other_role == target.pk:
                stats.peer_reviews_skipped += 1
                stats.warnings.append(
                    f"PeerReview {review.pk} ({review.table}): "
                    "contributor transfer would equal reviewer — skipped"
                )
                continue
            review.contributor = target
            review.save(update_fields=["contributor"])
            stats.peer_reviews_contributor += 1

    @staticmethod
    def _transfer_review_rounds(
        source: myuser, target: myuser, stats: TransferStats
    ) -> None:
        updated = ReviewRound.objects.filter(actor=source).update(actor=target)
        stats.review_rounds = updated

    @staticmethod
    def _transfer_oekg_modifications(
        source: myuser, target: myuser, stats: TransferStats
    ) -> None:
        updated = OEKG_Modifications.objects.filter(user=source).update(user=target)
        stats.oekg_modifications = updated

    def _transfer_table_metadata(
        self, source: myuser, target: myuser, stats: TransferStats
    ) -> None:
        source_emails = {source.email.lower()}
        source_names = {source.name.lower()}
        if source.fullname:
            source_names.add(source.fullname.lower())

        for table in Table.objects.exclude(oemetadata__isnull=True):
            metadata = table.oemetadata
            if not metadata:
                continue
            changed = self._update_contributors_in_metadata(
                metadata, source_emails, source_names, target
            )
            if changed:
                table.oemetadata = metadata
                table.save(update_fields=["oemetadata"])
                stats.table_metadata += 1

    @staticmethod
    def _update_contributors_in_metadata(
        metadata: dict,
        source_emails: set[str],
        source_names: set[str],
        target: myuser,
    ) -> bool:
        changed = False
        contributor_lists = []

        top_level = metadata.get("contributors")
        if isinstance(top_level, list):
            contributor_lists.append(top_level)

        for resource in metadata.get("resources") or []:
            if not isinstance(resource, dict):
                continue
            resource_contributors = resource.get("contributors")
            if isinstance(resource_contributors, list):
                contributor_lists.append(resource_contributors)

        display_name = target.fullname or target.name

        for contributors in contributor_lists:
            for contributor in contributors:
                if not isinstance(contributor, dict):
                    continue
                email = (contributor.get("email") or "").lower()
                name = (contributor.get("name") or contributor.get("title") or "").lower()
                if email not in source_emails and name not in source_names:
                    continue
                if contributor.get("email"):
                    contributor["email"] = target.email
                if "name" in contributor:
                    contributor["name"] = display_name
                if "title" in contributor:
                    contributor["title"] = display_name
                changed = True

        return changed

    @staticmethod
    def _transfer_factsheet_emails(
        source: myuser, target: myuser, stats: TransferStats
    ) -> None:
        source_email = source.email.lower()
        target_email = target.email.lower()

        for factsheet in BasicFactsheet.objects.all():
            emails = factsheet.contact_email or []
            updated_emails = []
            changed = False
            for email in emails:
                if email.lower() == source_email:
                    if target_email not in [e.lower() for e in updated_emails]:
                        updated_emails.append(target.email)
                    changed = True
                else:
                    updated_emails.append(email)
            if changed:
                factsheet.contact_email = updated_emails
                factsheet.save(update_fields=["contact_email"])
                stats.factsheet_emails += 1

    @staticmethod
    def _cleanup_source_tokens(source: myuser, stats: TransferStats) -> None:
        stats.activation_tokens_deleted = ActivationToken.objects.filter(
            user=source
        ).delete()[0]
        stats.auth_tokens_deleted = Token.objects.filter(user=source).delete()[0]

    def _deactivate_source(
        self, source: myuser, rename: bool, stats: TransferStats
    ) -> None:
        source.is_active = False
        update_fields = ["is_active"]

        if rename:
            source.name = f"{source.name}_merged_{source.pk}"
            source.email = f"{source.email}.merged.{source.pk}"
            update_fields.extend(["name", "email"])
            stats.warnings.append(
                f"Source user renamed to {source.name} <{source.email}>"
            )

        source.save(update_fields=update_fields)
