# Generated by Django 3.2.22 on 2024-03-05 13:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dataedit", "0034_table_human_readable_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="peerreview",
            name="oemetadata",
            field=models.JSONField(default=None, null=True),
        ),
        migrations.CreateModel(
            name="Embargo",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_started", models.DateTimeField(auto_now_add=True)),
                ("date_ended", models.DateTimeField()),
                (
                    "duration",
                    models.CharField(
                        choices=[("6_months", "6 Months"), ("1_year", "1 Year")],
                        max_length=10,
                    ),
                ),
                (
                    "table",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="embargoes",
                        to="dataedit.table",
                    ),
                ),
            ],
        ),
    ]
