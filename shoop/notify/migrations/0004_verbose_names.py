# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import enumfields.fields
import shoop.notify.enums


class Migration(migrations.Migration):

    dependencies = [
        ('shoop_notify', '0003_fk_on_delete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='marked_read',
            field=models.BooleanField(db_index=True, verbose_name='marked read', editable=False, default=False),
        ),
        migrations.AlterField(
            model_name='notification',
            name='marked_read_by',
            field=models.ForeignKey(verbose_name='marked read by', blank=True, null=True, related_name='+', to=settings.AUTH_USER_MODEL, editable=False, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='notification',
            name='marked_read_on',
            field=models.DateTimeField(verbose_name='marked read on', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='message',
            field=models.CharField(verbose_name='message', max_length=140, editable=False, default=''),
        ),
        migrations.AlterField(
            model_name='notification',
            name='priority',
            field=enumfields.fields.EnumIntegerField(db_index=True, verbose_name='priority', default=2, enum=shoop.notify.enums.Priority),
        ),
        migrations.AlterField(
            model_name='notification',
            name='recipient',
            field=models.ForeignKey(verbose_name='recipient', blank=True, null=True, related_name='+', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='notification',
            name='recipient_type',
            field=enumfields.fields.EnumIntegerField(verbose_name='recipient type', enum=shoop.notify.enums.RecipientType, default=1),
        ),
        migrations.AlterField(
            model_name='script',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='script',
            name='enabled',
            field=models.BooleanField(db_index=True, verbose_name='enabled', default=False),
        ),
        migrations.AlterField(
            model_name='script',
            name='event_identifier',
            field=models.CharField(db_index=True, verbose_name='event identifier', max_length=64),
        ),
        migrations.AlterField(
            model_name='script',
            name='name',
            field=models.CharField(verbose_name='name', max_length=64),
        ),
    ]
