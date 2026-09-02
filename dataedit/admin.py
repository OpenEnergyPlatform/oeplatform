"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.contrib import admin

from dataedit.models import BulkLoadEvent


@admin.register(BulkLoadEvent)
class BulkLoadEventAdmin(admin.ModelAdmin):
    """Bulk load events are an audit trail: visible, filterable, immutable."""

    list_display = (
        "created",
        "table_name",
        "user",
        "status",
        "row_count",
        "bytes_received",
        "id_min",
        "id_max",
    )
    list_filter = ("status", "created")
    search_fields = ("table_name", "user__name")
    ordering = ("-created",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
