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
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('available_from', models.DateTimeField(null=True, blank=True)),
                ('available_to', models.DateTimeField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('identifier', shuup.core.fields.InternalIdentifierField(verbose_name='internal identifier', help_text='This identifier can be used in templates to create URLs', editable=False, unique=True, null=True, blank=True, max_length=64)),
                ('visible_in_menu', models.BooleanField(verbose_name='Visible in menu', default=False)),
                ('created_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='+')),
                ('modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='+')),
            ],
            options={
                'verbose_name': 'page',
                'verbose_name_plural': 'pages',
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='PageTranslation',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('title', models.CharField(verbose_name='Page Title', max_length=256)),
                ('url', models.CharField(verbose_name='Page URL', null=True, unique=True, default=None, blank=True, max_length=100)),
                ('content', models.TextField(verbose_name='Content')),
                ('master', models.ForeignKey(editable=False, null=True, to='shuup_simple_cms.Page', related_name='translations')),
            ],
            options={
                'verbose_name': 'page Translation',
                'default_permissions': (),
                'managed': True,
                'db_table': 'shuup_simple_cms_page_translation',
                'db_tablespace': '',
            },
        ),
        migrations.AlterUniqueTogether(
            name='pagetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
