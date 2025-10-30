"""
SPDX-FileCopyrightText: 2025 wingechr
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0043_tag_category"),
        ("modelview", "0063_remove_basicfactsheet_tags_todo_deprecated_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="basicfactsheet",
            name="tags",
            field=models.ManyToManyField(related_name="factsheets", to="dataedit.tag"),
        ),
    ]
