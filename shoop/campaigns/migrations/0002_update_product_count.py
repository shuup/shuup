# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baskettotalproductamountcondition',
            name='product_count',
            field=models.DecimalField(null=True, verbose_name='product count in basket', max_digits=36, decimal_places=9, blank=True),
        ),
    ]
