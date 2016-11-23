# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0008_blank_slugs_for_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxtranslation',
            name='name',
            field=models.CharField(verbose_name='name', max_length=124),
        ),
    ]
