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
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        # `null=True` is NOT enough to leave existing rows empty.
        #
        # Django's schema editor special-cases `auto_now` and `auto_now_add`
        # in `_effective_default`, so `AddField` fills every existing row with
        # the moment the migration runs. Measured, not assumed: after the
        # first run of this migration every pre-existing factsheet carried a
        # `created` equal to the migration's own timestamp.
        #
        # That is the exact outcome the grace period must not have. It would
        # give all 339 existing factsheets a fresh creation date and open
        # every one of them to deletion by any logged-in account for a week
        # after the deploy. NULL reads as "older than the grace period", which
        # is the honest answer: their real creation date was never recorded.
        #
        # At this point in the migration every row is by definition
        # pre-existing, so clearing the column unconditionally is exact.
        migrations.RunSQL(
            sql="UPDATE modelview_basicfactsheet SET created = NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
