__license__ = """
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

# The Dataset lifecycle (#2618, spec #2613). ``published_at`` null is a draft,
# a value is "published since then"; ``modified_at`` is the last change to the
# Dataset itself, stamped by later slices.
#
# Every Dataset existing now was publicly listed, so it is migrated as
# published since its creation: ``published_at = created_at``, never the
# moment of the deploy, so no link, sidebar or OEKG citation goes dark.
# ``modified_at`` stays NULL: nothing recorded a Modification before.
#
# Neither field is auto_now/auto_now_add, so unlike dataedit.0057 the ADD
# COLUMN carries no DEFAULT (checked with sqlmigrate: ADD COLUMN ... NULL and
# nothing else). dataedit/tests/test_dataset_lifecycle_migration.py holds it.

from django.db import migrations, models
from django.db.models import F


def fill_published(apps, schema_editor):
    """Every existing Dataset is published since its creation."""
    Dataset = apps.get_model("dataedit", "Dataset")
    Dataset.objects.update(published_at=F("created_at"))


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0057_table_created"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="modified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dataset",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(fill_published, migrations.RunPython.noop),
    ]
