"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""

from __future__ import annotations

from dataclasses import dataclass, field

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


def transfer_user_ownership(
    source: myuser,
    target: myuser,
    *,
    deactivate_source: bool = False,
    rename_source: bool = False,
    skip_metadata: bool = False,
    skip_peer_reviews: bool = False,
    skip_bundles: bool = False,
    dry_run: bool = False,
) -> TransferStats:
    """Move ownership/attribution data from source user to target user."""
    if source.pk == target.pk:
        raise ValueError("Source and target user must be different.")
    if rename_source and not deactivate_source:
        raise ValueError("rename_source requires deactivate_source.")

    stats = TransferStats()

    with transaction.atomic():
        _transfer_table_permissions(source, target, stats)
        _transfer_group_memberships(source, target, stats)
        if not skip_bundles:
            _transfer_bundle_access(source, target, stats)
        if not skip_peer_reviews:
            _transfer_peer_reviews(source, target, stats)
            _transfer_review_rounds(source, target, stats)
        _transfer_oekg_modifications(source, target, stats)
        if not skip_metadata:
            _transfer_table_metadata(source, target, stats)
            _transfer_factsheet_emails(source, target, stats)
        _cleanup_source_tokens(source, stats)
        if deactivate_source:
            _deactivate_source(source, rename_source, stats)

        if dry_run:
            transaction.set_rollback(True)

    return stats


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


def _transfer_peer_reviews(
    source: myuser, target: myuser, stats: TransferStats
) -> None:
    for review in PeerReview.objects.filter(reviewer=source):
        if review.contributor_id == target.pk:
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
        if review.reviewer_id == target.pk:
            stats.peer_reviews_skipped += 1
            stats.warnings.append(
                f"PeerReview {review.pk} ({review.table}): "
                "contributor transfer would equal reviewer — skipped"
            )
            continue
        review.contributor = target
        review.save(update_fields=["contributor"])
        stats.peer_reviews_contributor += 1


def _transfer_review_rounds(
    source: myuser, target: myuser, stats: TransferStats
) -> None:
    stats.review_rounds = ReviewRound.objects.filter(actor=source).update(actor=target)


def _transfer_oekg_modifications(
    source: myuser, target: myuser, stats: TransferStats
) -> None:
    stats.oekg_modifications = OEKG_Modifications.objects.filter(user=source).update(
        user=target
    )


def _transfer_table_metadata(
    source: myuser, target: myuser, stats: TransferStats
) -> None:
    source_emails = {source.email.lower()}
    source_names = {source.name.lower()}
    if source.fullname:
        source_names.add(source.fullname.lower())

    for table in Table.objects.exclude(oemetadata__isnull=True):
        metadata = table.oemetadata
        if not metadata:
            continue
        changed = _update_contributors_in_metadata(
            metadata, source_emails, source_names, target
        )
        if changed:
            table.oemetadata = metadata
            table.save(update_fields=["oemetadata"])
            stats.table_metadata += 1


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


def _cleanup_source_tokens(source: myuser, stats: TransferStats) -> None:
    stats.activation_tokens_deleted = ActivationToken.objects.filter(
        user=source
    ).delete()[0]
    stats.auth_tokens_deleted = Token.objects.filter(user=source).delete()[0]


def _deactivate_source(source: myuser, rename: bool, stats: TransferStats) -> None:
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
