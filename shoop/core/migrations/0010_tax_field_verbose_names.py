# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0009_tax_price_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tax',
            name='amount_value',
            field=shoop.core.fields.MoneyValueField(max_digits=36, default=None, blank=True, verbose_name='tax amount value', help_text='The flat amount of the tax. Mutually exclusive with percentage rates.', null=True, decimal_places=9),
        ),
        migrations.AlterField(
            model_name='tax',
            name='currency',
            field=shoop.core.fields.CurrencyField(blank=True, verbose_name='currency of tax amount', default=None, null=True, max_length=4),
        ),
        migrations.AlterField(
            model_name='tax',
            name='rate',
            field=models.DecimalField(max_digits=6, blank=True, verbose_name='tax rate', help_text='The percentage rate of the tax.', null=True, decimal_places=5),
        ),
        migrations.AlterField(
            model_name='taxtranslation',
            name='name',
            field=models.CharField(verbose_name='name', max_length=64),
        ),
    ]
