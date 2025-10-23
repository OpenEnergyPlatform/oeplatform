"""
SPDX-FileCopyrightText: 2025 Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils import timezone
from sqlalchemy import text

from api.actions import _get_engine


class Command(BaseCommand):
    help = "migrate tags from oedb to oep"

    def handle(self, *args, **options):
        # copy data from oedb
        TagOEP = apps.get_model("dataedit", "Tag")
        TableOEP = apps.get_model("dataedit", "Table")

        tag_names = {}

        con = _get_engine()
        for (
            id,
            name_normalized,
            usage_count,
            name,
            color,
            usage_tracked_since,
        ) in con.execute(
            text(
                """
                select
                id, name_normalized, usage_count, name, color, usage_tracked_since
                from public.tags
                """
            )
        ).fetchall():
            tag_names[id] = name_normalized
            # convert to timezone aware
            usage_tracked_since = timezone.make_aware(
                usage_tracked_since, timezone.get_current_timezone()
            )
            TagOEP.objects.get_or_create(
                name_normalized=name_normalized,
                usage_count=usage_count,
                name=name,
                color=color,
                usage_tracked_since=usage_tracked_since,
            )

        for table_name, tag_id in con.execute(
            text(
                """
                select
                table_name, tag
                from public.table_tags
                """
            )
        ).fetchall():
            table = TableOEP.objects.filter(name=table_name).first()
            if not table:
                print(f"Warning: table does not exist: {table_name}")
                continue
            tag_name_normalized = tag_names[tag_id]
            tag = TagOEP.objects.filter(name_normalized=tag_name_normalized)
            if not tag:
                print(f"Warning: tag does not exist: {tag_id} / {tag_name_normalized}")
                continue
            table.tags.add(tag)  # type: ignore
            print(table_name, tag)
            table.save()
