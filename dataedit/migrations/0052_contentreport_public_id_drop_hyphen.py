"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from django.db import migrations


REPORT_ID_RE = re.compile(r"^(RP00/\d{4}/\d{2}/\d{2}/)-(\d+)$")


def rewrite_drop_hyphen(apps, schema_editor):
    ContentReport = apps.get_model("dataedit", "ContentReport")
    mapping = []
    for report in ContentReport.objects.all():
        match = REPORT_ID_RE.match(str(report.public_id))
        if not match:
            continue
        mapping.append((report.pk, f"{match.group(1)}{match.group(2)}"))

    for pk, _new_id in mapping:
        ContentReport.objects.filter(pk=pk).update(public_id=f"tmp-{pk}")

    for pk, new_id in mapping:
        ContentReport.objects.filter(pk=pk).update(public_id=new_id)


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0051_contentreport_public_id_format"),
    ]

    operations = [
        migrations.RunPython(rewrite_drop_hyphen, migrations.RunPython.noop),
    ]
