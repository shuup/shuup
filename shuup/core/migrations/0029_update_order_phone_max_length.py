# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import enumfields.fields
import shuup.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0028_roundingbehaviorcomponent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='phone',
            field=models.CharField(verbose_name='phone', blank=True, max_length=64),
        )
    ]
