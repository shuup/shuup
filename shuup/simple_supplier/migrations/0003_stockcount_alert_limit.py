# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('simple_supplier', '0002_stockadjustment_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockcount',
            name='alert_limit',
            field=shuup.core.fields.QuantityField(decimal_places=9, editable=False, verbose_name='alert limit', max_digits=36, default=0),
        ),
    ]
