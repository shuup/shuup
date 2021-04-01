# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import enumfields.fields
from django.db import migrations, models

import shuup.core.fields
import shuup.xtheme.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SavedViewConfig',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('theme_identifier', models.CharField(db_index=True, max_length=64, verbose_name='theme identifier')),
                ('view_name', models.CharField(db_index=True, max_length=64, verbose_name='view name')),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('status', enumfields.fields.EnumIntegerField(db_index=True, verbose_name='status', enum=shuup.xtheme.models.SavedViewConfigStatus)),
                ('_data', shuup.core.fields.TaggedJSONField(db_column='data', default=dict, verbose_name='internal data')),
            ],
        ),
        migrations.CreateModel(
            name='ThemeSettings',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('theme_identifier', models.CharField(db_index=True, max_length=64, verbose_name='theme identifier', unique=True)),
                ('active', models.BooleanField(verbose_name='active', db_index=True, default=False)),
                ('data', shuup.core.fields.TaggedJSONField(db_column='data', default=dict, verbose_name='data')),
            ],
        ),
    ]
