# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shuup_simple_cms', '0002_fk_on_delete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='available_from',
            field=models.DateTimeField(verbose_name='available from', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='available_to',
            field=models.DateTimeField(verbose_name='available to', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='created_by',
            field=models.ForeignKey(verbose_name='created by', blank=True, null=True, related_name='+', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='page',
            name='created_on',
            field=models.DateTimeField(verbose_name='created on', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='modified_by',
            field=models.ForeignKey(verbose_name='modified by', blank=True, null=True, related_name='+', to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='page',
            name='modified_on',
            field=models.DateTimeField(verbose_name='modified on', auto_now=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='visible_in_menu',
            field=models.BooleanField(verbose_name='visible in menu', default=False),
        ),
        migrations.AlterField(
            model_name='pagetranslation',
            name='content',
            field=models.TextField(verbose_name='content'),
        ),
        migrations.AlterField(
            model_name='pagetranslation',
            name='title',
            field=models.CharField(verbose_name='title', max_length=256),
        ),
        migrations.AlterField(
            model_name='pagetranslation',
            name='url',
            field=models.CharField(unique=True, blank=True, null=True, verbose_name='URL', max_length=100, default=None),
        ),
    ]
