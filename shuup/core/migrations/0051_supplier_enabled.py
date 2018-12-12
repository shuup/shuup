# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0050_move_product_status_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='enabled',
            field=models.BooleanField(verbose_name='enabled', default=True, help_text='Indicates whether this supplier is currently enabled.'),
        ),
    ]
