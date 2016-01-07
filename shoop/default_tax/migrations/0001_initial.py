# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxRule',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('enabled', models.BooleanField(verbose_name='enabled', db_index=True, default=True)),
                ('country_codes_pattern', models.CharField(blank=True, max_length=300)),
                ('region_codes_pattern', models.CharField(blank=True, max_length=500)),
                ('postal_codes_pattern', models.CharField(blank=True, max_length=500)),
                ('priority', models.IntegerField(default=0, help_text='Rules with same priority are value-added (e.g. US taxes) and rules with different priority are compound taxes (e.g. Canada Quebec PST case)')),
                ('customer_tax_groups', models.ManyToManyField(to='shoop.CustomerTaxGroup')),
                ('tax', models.ForeignKey(to='shoop.Tax')),
                ('tax_classes', models.ManyToManyField(to='shoop.TaxClass')),
            ],
        ),
    ]
