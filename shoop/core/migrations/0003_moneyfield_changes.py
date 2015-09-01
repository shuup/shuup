# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import shoop.core.fields


class Migration(migrations.Migration):
    dependencies = [
        ('shoop', '0002_identifier_field_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderline',
            name='_total_discount_amount',
            field=shoop.core.fields.MoneyField(decimal_places=9, verbose_name='total amount of discount',
                                               max_digits=36),
        ),
        migrations.AlterField(
            model_name='orderline',
            name='_unit_price_amount',
            field=shoop.core.fields.MoneyField(decimal_places=9, verbose_name='unit price amount', max_digits=36),
        ),
        migrations.AlterField(
            model_name='orderlinetax',
            name='amount',
            field=shoop.core.fields.MoneyField(decimal_places=9, verbose_name='tax amount', max_digits=36),
        ),
        migrations.AlterField(
            model_name='orderlinetax',
            name='base_amount',
            field=shoop.core.fields.MoneyField(help_text='Amount that this tax is calculated from', decimal_places=9,
                                               verbose_name='base amount', max_digits=36),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=shoop.core.fields.MoneyField(decimal_places=9, max_digits=36),
        ),
        migrations.AlterField(
            model_name='product',
            name='purchase_price',
            field=shoop.core.fields.MoneyField(blank=True, null=True, verbose_name='purchase price', default=None,
                                               decimal_places=9, max_digits=36),
        ),
        migrations.AlterField(
            model_name='product',
            name='suggested_retail_price',
            field=shoop.core.fields.MoneyField(blank=True, null=True, verbose_name='suggested retail price',
                                               default=None, decimal_places=9, max_digits=36),
        ),
        migrations.AlterField(
            model_name='suppliedproduct',
            name='purchase_price',
            field=shoop.core.fields.MoneyField(blank=True, null=True, verbose_name='purchase price', default=None,
                                               decimal_places=9, max_digits=36),
        ),
        migrations.AlterField(
            model_name='suppliedproduct',
            name='suggested_retail_price',
            field=shoop.core.fields.MoneyField(blank=True, null=True, verbose_name='suggested retail price',
                                               default=None, decimal_places=9, max_digits=36),
        ),
    ]
