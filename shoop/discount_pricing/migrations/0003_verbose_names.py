# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('discount_pricing', '0002_tax_price_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discountedproductprice',
            name='price_value',
            field=shoop.core.fields.MoneyValueField(verbose_name='price', decimal_places=9, max_digits=36),
        ),
        migrations.AlterField(
            model_name='discountedproductprice',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='+', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='discountedproductprice',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', to='shoop.Shop'),
        ),
    ]
