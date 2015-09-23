# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0007_product_media'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='maintenance_mode',
            field=models.BooleanField(default=False, verbose_name='maintenance mode'),
        ),
        migrations.AddField(
            model_name='shoptranslation',
            name='maintenance_message',
            field=models.CharField(max_length=300, blank=True),
        ),
    ]
