__license__ = """
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

# An honest creation date (#2559, spec #2551). ``date_updated`` is the
# creation time only for Tables created after 0044_table_date_updated ran;
# that migration filled it for every Table existing then from dates declared
# in the Table's own metadata (publicationDate, contributors[].date), or NULL.
# So ``created`` copies ``date_updated`` for the Tables above the rollout line
# and leaves every other one NULL, which the dashboard shows as "before Nov
# 2025". ``date_updated`` is not touched.
#
# TRAP (the modelview.0066 one): ``null=True`` does not keep AddField from
# filling the existing rows. Django's schema editor special-cases
# auto_now_add in ``_effective_default``, so the ADD COLUMN carries a DEFAULT
# of the moment the migration runs and stamps every existing Table with it.
# ``fill_created`` therefore writes every row, both sides of the line.
# Checked with sqlmigrate: ADD COLUMN ... DEFAULT '<now>' NULL, then DROP
# DEFAULT; the RunPython step overwrites both halves.

from django.db import migrations, models
from django.db.models import F

# The highest Table id whose ``date_updated`` is not a creation time.
# Measured on production by the maintainer on 2026-10-05, read-only (a READ
# ONLY transaction in ``manage.py shell`` on the Django database), with the
# recipe in spec #2551's Further Notes:
# - 0044_table_date_updated was applied at 2025-10-30 15:14:38.109145+00:00;
# - the highest id with ``date_updated`` NULL or before that moment is 69915
#   (4,567 Tables at or below it, 547 above, highest id 71204);
# - above it the dates rise with the id, with no out-of-order row in the first
#   30. The first ones (69931 on 2025-11-05, 69932 and 69933 on 2025-11-07)
#   carry microseconds, so they are creation times, not metadata dates (those
#   parse to midnight). Ids 69916-69930 do not exist (deleted Tables) and do
#   not move the line.
# On any other database (a developer's, a test run's) the ids mean nothing:
# there every Table at or below the line reads "before Nov 2025".
ROLLOUT_LINE = 69915


def fill_created(apps, schema_editor):
    """Copy ``date_updated`` above the line, clear it at or below. Both
    halves are written, because AddField has just stamped every row."""
    Table = apps.get_model("dataedit", "Table")
    Table.objects.filter(pk__gt=ROLLOUT_LINE).update(created=F("date_updated"))
    Table.objects.filter(pk__lte=ROLLOUT_LINE).update(created=None)


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0056_table_modified"),
    ]

    operations = [
        migrations.AddField(
            model_name="table",
            name="created",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.RunPython(fill_created, migrations.RunPython.noop),
    ]
