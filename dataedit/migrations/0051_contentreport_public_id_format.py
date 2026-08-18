"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from collections import defaultdict

from django.db import migrations, models
from django.utils import timezone


def rewrite_report_public_ids(apps, schema_editor):
    ContentReport = apps.get_model("dataedit", "ContentReport")
    grouped = defaultdict(list)
    for report in ContentReport.objects.order_by("created", "id"):
        created = report.created or timezone.now()
        if timezone.is_aware(created):
            created = timezone.localtime(created)
        key = (created.year, created.month, created.day)
        grouped[key].append(report)

    # Two-step update so unique constraint is never violated mid-rewrite.
    for reports in grouped.values():
        for report in reports:
            report.public_id = f"tmp-{report.pk}"
            report.save(update_fields=["public_id"])

    for (year, month, day), reports in grouped.items():
        for index, report in enumerate(reports, start=1):
            report.public_id = f"RP00/{year:04d}/{month:02d}/{day:02d}/-{index}"
            report.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0050_contentreport_public_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contentreport",
            name="public_id",
            field=models.CharField(editable=False, max_length=40, unique=True),
        ),
        migrations.RunPython(rewrite_report_public_ids, migrations.RunPython.noop),
    ]
