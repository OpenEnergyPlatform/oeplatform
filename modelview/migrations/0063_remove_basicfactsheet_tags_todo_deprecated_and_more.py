"""
SPDX-FileCopyrightText: 2025 wingechr
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0043_tag_category"),
        ("modelview", "0062_rename_tags_basicfactsheet_tags_todo_deprecated"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="basicfactsheet",
            name="tags_TODO_deprecated",
        ),
        migrations.AlterField(
            model_name="basicfactsheet",
            name="tags",
            field=models.ManyToManyField(
                null=True, related_name="factsheets", to="dataedit.tag"
            ),
        ),
    ]
