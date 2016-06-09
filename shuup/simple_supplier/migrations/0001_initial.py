# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import shuup.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StockAdjustment',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(db_index=True, auto_now_add=True)),
                ('delta', shuup.core.fields.QuantityField(default=0, decimal_places=9, max_digits=36)),
                ('created_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('product', models.ForeignKey(to='shuup.Product', related_name='+')),
                ('supplier', models.ForeignKey(to='shuup.Supplier')),
            ],
        ),
        migrations.CreateModel(
            name='StockCount',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('logical_count', shuup.core.fields.QuantityField(default=0, editable=False, decimal_places=9, max_digits=36)),
                ('physical_count', shuup.core.fields.QuantityField(default=0, editable=False, decimal_places=9, max_digits=36)),
                ('product', models.ForeignKey(editable=False, to='shuup.Product', related_name='+')),
                ('supplier', models.ForeignKey(to='shuup.Supplier', editable=False)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='stockcount',
            unique_together=set([('product', 'supplier')]),
        ),
        migrations.AlterUniqueTogether(
            name='stockadjustment',
            unique_together=set([('product', 'supplier')]),
        ),
    ]
