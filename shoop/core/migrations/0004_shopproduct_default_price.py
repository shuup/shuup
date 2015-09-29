# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):
    dependencies = [
        ('shoop', '0003_moneyfield_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopproduct',
            name='default_price',
            field=shoop.core.fields.MoneyValueField(blank=True, null=True, verbose_name='Default price', decimal_places=9,
                                               max_digits=36),
        ),
        migrations.AddField(
            model_name='shop',
            name='prices_include_tax',
            field=models.BooleanField(default=True),
        ),
    ]
