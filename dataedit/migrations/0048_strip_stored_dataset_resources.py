# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut # noqa: E501
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import migrations


def strip_stored_resources(apps, schema_editor):
    """Resources are assembled live from member tables on every read; drop
    the stale copies persisted by earlier versions of the dataset API."""
    Dataset = apps.get_model("dataedit", "Dataset")
    for dataset in Dataset.objects.all():
        if "resources" in dataset.metadata:
            dataset.metadata.pop("resources")
            dataset.save(update_fields=["metadata"])


class Migration(migrations.Migration):
    dependencies = [
        ("dataedit", "0047_dataset_creator"),
    ]

    operations = [
        migrations.RunPython(strip_stored_resources, migrations.RunPython.noop),
    ]
