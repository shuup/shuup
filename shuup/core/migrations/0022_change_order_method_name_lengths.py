# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0021_weight_based_pricing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method_name',
            field=models.CharField(default='', max_length=100, verbose_name='payment method name', blank=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='shipping_method_name',
            field=models.CharField(default='', max_length=100, verbose_name='shipping method name', blank=True),
        ),
    ]
