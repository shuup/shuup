# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('simple_pricing', '0003_remove_groupless_prices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simpleproductprice',
            name='price',
            field=shoop.core.fields.MoneyValueField(max_digits=36, decimal_places=9),
        ),
    ]
