# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-21 15:15
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("modelview", "0035_auto_20170724_1801")]

    operations = [
        migrations.AddField(
            model_name="basicfactsheet",
            name="tags",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), default=list, size=None
            ),
        )
    ]
