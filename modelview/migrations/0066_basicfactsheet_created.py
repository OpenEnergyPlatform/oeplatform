"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "modelview",
            "0065_rename_number_of_devolopers_basicfactsheet_number_of_developers",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="basicfactsheet",
            name="created",
            # Nullable and NOT backfilled. A default of "now" would have
            # given all 339 existing factsheets a fresh creation date and so
            # opened every one of them to deletion by any account for a week
            # after this deploys. NULL reads as "older than the grace period".
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
