# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields
import shuup.core.fields
import parler.models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('available_from', models.DateTimeField(blank=True, verbose_name='available from', null=True)),
                ('available_to', models.DateTimeField(blank=True, verbose_name='available to', null=True)),
                ('created_on', models.DateTimeField(verbose_name='created on', auto_now_add=True)),
                ('modified_on', models.DateTimeField(verbose_name='modified on', auto_now=True)),
                ('identifier', shuup.core.fields.InternalIdentifierField(max_length=64, null=True, unique=True, editable=False, blank=True)),
                ('visible_in_menu', models.BooleanField(verbose_name='visible in menu', default=False)),
                ('list_children_on_page', models.BooleanField(verbose_name='list children on page', default=False)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('created_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='created by')),
                ('modified_by', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, null=True, verbose_name='modified by')),
                ('parent', mptt.fields.TreeForeignKey(blank=True, on_delete=models.CASCADE, related_name='children', to='shuup_simple_cms.Page', null=True, verbose_name='parent')),
            ],
            options={
                'verbose_name': 'page',
                'ordering': ('-id',),
                'verbose_name_plural': 'pages',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='PageTranslation',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                ('title', models.CharField(max_length=256, verbose_name='title')),
                ('url', models.CharField(default=None, null=True, unique=True, verbose_name='URL', blank=True, max_length=100)),
                ('content', models.TextField(verbose_name='content')),
                ('master', models.ForeignKey(on_delete=models.CASCADE, related_name='translations', to='shuup_simple_cms.Page', null=True, editable=False)),
            ],
            options={
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'page Translation',
                'managed': True,
                'db_table': 'shuup_simple_cms_page_translation',
            },
        ),
        migrations.AlterUniqueTogether(
            name='pagetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
