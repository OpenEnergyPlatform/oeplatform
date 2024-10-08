# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-29 15:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("modelview", "0006_auto_20160229_1538")]

    operations = [
        migrations.RenameField(
            model_name="energyscenario",
            old_name="share_RE_amount",
            new_name="share_RE_power_amount",
        ),
        migrations.AddField(
            model_name="energyscenario",
            name="share_RE_heat_amount",
            field=models.SmallIntegerField(
                default=100,
                help_text="development of renewable energy in the heat sector",
                verbose_name="Share RE (heat sector)",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="energyscenario",
            name="share_RE_mobility_amount",
            field=models.SmallIntegerField(
                default=100,
                help_text="development of renewable energy in the mobility sector",
                verbose_name="Share RE (mobility sector)",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="energyscenario",
            name="share_RE_total_amount",
            field=models.SmallIntegerField(
                default=100,
                help_text="development of total renewable energy supply",
                verbose_name="Share RE (total energy supply)",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="energyscenario",
            name="emission_reductions_amount",
            field=models.SmallIntegerField(
                help_text="Development of emissions",
                verbose_name="Potential energy saving",
            ),
        ),
    ]
