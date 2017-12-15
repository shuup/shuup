# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
import enumfields.fields
import filer.fields.image
import parler.models
from django.db import migrations, models

import shuup.front.apps.carousel.models


class Migration(migrations.Migration):
    replaces = [
        ('carousel', '0001_initial'),
        ('carousel', '0002_alter_names'),
    ]

    dependencies = [
        ('filer', '0002_auto_20150606_2003'),
        ('shuup_simple_cms', '0001_initial'),
        ('shuup', '0001_squashed_0039_alter_names'),
    ]

    operations = [
        migrations.CreateModel(
            name='Carousel',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    verbose_name='ID',
                    auto_created=True,
                    primary_key=True)),
                ('name', models.CharField(
                    max_length=50,
                    verbose_name='name',
                    help_text='Name is only used to configure carousels.')),
                ('animation', enumfields.fields.EnumIntegerField(
                    default=0,
                    verbose_name='animation',
                    help_text='Animation type for cycling slides.',
                    enum=shuup.front.apps.carousel.models.CarouselMode)),
                ('interval', models.IntegerField(
                    default=5,
                    verbose_name='interval',
                    help_text='Slide interval in seconds.')),
                ('pause_on_hover', models.BooleanField(
                    default=True,
                    verbose_name='pause on hover',
                    help_text=(
                        'Pauses the cycling of the carousel on mouse over.'))),
                ('is_arrows_visible', models.BooleanField(
                    default=True, verbose_name='show navigation arrows')),
                ('use_dot_navigation', models.BooleanField(
                    default=True, verbose_name='show navigation dots')),
                ('image_width', models.IntegerField(
                    default=1200,
                    verbose_name='image width',
                    help_text='Slide images will be cropped to this width.')),
                ('image_height', models.IntegerField(
                    default=600,
                    verbose_name='image height',
                    help_text='Slide images will be cropped to this height.')),
            ],
            options={
                'verbose_name_plural': 'Carousels',
                'verbose_name': 'Carousel',
            }),
        migrations.CreateModel(
            name='Slide',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    verbose_name='ID',
                    auto_created=True,
                    primary_key=True)),
                ('name', models.CharField(
                    null=True,
                    max_length=50,
                    verbose_name='name',
                    help_text='Name is only used to configure slides.',
                    blank=True)),
                ('ordering', models.IntegerField(
                    null=True, default=0, verbose_name='ordering',
                    blank=True)),
                ('target', enumfields.fields.EnumIntegerField(
                    default=0,
                    verbose_name='link target',
                    enum=shuup.front.apps.carousel.models.LinkTargetType)),
                ('available_from', models.DateTimeField(
                    null=True, verbose_name='available from', blank=True)),
                ('available_to', models.DateTimeField(
                    null=True, verbose_name='available to', blank=True)),
                ('carousel', models.ForeignKey(
                    related_name='slides', to='carousel.Carousel')),
                ('category_link', models.ForeignKey(
                    null=True,
                    verbose_name='category link',
                    related_name='+',
                    to='shuup.Category',
                    blank=True)),
                ('cms_page_link', models.ForeignKey(
                    null=True,
                    verbose_name='cms page link',
                    related_name='+',
                    to='shuup_simple_cms.Page',
                    blank=True)),
                ('product_link', models.ForeignKey(
                    null=True,
                    verbose_name='product link',
                    related_name='+',
                    to='shuup.Product',
                    blank=True)),
            ],
            options={
                'verbose_name_plural': 'Slides',
                'verbose_name': 'Slide',
                'ordering': ('ordering', 'id'),
            },
            bases=(parler.models.TranslatableModelMixin, models.Model)),
        migrations.CreateModel(
            name='SlideTranslation',
            fields=[
                ('id', models.AutoField(
                    serialize=False,
                    verbose_name='ID',
                    auto_created=True,
                    primary_key=True)),
                ('language_code', models.CharField(
                    max_length=15, verbose_name='Language', db_index=True)),
                ('caption', models.CharField(
                    null=True,
                    max_length=80,
                    verbose_name='caption',
                    blank=True)),
                ('caption_text', models.TextField(
                    null=True,
                    verbose_name='caption text',
                    help_text=(
                        'When displayed in banner box mode, '
                        'caption text is shown as a tooltip'),
                    blank=True)),
                ('external_link', models.CharField(
                    null=True,
                    max_length=160,
                    verbose_name='external link',
                    blank=True)),
                ('image', filer.fields.image.FilerImageField(
                    null=True,
                    verbose_name='image',
                    related_name='+',
                    on_delete=django.db.models.deletion.PROTECT,
                    to='filer.Image',
                    blank=True)),
                ('master', models.ForeignKey(
                    editable=False,
                    null=True,
                    related_name='translations',
                    to='carousel.Slide')),
            ],
            options={
                'db_tablespace': '',
                'verbose_name': 'Slide Translation',
                'managed': True,
                'default_permissions': (),
                'db_table': 'carousel_slide_translation',
            }),
        migrations.AlterUniqueTogether(
            name='slidetranslation',
            unique_together=set([('language_code', 'master')]), ),
        migrations.AlterField(
            model_name='carousel',
            name='is_arrows_visible',
            field=models.BooleanField(
                default=True,
                verbose_name='show navigation arrows',
                help_text=(
                    'When checked, navigational arrows are shown on the '
                    'carousel allowing for customers to go back and forward.')
            )),
        migrations.AlterField(
            model_name='carousel',
            name='name',
            field=models.CharField(
                max_length=50,
                verbose_name='name',
                help_text='The carousel name use for carousel configuration.'),
        ),
        migrations.AlterField(
            model_name='carousel',
            name='pause_on_hover',
            field=models.BooleanField(
                default=True,
                verbose_name='pause on hover',
                help_text=(
                    'When checked, the carousel cycling pauses '
                    'on mouse over.'))),
        migrations.AlterField(
            model_name='carousel',
            name='use_dot_navigation',
            field=models.BooleanField(
                default=True,
                verbose_name='show navigation dots',
                help_text=(
                    'When checked, navigational indicator dots are shown.')
            )),
        migrations.AlterField(
            model_name='slide',
            name='available_from',
            field=models.DateTimeField(
                null=True,
                verbose_name='available from',
                help_text=(
                    'Set the date and time from which this slide should be '
                    'visible in the carousel. This is useful to advertise '
                    'sales campaigns or other time-sensitive marketing.'),
                blank=True)),
        migrations.AlterField(
            model_name='slide',
            name='available_to',
            field=models.DateTimeField(
                null=True,
                verbose_name='available to',
                help_text=(
                    'Set the date and time from which this slide should be '
                    'visible in the carousel. This is useful to advertise '
                    'sales campaigns or other time-sensitive marketing.'),
                blank=True)),
        migrations.AlterField(
            model_name='slide',
            name='category_link',
            field=models.ForeignKey(
                null=True,
                verbose_name='category link',
                related_name='+',
                help_text=(
                    'Set the product category page that should be shown '
                    'when this slide is clicked, if any.'),
                to='shuup.Category',
                blank=True)),
        migrations.AlterField(
            model_name='slide',
            name='cms_page_link',
            field=models.ForeignKey(
                null=True,
                verbose_name='cms page link',
                related_name='+',
                help_text=(
                    'Set the web page that should be shown when the slide '
                    'is clicked, if any.'),
                to='shuup_simple_cms.Page',
                blank=True)),
        migrations.AlterField(
            model_name='slide',
            name='ordering',
            field=models.IntegerField(
                null=True,
                default=0,
                verbose_name='ordering',
                help_text=(
                    'Set the numeric order in which this slide should '
                    'appear relative to other slides in this carousel.'),
                blank=True)),
        migrations.AlterField(
            model_name='slide',
            name='product_link',
            field=models.ForeignKey(
                null=True,
                verbose_name='product link',
                related_name='+',
                help_text=(
                    'Set the product detail page that should be shown '
                    'when this slide is clicked, if any.'),
                to='shuup.Product',
                blank=True)),
        migrations.AlterField(
            model_name='slide',
            name='target',
            field=enumfields.fields.EnumIntegerField(
                default=0,
                verbose_name='link target',
                help_text=(
                    'Set this to current if clicking on this slide '
                    'should open a new browser tab.'),
                enum=shuup.front.apps.carousel.models.LinkTargetType)),
        migrations.AlterField(
            model_name='slidetranslation',
            name='caption',
            field=models.CharField(
                null=True,
                max_length=80,
                verbose_name='caption',
                help_text=(
                    'Text that describes the image. Used for search '
                    'engine purposes.'),
                blank=True)),
        migrations.AlterField(
            model_name='slidetranslation',
            name='external_link',
            field=models.CharField(
                null=True,
                max_length=160,
                verbose_name='external link',
                help_text=(
                    'Set the external site that should be shown when '
                    'this slide is clicked, if any.'),
                blank=True)),
        migrations.AlterField(
            model_name='slidetranslation',
            name='image',
            field=filer.fields.image.FilerImageField(
                null=True,
                verbose_name='image',
                related_name='+',
                help_text='The slide image to show.',
                on_delete=django.db.models.deletion.PROTECT,
                to='filer.Image',
                blank=True)),
    ]
