"""
SPDX-FileCopyrightText: 2025 wingechr
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("modelview", "0064_alter_basicfactsheet_tags"),
    ]

    operations = [
        migrations.RenameField(
            model_name="basicfactsheet",
            old_name="number_of_devolopers",
            new_name="number_of_developers",
        ),
    ]
