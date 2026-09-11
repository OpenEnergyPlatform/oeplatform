"""Room in the modifications table for what the REST API records.

Purely additive: every new column is nullable and nothing backfills. Rows
written before the API keep their values untouched -- `verb` stays NULL on
them, which is what lets a reader tell the two generations apart without a
migration that rewrites the one table whose value is being an unaltered record.

`old_state` and `new_state` become nullable for the same reason from the other
side: API rows carry their diff in `removed` / `added` as real structured JSON,
so they leave the double-encoded legacy columns empty rather than writing a
second representation into them and breaking the existing diff viewer.

The index on `bundle_id` is the only sensible query key and there was none.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("factsheet", "0011_scenariobundleaccesscontrol"),
    ]

    operations = [
        migrations.AddField(
            model_name="oekg_modifications",
            name="added",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oekg_modifications",
            name="removed",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oekg_modifications",
            name="resource_type",
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AddField(
            model_name="oekg_modifications",
            name="resource_uuid",
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AddField(
            model_name="oekg_modifications",
            name="verb",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="oekg_modifications",
            name="version_after",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="oekg_modifications",
            name="version_before",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="oekg_modifications",
            name="bundle_id",
            field=models.CharField(db_index=True, default="none", max_length=400),
        ),
        migrations.AlterField(
            model_name="oekg_modifications",
            name="new_state",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="oekg_modifications",
            name="old_state",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
