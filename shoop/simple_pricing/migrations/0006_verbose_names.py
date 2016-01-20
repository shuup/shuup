# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('simple_pricing', '0005_tax_price_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simpleproductprice',
            name='group',
            field=models.ForeignKey(verbose_name='contact group', to='shoop.ContactGroup'),
        ),
        migrations.AlterField(
            model_name='simpleproductprice',
            name='price_value',
            field=shoop.core.fields.MoneyValueField(verbose_name='price', decimal_places=9, max_digits=36),
        ),
        migrations.AlterField(
            model_name='simpleproductprice',
            name='product',
            field=models.ForeignKey(verbose_name='product', related_name='+', to='shoop.Product'),
        ),
        migrations.AlterField(
            model_name='simpleproductprice',
            name='shop',
            field=models.ForeignKey(verbose_name='shop', to='shoop.Shop'),
        ),
    ]
