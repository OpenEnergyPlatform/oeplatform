"""One more nullable column: the acronym a deleted bundle went by.

Purely additive -- one nullable varchar, no backfill, nothing altered, no
index. Every existing row keeps NULL, which is also what every row other than a
whole-bundle delete will keep: the column exists because a delete is the one
write whose subject is gone afterwards, so the identifier a person would
recognise cannot be looked up any more and has to be in the ledger itself.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("factsheet", "0012_oekg_modifications_api_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="oekg_modifications",
            name="acronym",
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
    ]
