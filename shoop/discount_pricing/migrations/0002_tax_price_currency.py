# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('discount_pricing', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='discountedproductprice',
            old_name='price',
            new_name='price_value',
        ),
    ]
