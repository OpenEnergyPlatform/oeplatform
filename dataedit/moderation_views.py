"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from api.utils import table_or_404
from dataedit.forms import ContentReportForm, ModerationResolveForm, UploaderResponseForm
from dataedit.models import ContentReport
from dataedit.moderation import (
    create_content_report,
    get_table_uploaders,
    open_reports_queryset,
    record_uploader_response,
    resolve_no_violation,
    resolve_violation,
)
from dataedit.moderation_mail import (
    notify_new_report,
    notify_resolved_dismissed,
    notify_resolved_violation,
    notify_uploader_responded,
)


DEFAULT_REPORT_MESSAGE = (
    "I believe the following dataset may contain content that violates "
    "the Open Energy Platform terms of use.\n\n"
    "Please describe the issue below:\n"
    "- What content is problematic?\n"
    "- Why do you believe it is illegal or otherwise prohibited?\n"
    "- Any additional context for moderators:\n"
)


class PlatformAdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not getattr(request.user, "is_admin", False):
            raise PermissionDenied("Platform administrator access required.")
        return super().dispatch(request, *args, **kwargs)


class TableReportView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, table: str) -> HttpResponse:
        table_obj = table_or_404(table=table)
        form = ContentReportForm(
            initial={
                "subject": f"Report dataset: {table_obj.name} (id={table_obj.pk})",
                "reason": ContentReport.REASON_ILLEGAL,
                "message": DEFAULT_REPORT_MESSAGE,
            }
        )
        return render(
            request,
            "dataedit/report_content.html",
            {"form": form, "table": table_obj, "success": False},
        )

    def post(self, request: HttpRequest, table: str) -> HttpResponse:
        table_obj = table_or_404(table=table)
        form = ContentReportForm(data=request.POST)
        if not form.is_valid():
            return render(
                request,
                "dataedit/report_content.html",
                {"form": form, "table": table_obj, "success": False},
            )

        existing = ContentReport.objects.filter(
            table=table_obj,
            reporter=request.user,
            status__in=ContentReport.OPEN_STATUSES,
        ).exists()
        if existing:
            messages.warning(
                request,
                "You already have an open report for this dataset.",
            )
            return redirect("dataedit:view", table=table_obj.name)

        report = create_content_report(
            table=table_obj,
            reporter=request.user,
            subject=form.cleaned_data["subject"],
            reason=form.cleaned_data["reason"],
            message=form.cleaned_data["message"],
        )
        uploaders = get_table_uploaders(table_obj)
        notify_new_report(report, uploaders)
        messages.success(
            request,
            "Thank you. Your report "
            f"{report.tracking_id} was submitted and the dataset has been "
            "temporarily blocked pending review. A confirmation email was sent.",
        )
        return redirect("dataedit:view", table=table_obj.name)


class TableReportRespondView(LoginRequiredMixin, View):
    def _get_report_for_uploader(
        self, request: HttpRequest, table: str, report_id: int
    ) -> ContentReport:
        table_obj = table_or_404(table=table)
        report = get_object_or_404(
            ContentReport, pk=report_id, table=table_obj, table_name=table_obj.name
        )
        uploaders = get_table_uploaders(table_obj)
        if request.user not in uploaders and not getattr(request.user, "is_admin", False):
            raise PermissionDenied("Only the dataset uploader can respond.")
        if not report.is_open:
            raise PermissionDenied("This report is already closed.")
        return report

    def get(self, request: HttpRequest, table: str, report_id: int) -> HttpResponse:
        report = self._get_report_for_uploader(request, table, report_id)
        form = UploaderResponseForm(initial={"response": report.uploader_response})
        return render(
            request,
            "dataedit/report_respond.html",
            {"form": form, "report": report, "table": report.table},
        )

    def post(self, request: HttpRequest, table: str, report_id: int) -> HttpResponse:
        report = self._get_report_for_uploader(request, table, report_id)
        form = UploaderResponseForm(data=request.POST)
        if not form.is_valid():
            return render(
                request,
                "dataedit/report_respond.html",
                {"form": form, "report": report, "table": report.table},
            )
        record_uploader_response(report, form.cleaned_data["response"])
        notify_uploader_responded(report)
        messages.success(request, "Your response was sent to the moderation team.")
        return redirect("dataedit:view", table=table)


class ModerationQueueView(PlatformAdminRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "dataedit/moderation_queue.html",
            {
                "open_reports": open_reports_queryset(),
                "closed_reports": ContentReport.objects.exclude(
                    status__in=ContentReport.OPEN_STATUSES
                ).select_related("reporter", "resolved_by")[:50],
            },
        )


class ModerationDetailView(PlatformAdminRequiredMixin, View):
    def get(self, request: HttpRequest, report_id: int) -> HttpResponse:
        report = get_object_or_404(
            ContentReport.objects.select_related("table", "reporter", "resolved_by"),
            pk=report_id,
        )
        uploaders = get_table_uploaders(report.table) if report.table else []
        form = ModerationResolveForm() if report.is_open else None
        return render(
            request,
            "dataedit/moderation_detail.html",
            {
                "report": report,
                "uploaders": uploaders,
                "form": form,
            },
        )

    def post(self, request: HttpRequest, report_id: int) -> HttpResponse:
        report = get_object_or_404(ContentReport, pk=report_id)
        if not report.is_open:
            messages.warning(request, "This report is already resolved.")
            return redirect("dataedit:moderation-detail", report_id=report.pk)

        form = ModerationResolveForm(data=request.POST)
        if not form.is_valid():
            uploaders = get_table_uploaders(report.table) if report.table else []
            return render(
                request,
                "dataedit/moderation_detail.html",
                {"report": report, "uploaders": uploaders, "form": form},
            )

        action = form.cleaned_data["action"]
        note = form.cleaned_data["resolution_note"]
        uploaders = get_table_uploaders(report.table) if report.table else []

        if action == ModerationResolveForm.ACTION_DISMISS:
            resolve_no_violation(report, request.user, note)
            notify_resolved_dismissed(report, uploaders)
            messages.success(
                request, "Report dismissed. Moderation hold cleared (if any)."
            )
        elif action == ModerationResolveForm.ACTION_VIOLATION:
            report, deactivated = resolve_violation(report, request.user, note)
            notify_resolved_violation(report, uploaders, deactivated)
            if deactivated:
                names = ", ".join(u.name for u in deactivated)
                messages.warning(
                    request,
                    f"Violation recorded. Dataset deleted. Accounts deactivated: {names}",
                )
            else:
                messages.warning(
                    request,
                    "Violation recorded. Dataset deleted and uploader(s) warned.",
                )
        else:
            raise Http404("Unknown moderation action")

        return redirect("dataedit:moderation-queue")
