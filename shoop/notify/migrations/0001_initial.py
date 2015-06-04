# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings
import shoop.notify.enums
import enumfields.fields
import shoop.core.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('recipient_type', enumfields.fields.EnumIntegerField(default=1, enum=shoop.notify.enums.RecipientType)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('message', models.CharField(default='', editable=False, max_length=140)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', help_text="Do not change this value if you are not sure what you're doing.", editable=False, unique=True, null=True, blank=True, max_length=64)),
                ('priority', enumfields.fields.EnumIntegerField(default=2, enum=shoop.notify.enums.Priority, db_index=True)),
                ('_data', jsonfield.fields.JSONField(db_column='data', editable=False, null=True, blank=True)),
                ('marked_read', models.BooleanField(default=False, editable=False, db_index=True)),
                ('marked_read_on', models.DateTimeField(null=True, blank=True)),
                ('marked_read_by', models.ForeignKey(editable=False, null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='+')),
                ('recipient', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='+')),
            ],
        ),
        migrations.CreateModel(
            name='Script',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('event_identifier', models.CharField(db_index=True, max_length=64)),
                ('identifier', shoop.core.fields.InternalIdentifierField(verbose_name='internal identifier', help_text="Do not change this value if you are not sure what you're doing.", editable=False, unique=True, null=True, blank=True, max_length=64)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=64)),
                ('enabled', models.BooleanField(default=False, db_index=True)),
                ('_step_data', jsonfield.fields.JSONField(db_column='step_data', default=[])),
            ],
        ),
    ]
