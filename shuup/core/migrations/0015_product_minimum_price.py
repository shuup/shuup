# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0014_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopproduct',
            name='minimum_price_value',
            field=shuup.core.fields.MoneyValueField(null=True, max_digits=36, decimal_places=9, blank=True, verbose_name='minimum price'),
        ),
    ]
