# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@gmail.com>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("modelview", "0056_auto_20200910_1231"),
    ]

    operations = [
        migrations.RunSQL(
            'ALTER TABLE "modelview_basicfactsheet" ALTER COLUMN "contact_email" TYPE varchar(254)[] USING ARRAY["contact_email"];'  # noqa
        )
    ]
