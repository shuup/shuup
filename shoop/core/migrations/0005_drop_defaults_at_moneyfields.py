# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0004_shopproduct_default_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderline',
            name='_total_discount_amount',
            field=shoop.core.fields.MoneyValueField(default=0, verbose_name='total amount of discount', max_digits=36, decimal_places=9),
        ),
        migrations.AlterField(
            model_name='orderline',
            name='_unit_price_amount',
            field=shoop.core.fields.MoneyValueField(default=0, verbose_name='unit price amount', max_digits=36, decimal_places=9),
        ),
        migrations.AlterField(
            model_name='product',
            name='purchase_price',
            field=shoop.core.fields.MoneyValueField(null=True, verbose_name='purchase price', max_digits=36, decimal_places=9, blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='suggested_retail_price',
            field=shoop.core.fields.MoneyValueField(null=True, verbose_name='suggested retail price', max_digits=36, decimal_places=9, blank=True),
        ),
        migrations.AlterField(
            model_name='suppliedproduct',
            name='purchase_price',
            field=shoop.core.fields.MoneyValueField(null=True, verbose_name='purchase price', max_digits=36, decimal_places=9, blank=True),
        ),
        migrations.AlterField(
            model_name='suppliedproduct',
            name='suggested_retail_price',
            field=shoop.core.fields.MoneyValueField(null=True, verbose_name='suggested retail price', max_digits=36, decimal_places=9, blank=True),
        ),
    ]
