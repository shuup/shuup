# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('simple_supplier', '0003_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockadjustment',
            name='purchase_price_value',
            field=shuup.core.fields.MoneyValueField(default=0, max_digits=36, decimal_places=9),
        ),
        migrations.AddField(
            model_name='stockcount',
            name='stock_value_value',
            field=shuup.core.fields.MoneyValueField(default=0, max_digits=36, decimal_places=9),
        ),
        migrations.AlterUniqueTogether(
            name='stockadjustment',
            unique_together=set([]),
        ),
    ]
