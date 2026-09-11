"""Room in the modifications table for what the REST API records.

**Purely additive, and literally so**: seven nullable columns and one index.
Nothing backfills, nothing is altered, and no existing value is read or
rewritten. Rows written before the API keep everything they have -- `verb`
stays NULL on them, which is what lets a reader tell the two generations apart
without touching the one table whose value is being an unaltered record.

The index is the only non-column change. `bundle_id` is the sole query key this
table has and it had no index at all. Declared as a plain btree rather than
`db_index=True`, because on a CharField that shortcut also builds a second
varchar_pattern_ops index for LIKE queries nothing here makes.

Deploy note: the CREATE INDEX is not CONCURRENT, so it takes a write lock on
the table for as long as it runs. The table holds one row per scenario-bundle
edit made through the browser since 2023, so that is short -- but it is a lock
on the audit table, not nothing.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("factsheet", "0011_scenariobundleaccesscontrol"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
        migrations.AddIndex(
            model_name="oekg_modifications",
            index=models.Index(fields=["bundle_id"], name="oekg_mod_bundle_idx"),
        ),
    ]
