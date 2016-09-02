# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0007_shop_languages_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producttranslation',
            name='slug',
            field=models.SlugField(null=True, verbose_name='slug', blank=True, max_length=255),
        ),
    ]
