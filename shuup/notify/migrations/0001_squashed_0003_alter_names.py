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
    replaces = [
        ('shuup_notify', '0001_initial'),
        ('shuup_notify', '0002_notify_script_template'),
        ('shuup_notify', '0003_alter_names'),
    ]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True)),
                ('recipient_type', enumfields.fields.EnumIntegerField(
                    default=1,
                    verbose_name='recipient type',
                    enum=shuup.notify.enums.RecipientType)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('message', models.CharField(
                    default='',
                    verbose_name='message',
                    max_length=140,
                    editable=False)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    null=True,
                    editable=False,
                    max_length=64,
                    blank=True,
                    unique=False)),
                ('priority', enumfields.fields.EnumIntegerField(
                    default=2,
                    verbose_name='priority',
                    db_index=True,
                    enum=shuup.notify.enums.Priority)),
                ('_data', jsonfield.fields.JSONField(
                    blank=True, null=True, editable=False, db_column='data')),
                ('marked_read', models.BooleanField(
                    default=False,
                    verbose_name='marked read',
                    db_index=True,
                    editable=False)),
                ('marked_read_on', models.DateTimeField(
                    blank=True, null=True, verbose_name='marked read on')),
                ('marked_read_by', models.ForeignKey(
                    null=True,
                    editable=False,
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    verbose_name='marked read by',
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+')),
                ('recipient', models.ForeignKey(
                    null=True,
                    to=settings.AUTH_USER_MODEL,
                    blank=True,
                    verbose_name='recipient',
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+')),
            ], ),
        migrations.CreateModel(
            name='Script',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    auto_created=True,
                    verbose_name='ID',
                    primary_key=True)),
                ('event_identifier', models.CharField(
                    verbose_name='event identifier',
                    db_index=True,
                    max_length=64)),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    null=True,
                    editable=False,
                    max_length=64,
                    blank=True,
                    unique=True)),
                ('created_on', models.DateTimeField(
                    verbose_name='created on', auto_now_add=True)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('enabled', models.BooleanField(
                    default=False, verbose_name='enabled', db_index=True)),
                ('_step_data', jsonfield.fields.JSONField(
                    default=[], db_column='step_data')),
                ('template', models.CharField(
                    default=None,
                    max_length=64,
                    help_text=(
                        'the template identifier used to create this script'),
                    blank=True,
                    verbose_name='template identifier',
                    null=True)),
            ], ),
    ]
