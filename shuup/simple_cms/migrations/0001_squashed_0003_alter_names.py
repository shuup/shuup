# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.migrations.operations.special
import django.db.models.deletion
import mptt.fields
import parler.models
from django.conf import settings
from django.db import migrations, models

import shuup.core.fields


class Migration(migrations.Migration):
    replaces = [
        ('shuup_simple_cms', '0001_initial'),
        ('shuup_simple_cms', '0002_md_to_html'),
        ('shuup_simple_cms', '0003_alter_names'),
    ]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('available_from', models.DateTimeField(
                    null=True, blank=True, verbose_name='available from')),
                ('available_to', models.DateTimeField(
                    null=True, blank=True, verbose_name='available to')),
                ('created_on', models.DateTimeField(
                    auto_now_add=True, verbose_name='created on')),
                ('modified_on', models.DateTimeField(
                    auto_now=True, verbose_name='modified on')),
                ('identifier', shuup.core.fields.InternalIdentifierField(
                    editable=False,
                    blank=True,
                    unique=True,
                    null=True,
                    max_length=64)),
                ('visible_in_menu', models.BooleanField(
                    default=False, verbose_name='visible in menu')),
                ('list_children_on_page', models.BooleanField(
                    default=False, verbose_name='list children on page')),
                ('lft', models.PositiveIntegerField(
                    db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(
                    db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(
                    db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(
                    db_index=True, editable=False)),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    blank=True,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='created by',
                    null=True,
                    related_name='+')),
                ('modified_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    blank=True,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='modified by',
                    null=True,
                    related_name='+')),
                ('parent', mptt.fields.TreeForeignKey(
                    blank=True,
                    to='shuup_simple_cms.Page',
                    verbose_name='parent',
                    null=True,
                    related_name='children', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'pages',
                'ordering': ('-id', ),
                'verbose_name': 'page',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model), ),
        migrations.CreateModel(
            name='PageTranslation',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False,
                    primary_key=True,
                    verbose_name='ID')),
                ('language_code', models.CharField(
                    db_index=True, max_length=15, verbose_name='Language')),
                ('title', models.CharField(
                    max_length=256, verbose_name='title')),
                ('url', models.CharField(
                    blank=True,
                    default=None,
                    verbose_name='URL',
                    null=True,
                    max_length=100,
                    unique=True)),
                ('content', models.TextField(verbose_name='content')),
                ('master', models.ForeignKey(
                    editable=False,
                    to='shuup_simple_cms.Page',
                    null=True,
                    related_name='translations', on_delete=models.CASCADE)),
            ],
            options={
                'default_permissions': (),
                'db_tablespace': '',
                'db_table': 'shuup_simple_cms_page_translation',
                'managed': True,
                'verbose_name': 'page Translation',
            }, ),
        migrations.AlterUniqueTogether(
            name='pagetranslation',
            unique_together=set([('language_code', 'master')])),
        migrations.AlterField(
            model_name='page',
            name='available_from',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=(
                    'Set an available from date to restrict the page to '
                    'be available only after a certain date and time. This '
                    'is useful for pages describing sales campaigns or other '
                    'time-sensitive pages.'),
                verbose_name='available from')),
        migrations.AlterField(
            model_name='page',
            name='available_to',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=(
                    'Set an available to date to restrict the page to be '
                    'available only after a certain date and time. This is '
                    'useful for pages describing sales campaigns or other '
                    'time-sensitive pages.'),
                verbose_name='available to')),
        migrations.AlterField(
            model_name='page',
            name='list_children_on_page',
            field=models.BooleanField(
                help_text=(
                    'Check this if this page should list its children pages.'),
                default=False,
                verbose_name='list children on page'), ),
        migrations.AlterField(
            model_name='page',
            name='parent',
            field=mptt.fields.TreeForeignKey(
                blank=True,
                to='shuup_simple_cms.Page',
                verbose_name='parent',
                null=True,
                related_name='children',
                on_delete=models.CASCADE,
                help_text=(
                    'Set this to a parent page if this page should be '
                    'subcategorized under another page.')
            )),
        migrations.AlterField(
            model_name='page',
            name='visible_in_menu',
            field=models.BooleanField(
                help_text=(
                    'Check this if this page should have a link in the top '
                    'menu of the store front.'),
                default=False,
                verbose_name='visible in menu'), ),
        migrations.AlterField(
            model_name='pagetranslation',
            name='content',
            field=models.TextField(
                help_text=(
                    'The page content. This is the text that is displayed '
                    'when customers click on your page link.'),
                verbose_name='content'), ),
        migrations.AlterField(
            model_name='pagetranslation',
            name='title',
            field=models.CharField(
                max_length=256,
                help_text=(
                    'The page title. This is shown anywhere links to your '
                    'page are shown.'),
                verbose_name='title'), ),
        migrations.AlterField(
            model_name='pagetranslation',
            name='url',
            field=models.CharField(
                blank=True,
                default=None,
                verbose_name='URL',
                null=True,
                max_length=100,
                help_text=(
                    'The page url. Choose a descriptive url so that search '
                    'engines can rank your page higher. Often the best url is '
                    'simply the page title with spaces replaced with dashes.'),
                unique=True), ),
    ]
