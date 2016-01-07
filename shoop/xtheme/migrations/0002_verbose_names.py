# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoop.xtheme.models
import shoop.core.fields
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoop_xtheme', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savedviewconfig',
            name='_data',
            field=shoop.core.fields.TaggedJSONField(verbose_name='internal data', default=dict, db_column='data'),
        ),
        migrations.AlterField(
            model_name='savedviewconfig',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='savedviewconfig',
            name='status',
            field=enumfields.fields.EnumIntegerField(db_index=True, verbose_name='status', enum=shoop.xtheme.models.SavedViewConfigStatus),
        ),
        migrations.AlterField(
            model_name='savedviewconfig',
            name='theme_identifier',
            field=models.CharField(db_index=True, verbose_name='theme identifier', max_length=64),
        ),
        migrations.AlterField(
            model_name='savedviewconfig',
            name='view_name',
            field=models.CharField(db_index=True, verbose_name='view name', max_length=64),
        ),
        migrations.AlterField(
            model_name='themesettings',
            name='active',
            field=models.BooleanField(db_index=True, verbose_name='active', default=False),
        ),
        migrations.AlterField(
            model_name='themesettings',
            name='data',
            field=shoop.core.fields.TaggedJSONField(verbose_name='data', default=dict, db_column='data'),
        ),
        migrations.AlterField(
            model_name='themesettings',
            name='theme_identifier',
            field=models.CharField(db_index=True, verbose_name='theme identifier', unique=True, max_length=64),
        ),
    ]
