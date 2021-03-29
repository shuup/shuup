# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0007_add_excluded_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='freeproductline',
            name='quantity',
            field=shuup.core.fields.QuantityField(decimal_places=9, default=1, verbose_name='quantity', max_digits=36),
        ),
    ]
