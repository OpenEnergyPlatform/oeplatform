"""
SPDX-FileCopyrightText: 2025 Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0040_tag_table_tags"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="table",
            name="schema",
        ),
    ]
