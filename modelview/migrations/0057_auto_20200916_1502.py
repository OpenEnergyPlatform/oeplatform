# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
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
