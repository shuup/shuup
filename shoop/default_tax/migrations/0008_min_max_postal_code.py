# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('default_tax', '0007_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxrule',
            name='_postal_codes_max',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='taxrule',
            name='_postal_codes_min',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
