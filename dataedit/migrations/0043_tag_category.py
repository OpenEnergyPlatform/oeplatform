"""
SPDX-FileCopyrightText: 2025 wingechr
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0042_delete_schema_remove_peerreview_schema_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tag",
            name="category",
            field=models.CharField(max_length=40, null=True),
        ),
    ]
