# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('default_tax', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxrule',
            name='customer_tax_groups',
            field=models.ManyToManyField(to='shuup.CustomerTaxGroup', blank=True),
        ),
    ]
