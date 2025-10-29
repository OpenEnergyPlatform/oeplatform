"""
SPDX-FileCopyrightText: 2025 wingechr
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from datetime import datetime

from dateutil import parser
from django.db import migrations, models
from django.utils import timezone


def parse_date(date_string: str) -> datetime | None:
    try:
        return parser.parse(date_string)
    except Exception:
        return None


def get_metadata_date(metadata: dict) -> datetime | None:
    """try to get date from metadata (v2.0) from first resource:
    latest date from publicationDate or date from contributions
    """
    # its ok if there is an error, we will catch it
    resource = metadata["resources"][0]
    dates = []
    dates.append(resource.get("publicationDate"))
    contributors = resource.get("contributors", [])
    for contributor in contributors:
        dates.append(contributor.get("date"))
    # convert and filter None
    dates = [parse_date(ds) for ds in dates]
    dates = [d for d in dates if d]
    if not dates:
        return None
    date = max(dates)
    # make timezone aware
    date = timezone.make_aware(date, timezone.get_current_timezone())

    return date


def update_date_from_metadata(apps, schema_editor):
    """try to set the value of the new field `date_updated` from metadata (v2.0)"""
    Table = apps.get_model("dataedit", "Table")
    for table in Table.objects.all():
        try:
            table.date_updated = get_metadata_date(table.oemetadata or {})
        except Exception:
            pass
        if table.date_updated:
            print(f"{table.name}: {table.date_updated}")
            table.save()


def update_date_from_metadata_rev(apps, schema_editor):
    """no reverse required"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0043_tag_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="table",
            name="date_updated",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.RunPython(update_date_from_metadata, update_date_from_metadata_rev),
    ]
