"""
SPDX-FileCopyrightText: 2025 Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils import timezone
from sqlalchemy import text

from oedb.connection import _get_engine


class Command(BaseCommand):
    help = "migrate tags from oedb to oep part2"

    def handle(self, *args, **options):
        # copy data from oedb
        TagOEP = apps.get_model("dataedit", "Tag")
        BasicFactsheet = apps.get_model("modelview", "BasicFactsheet")
        Energymodel = apps.get_model("modelview", "Energymodel")
        Energyframework = apps.get_model("modelview", "Energyframework")

        # map numerical id to normalized name
        tag_names = {}

        con = _get_engine()

        # update tags
        for (
            tag_id,
            tag_name_normalized,
            usage_count,
            name,
            color,
            usage_tracked_since,
            category,
        ) in con.execute(
            text(
                """
                select
                id, name_normalized, usage_count, name, color, usage_tracked_since,
                category
                from public.tags
                """
            )
        ).fetchall():
            tag_names[tag_id] = tag_name_normalized
            tag = TagOEP.objects.filter(name_normalized=tag_name_normalized).first()
            if not tag:
                usage_tracked_since = timezone.make_aware(
                    usage_tracked_since, timezone.get_current_timezone()
                )
                TagOEP.objects.get_or_create(
                    name_normalized=tag_name_normalized,
                    usage_count=usage_count,
                    name=name,
                    color=color,
                    usage_tracked_since=usage_tracked_since,
                    category=category,
                )
            else:
                if category:
                    tag.category = category  # type:ignore
                    tag.save()

        # update factsheets
        for factsheet_class in [BasicFactsheet, Energymodel, Energyframework]:
            for factsheet in factsheet_class.objects.all():
                tag_int_ids = factsheet.tags_TODO_deprecated  # type:ignore
                for tag_int_id in tag_int_ids:
                    if tag_int_id not in tag_names:
                        print(f"Missing tag: {tag_int_id}")
                        continue
                    tag_name_normalized = tag_names[tag_int_id]
                    tag = TagOEP.objects.get(name_normalized=tag_name_normalized)
                    factsheet.tags.add(tag)  # type:ignore
                factsheet.save()
