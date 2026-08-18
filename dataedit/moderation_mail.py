"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from dataedit.models import ContentReport
from dataedit.moderation import (
    moderation_detail_url,
    recipient_emails,
    report_respond_url,
)

logger = logging.getLogger("oeplatform")


def _send(subject: str, template: str, context: dict, recipients: list[str]) -> None:
    if not recipients:
        return
    context = {**context, "site_name": settings.URL}
    try:
        html_content = render_to_string(template, context)
        send_mail(
            subject,
            strip_tags(html_content),
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
            html_message=html_content,
        )
    except Exception:
        logger.exception("Failed to send moderation mail: %s", subject)


def moderation_inbox() -> list[str]:
    addresses = getattr(settings, "CONTACT_ADDRESSES", {}) or {}
    return list(
        addresses.get("moderation")
        or addresses.get("other")
        or addresses.get("technical")
        or []
    )


def notify_new_report(report: ContentReport, uploaders) -> None:
    absolute_moderation = f"https://{settings.URL}{moderation_detail_url(report)}"
    absolute_respond = f"https://{settings.URL}{report_respond_url(report)}"
    ctx = {
        "report": report,
        "moderation_url": absolute_moderation,
        "respond_url": absolute_respond,
    }
    _send(
        subject=f"[OEP moderation] {report.tracking_id}: {report.subject}",
        template="mails/moderation_new_report.html",
        context=ctx,
        recipients=moderation_inbox(),
    )
    _send(
        subject=(
            f"[OEP] Dataset temporarily blocked ({report.tracking_id}): "
            f"{report.table_name}"
        ),
        template="mails/moderation_uploader_blocked.html",
        context=ctx,
        recipients=recipient_emails(uploaders),
    )
    if report.reporter and report.reporter.email:
        _send(
            subject=f"[OEP] Report received ({report.tracking_id}): {report.table_name}",
            template="mails/moderation_report_received.html",
            context=ctx,
            recipients=[report.reporter.email],
        )


def notify_uploader_responded(report: ContentReport) -> None:
    absolute_moderation = f"https://{settings.URL}{moderation_detail_url(report)}"
    _send(
        subject=(
            f"[OEP moderation] Uploader response ({report.tracking_id}): "
            f"{report.table_name}"
        ),
        template="mails/moderation_uploader_responded.html",
        context={"report": report, "moderation_url": absolute_moderation},
        recipients=moderation_inbox(),
    )


def notify_resolved_dismissed(report: ContentReport, uploaders) -> None:
    recipients = recipient_emails(uploaders)
    if report.reporter and report.reporter.email:
        recipients.append(report.reporter.email)
    _send(
        subject=(
            f"[OEP] Report closed (no violation, {report.tracking_id}): "
            f"{report.table_name}"
        ),
        template="mails/moderation_resolved_dismissed.html",
        context={"report": report},
        recipients=list(dict.fromkeys(recipients)),
    )


def notify_resolved_violation(
    report: ContentReport, uploaders, deactivated_users
) -> None:
    deactivated_ids = {u.pk for u in deactivated_users}
    for uploader in uploaders:
        if uploader.pk in deactivated_ids:
            template = "mails/moderation_account_deactivated.html"
            subject = (
                f"[OEP] Account deactivated after repeated content violation "
                f"({report.tracking_id})"
            )
        else:
            template = "mails/moderation_violation_warning.html"
            subject = (
                f"[OEP] Content violation warning ({report.tracking_id}): "
                f"{report.table_name}"
            )
        if uploader.email:
            _send(
                subject=subject,
                template=template,
                context={"report": report, "user": uploader},
                recipients=[uploader.email],
            )
    if report.reporter and report.reporter.email:
        _send(
            subject=(
                f"[OEP] Report resolved (violation, {report.tracking_id}): "
                f"{report.table_name}"
            ),
            template="mails/moderation_resolved_violation_reporter.html",
            context={"report": report},
            recipients=[report.reporter.email],
        )
