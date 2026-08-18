"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import uuid

from django.db import migrations, models


def fill_public_ids(apps, schema_editor):
    ContentReport = apps.get_model("dataedit", "ContentReport")
    for report in ContentReport.objects.all():
        report.public_id = uuid.uuid4()
        report.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0049_content_moderation"),
    ]

    operations = [
        migrations.AddField(
            model_name="contentreport",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.RunPython(fill_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="contentreport",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
