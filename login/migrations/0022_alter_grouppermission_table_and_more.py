"""
SPDX-FileCopyrightText: Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0044_table_date_updated"),
        ("login", "0021_auto_20230420_2000"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grouppermission",
            name="table",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_items",
                to="dataedit.table",
            ),
        ),
        migrations.AlterField(
            model_name="userpermission",
            name="table",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_items",
                to="dataedit.table",
            ),
        ),
    ]
