# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('default_tax', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxrule',
            name='postal_codes_pattern',
            field=models.TextField(verbose_name='postal codes pattern', blank=True),
        ),
    ]
