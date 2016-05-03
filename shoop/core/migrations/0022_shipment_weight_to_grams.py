# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0021_weight_based_pricing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='weight',
            field=shoop.core.fields.MeasurementField(default=0, unit='g', verbose_name='weight', max_digits=36, decimal_places=9),
        ),
    ]
