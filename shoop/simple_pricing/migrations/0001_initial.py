# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimpleProductPrice',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('price', shoop.core.fields.MoneyValueField(default=0, decimal_places=9, max_digits=36)),
                ('includes_tax', models.BooleanField(default=True)),
                ('group', models.ForeignKey(null=True, to='shoop.ContactGroup', blank=True)),
                ('product', models.ForeignKey(to='shoop.Product', related_name='+')),
                ('shop', models.ForeignKey(null=True, to='shoop.Shop', blank=True)),
            ],
            options={
                'verbose_name': 'product price',
                'verbose_name_plural': 'product prices',
            },
        ),
        migrations.AlterUniqueTogether(
            name='simpleproductprice',
            unique_together=set([('product', 'shop', 'group')]),
        ),
    ]
