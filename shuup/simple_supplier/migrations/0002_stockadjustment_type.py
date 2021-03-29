# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import enumfields.fields
from django.db import migrations, models

import shuup.core.suppliers.enums


class Migration(migrations.Migration):

    dependencies = [
        ('simple_supplier', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockadjustment',
            name='type',
            field=enumfields.fields.EnumIntegerField(default=1, db_index=True, verbose_name='type', enum=shuup.core.suppliers.enums.StockAdjustmentType),
        ),
    ]
