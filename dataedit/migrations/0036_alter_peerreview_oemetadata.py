# Generated by Django 3.2.22 on 2024-05-22 10:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dataedit", "0035_auto_20240305_1421"),
    ]

    operations = [
        migrations.AlterField(
            model_name="peerreview",
            name="oemetadata",
            field=models.JSONField(default=dict),
        ),
    ]
