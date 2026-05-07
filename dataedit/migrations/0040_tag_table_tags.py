"""
SPDX-FileCopyrightText: 2025 Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0039_alter_table_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "name_normalized",
                    models.CharField(max_length=40, primary_key=True, serialize=False),
                ),
                ("usage_count", models.IntegerField(default=0)),
                ("name", models.CharField(max_length=40)),
                ("color", models.IntegerField(default=3028536)),
                (
                    "usage_tracked_since",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
            ],
        ),
        migrations.AddField(
            model_name="table",
            name="tags",
            field=models.ManyToManyField(related_name="tables", to="dataedit.tag"),
        ),
    ]
