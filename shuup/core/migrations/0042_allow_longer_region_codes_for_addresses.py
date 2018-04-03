# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0041_manufacturer_shops'),
    ]

    operations = [
        migrations.AlterField(
            model_name='immutableaddress',
            name='region_code',
            field=models.CharField(help_text='The address region, province, or state.', max_length=64, verbose_name='region code', blank=True),
        ),
        migrations.AlterField(
            model_name='mutableaddress',
            name='region_code',
            field=models.CharField(help_text='The address region, province, or state.', max_length=64, verbose_name='region code', blank=True),
        ),
    ]
