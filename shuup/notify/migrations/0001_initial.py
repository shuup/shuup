# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
import enumfields.fields
import jsonfield.fields
from django.conf import settings
from django.db import migrations, models

import shuup.core.fields
import shuup.notify.enums


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('recipient_type', enumfields.fields.EnumIntegerField(verbose_name='recipient type', default=1, enum=shuup.notify.enums.RecipientType)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(verbose_name='message', editable=False, max_length=140, default='')),
                ('identifier', shuup.core.fields.InternalIdentifierField(max_length=64, null=True, unique=False, editable=False, blank=True)),
                ('priority', enumfields.fields.EnumIntegerField(verbose_name='priority', db_index=True, default=2, enum=shuup.notify.enums.Priority)),
                ('_data', jsonfield.fields.JSONField(db_column='data', blank=True, null=True, editable=False)),
                ('marked_read', models.BooleanField(verbose_name='marked read', editable=False, default=False, db_index=True)),
                ('marked_read_on', models.DateTimeField(blank=True, verbose_name='marked read on', null=True)),
                ('marked_read_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, editable=False, verbose_name='marked read by')),
                ('recipient', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='recipient')),
            ],
        ),
        migrations.CreateModel(
            name='Script',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('event_identifier', models.CharField(db_index=True, max_length=64, verbose_name='event identifier')),
                ('identifier', shuup.core.fields.InternalIdentifierField(max_length=64, null=True, unique=True, editable=False, blank=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('name', models.CharField(max_length=64, verbose_name='name')),
                ('enabled', models.BooleanField(verbose_name='enabled', db_index=True, default=False)),
                ('_step_data', jsonfield.fields.JSONField(db_column='step_data', default=[])),
            ],
        ),
    ]
