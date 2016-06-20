# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0007_freeproductline'),
    ]

    operations = [
        migrations.AddField(
            model_name='freeproductline',
            name='quantity',
            field=models.PositiveIntegerField(verbose_name='quantity', default=1),
        ),
        migrations.AddField(
            model_name='productsinbasketcondition',
            name='quantity',
            field=models.PositiveIntegerField(verbose_name='quantity', default=1),
        ),
    ]
