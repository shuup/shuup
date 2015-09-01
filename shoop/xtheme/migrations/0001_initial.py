# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models, migrations
import shoop.xtheme.models
import shoop.core.fields
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SavedViewConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('theme_identifier', models.CharField(max_length=64, db_index=True)),
                ('view_name', models.CharField(max_length=64, db_index=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('status', enumfields.fields.EnumIntegerField(db_index=True, enum=shoop.xtheme.models.SavedViewConfigStatus)),
                ('_data', shoop.core.fields.TaggedJSONField(default=dict, db_column='data')),
            ],
        ),
        migrations.CreateModel(
            name='ThemeSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('theme_identifier', models.CharField(max_length=64, unique=True, db_index=True)),
                ('active', models.BooleanField(default=False, db_index=True)),
                ('data', shoop.core.fields.TaggedJSONField(default=dict, db_column='data')),
            ],
        ),
    ]
