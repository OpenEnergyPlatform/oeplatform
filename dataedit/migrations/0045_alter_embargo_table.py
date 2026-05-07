"""
SPDX-FileCopyrightText: Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0044_table_date_updated"),
    ]

    operations = [
        migrations.AlterField(
            model_name="embargo",
            name="table",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="embargos",
                to="dataedit.table",
            ),
        ),
    ]
