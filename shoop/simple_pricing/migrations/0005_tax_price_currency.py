# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simple_pricing', '0004_simpleproductprice_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='simpleproductprice',
            old_name='price',
            new_name='price_value',
        ),
    ]
