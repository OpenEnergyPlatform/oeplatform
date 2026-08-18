"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import Iterable

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from dataedit.models import ContentReport, ModerationHold, Table, UserModerationWarning
from login.models import UserPermission, myuser
from login.permissions import ADMIN_PERM


def get_table_uploaders(table: Table) -> list[myuser]:
    holders = (
        UserPermission.objects.filter(table=table, level__gte=ADMIN_PERM)
        .select_related("holder")
        .order_by("holder_id")
    )
    seen: set[int] = set()
    uploaders: list[myuser] = []
    for perm in holders:
        if perm.holder_id in seen:
            continue
        seen.add(perm.holder_id)
        uploaders.append(perm.holder)
    return uploaders


def is_moderation_blocked(table: Table) -> bool:
    return ModerationHold.objects.filter(table=table).exists()


def apply_moderation_hold(
    table: Table, report: ContentReport, created_by: myuser | None
) -> ModerationHold:
    was_published = bool(table.is_publish)
    hold, _created = ModerationHold.objects.update_or_create(
        table=table,
        defaults={
            "report": report,
            "created_by": created_by,
            "created": timezone.now(),
            "was_published": was_published,
        },
    )
    if table.is_publish:
        table.set_not_published()
    return hold


def clear_moderation_hold(table: Table | None, restore_publish: bool = False) -> None:
    if not table:
        return
    hold = ModerationHold.objects.filter(table=table).first()
    if not hold:
        return
    should_restore = restore_publish and hold.was_published
    hold.delete()
    if should_restore and not table.is_publish:
        table.is_publish = True
        table.save(update_fields=["is_publish"])


def create_content_report(
    *,
    table: Table,
    reporter: myuser,
    subject: str,
    reason: str,
    message: str,
) -> ContentReport:
    with transaction.atomic():
        report = ContentReport.objects.create(
            table=table,
            table_name=table.name,
            reporter=reporter,
            subject=subject,
            reason=reason,
            message=message,
            status=ContentReport.STATUS_AWAITING_UPLOADER,
        )
        apply_moderation_hold(table, report, created_by=reporter)
    return report


def record_uploader_response(report: ContentReport, response_text: str) -> ContentReport:
    report.uploader_response = response_text.strip()
    report.uploader_responded_at = timezone.now()
    report.status = ContentReport.STATUS_UNDER_REVIEW
    report.updated = timezone.now()
    report.save(
        update_fields=[
            "uploader_response",
            "uploader_responded_at",
            "status",
            "updated",
        ]
    )
    return report


def resolve_no_violation(
    report: ContentReport, staff: myuser, note: str = ""
) -> ContentReport:
    with transaction.atomic():
        clear_moderation_hold(report.table, restore_publish=True)
        report.status = ContentReport.STATUS_DISMISSED
        report.resolved_by = staff
        report.resolution_note = note.strip()
        report.updated = timezone.now()
        report.save(
            update_fields=["status", "resolved_by", "resolution_note", "updated"]
        )
    return report


def resolve_violation(
    report: ContentReport, staff: myuser, note: str = ""
) -> tuple[ContentReport, list[myuser]]:
    deactivated: list[myuser] = []
    with transaction.atomic():
        table = report.table
        uploaders: list[myuser] = []
        if table is not None:
            uploaders = get_table_uploaders(table)
            clear_moderation_hold(table)
            table.delete()
            report.table = None

        for uploader in uploaders:
            prior_count = UserModerationWarning.objects.filter(user=uploader).count()
            UserModerationWarning.objects.create(
                user=uploader,
                report=report,
                note=note.strip() or f"Violation for dataset {report.table_name}",
                created_by=staff,
            )
            if prior_count >= 1 and uploader.is_active:
                uploader.is_active = False
                uploader.save(update_fields=["is_active"])
                deactivated.append(uploader)

        report.status = ContentReport.STATUS_VIOLATION
        report.resolved_by = staff
        report.resolution_note = note.strip()
        report.updated = timezone.now()
        report.save(
            update_fields=[
                "table",
                "status",
                "resolved_by",
                "resolution_note",
                "updated",
            ]
        )
    return report, deactivated


def open_reports_queryset():
    return ContentReport.objects.filter(
        status__in=ContentReport.OPEN_STATUSES
    ).select_related("table", "reporter")


def moderation_detail_url(report: ContentReport) -> str:
    return reverse("dataedit:moderation-detail", kwargs={"report_id": report.pk})


def report_respond_url(report: ContentReport) -> str:
    return reverse(
        "dataedit:report-respond",
        kwargs={"table": report.table_name, "report_id": report.pk},
    )


def recipient_emails(users: Iterable[myuser]) -> list[str]:
    return [u.email for u in users if u and u.email and u.is_active]
