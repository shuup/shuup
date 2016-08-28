# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import parler.models
import enumfields.fields
import filer.fields.image
import shuup.front.apps.carousel.models


class Migration(migrations.Migration):

    dependencies = [
        ('filer', '0006_auto_20160623_1627'),
        ('shuup', '0005_shopproduct_visibilty'),
        ('shuup_simple_cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Carousel',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=50, help_text='Name is only used to configure carousels.', verbose_name='name')),
                ('animation', enumfields.fields.EnumIntegerField(enum=shuup.front.apps.carousel.models.CarouselMode, verbose_name='animation', default=0, help_text='Animation type for cycling slides.')),
                ('interval', models.IntegerField(verbose_name='interval', help_text='Slide interval in seconds.', default=5)),
                ('pause_on_hover', models.BooleanField(verbose_name='pause on hover', help_text='Pauses the cycling of the carousel on mouse over.', default=True)),
                ('is_arrows_visible', models.BooleanField(verbose_name='show navigation arrows', default=True)),
                ('use_dot_navigation', models.BooleanField(verbose_name='show navigation dots', default=True)),
                ('image_width', models.IntegerField(verbose_name='image width', help_text='Slide images will be cropped to this width.', default=1200)),
                ('image_height', models.IntegerField(verbose_name='image height', help_text='Slide images will be cropped to this height.', default=600)),
            ],
            options={
                'verbose_name': 'Carousel',
                'verbose_name_plural': 'Carousels',
            },
        ),
        migrations.CreateModel(
            name='Slide',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=50, null=True, help_text='Name is only used to configure slides.', blank=True, verbose_name='name')),
                ('ordering', models.IntegerField(blank=True, default=0, null=True, verbose_name='ordering')),
                ('target', enumfields.fields.EnumIntegerField(enum=shuup.front.apps.carousel.models.LinkTargetType, verbose_name='link target', default=0)),
                ('available_from', models.DateTimeField(blank=True, null=True, verbose_name='available from')),
                ('available_to', models.DateTimeField(blank=True, null=True, verbose_name='available to')),
                ('carousel', models.ForeignKey(to='carousel.Carousel', related_name='slides')),
                ('category_link', models.ForeignKey(blank=True, to='shuup.Category', verbose_name='category link', null=True)),
                ('cms_page_link', models.ForeignKey(blank=True, to='shuup_simple_cms.Page', verbose_name='cms page link', null=True)),
                ('product_link', models.ForeignKey(blank=True, to='shuup.Product', verbose_name='product link', null=True)),
            ],
            options={
                'verbose_name': 'Slide',
                'ordering': ('ordering', 'id'),
                'verbose_name_plural': 'Slides',
            },
            bases=(parler.models.TranslatableModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SlideTranslation',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('language_code', models.CharField(db_index=True, max_length=15, verbose_name='Language')),
                ('caption', models.CharField(max_length=80, null=True, blank=True, verbose_name='caption')),
                ('caption_text', models.TextField(blank=True, null=True, help_text='When displayed in banner box mode, caption text is shown as a tooltip', verbose_name='caption text')),
                ('external_link', models.CharField(max_length=160, null=True, blank=True, verbose_name='external link')),
                ('image', filer.fields.image.FilerImageField(blank=True, to='filer.Image', on_delete=django.db.models.deletion.PROTECT, verbose_name='image', null=True)),
                ('master', models.ForeignKey(to='carousel.Slide', related_name='translations', null=True, editable=False)),
            ],
            options={
                'managed': True,
                'db_tablespace': '',
                'db_table': 'carousel_slide_translation',
                'verbose_name': 'Slide Translation',
                'default_permissions': (),
            },
        ),
        migrations.AlterUniqueTogether(
            name='slidetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
