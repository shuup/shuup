# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
import enumfields.fields
import filer.fields.image
import parler.models
from django.db import migrations, models

import shuup.front.apps.carousel.models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0009_update_tax_name_max_length'),
        ('shuup_simple_cms', '0001_initial'),
        ('filer', '0002_auto_20150606_2003'),
    ]

    operations = [
        migrations.CreateModel(
            name='Carousel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(help_text='Name is only used to configure carousels.', max_length=50, verbose_name='name')),
                ('animation', enumfields.fields.EnumIntegerField(help_text='Animation type for cycling slides.', enum=shuup.front.apps.carousel.models.CarouselMode, verbose_name='animation', default=0)),
                ('interval', models.IntegerField(help_text='Slide interval in seconds.', verbose_name='interval', default=5)),
                ('pause_on_hover', models.BooleanField(help_text='Pauses the cycling of the carousel on mouse over.', verbose_name='pause on hover', default=True)),
                ('is_arrows_visible', models.BooleanField(verbose_name='show navigation arrows', default=True)),
                ('use_dot_navigation', models.BooleanField(verbose_name='show navigation dots', default=True)),
                ('image_width', models.IntegerField(help_text='Slide images will be cropped to this width.', verbose_name='image width', default=1200)),
                ('image_height', models.IntegerField(help_text='Slide images will be cropped to this height.', verbose_name='image height', default=600)),
            ],
            options={
                'verbose_name': 'Carousel',
                'verbose_name_plural': 'Carousels',
            },
        ),
        migrations.CreateModel(
            name='Slide',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(help_text='Name is only used to configure slides.', blank=True, max_length=50, verbose_name='name', null=True)),
                ('ordering', models.IntegerField(verbose_name='ordering', blank=True, default=0, null=True)),
                ('target', enumfields.fields.EnumIntegerField(verbose_name='link target', enum=shuup.front.apps.carousel.models.LinkTargetType, default=0)),
                ('available_from', models.DateTimeField(verbose_name='available from', blank=True, null=True)),
                ('available_to', models.DateTimeField(verbose_name='available to', blank=True, null=True)),
                ('carousel', models.ForeignKey(related_name='slides', to='carousel.Carousel', on_delete=models.CASCADE)),
                ('category_link', models.ForeignKey(to='shuup.Category', related_name='+', null=True, verbose_name='category link', blank=True, on_delete=models.CASCADE)),
                ('cms_page_link', models.ForeignKey(to='shuup_simple_cms.Page', related_name='+', null=True, verbose_name='cms page link', blank=True, on_delete=models.CASCADE)),
                ('product_link', models.ForeignKey(to='shuup.Product', related_name='+', null=True, verbose_name='product link', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('ordering', 'id'),
                'verbose_name': 'Slide',
                'verbose_name_plural': 'Slides',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SlideTranslation',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('language_code', models.CharField(verbose_name='Language', max_length=15, db_index=True)),
                ('caption', models.CharField(verbose_name='caption', blank=True, max_length=80, null=True)),
                ('caption_text', models.TextField(help_text='When displayed in banner box mode, caption text is shown as a tooltip', blank=True, verbose_name='caption text', null=True)),
                ('external_link', models.CharField(verbose_name='external link', blank=True, max_length=160, null=True)),
                ('image', filer.fields.image.FilerImageField(on_delete=django.db.models.deletion.PROTECT, to='filer.Image', related_name='+', null=True, verbose_name='image', blank=True)),
                ('master', models.ForeignKey(editable=False, related_name='translations', null=True, to='carousel.Slide', on_delete=models.CASCADE)),
            ],
            options={
                'managed': True,
                'db_tablespace': '',
                'db_table': 'carousel_slide_translation',
                'default_permissions': (),
                'verbose_name': 'Slide Translation',
            },
        ),
        migrations.AlterUniqueTogether(
            name='slidetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
