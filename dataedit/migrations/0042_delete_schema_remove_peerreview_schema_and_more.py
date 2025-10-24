"""
SPDX-FileCopyrightText: 2025 Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0041_remove_table_schema"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Schema",
        ),
        migrations.RemoveField(
            model_name="peerreview",
            name="schema",
        ),
        migrations.RemoveField(
            model_name="tablerevision",
            name="schema",
        ),
        migrations.RemoveField(
            model_name="view",
            name="schema",
        ),
    ]
