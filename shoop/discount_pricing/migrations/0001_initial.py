# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0005_drop_defaults_at_moneyfields'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountedProductPrice',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('price', shoop.core.fields.MoneyValueField(max_digits=36, decimal_places=9)),
                ('product', models.ForeignKey(to='shoop.Product', related_name='+')),
                ('shop', models.ForeignKey(to='shoop.Shop')),
            ],
            options={
                'verbose_name_plural': 'product prices',
                'verbose_name': 'product price',
            },
        ),
        migrations.AlterUniqueTogether(
            name='discountedproductprice',
            unique_together=set([('product', 'shop')]),
        ),
    ]
