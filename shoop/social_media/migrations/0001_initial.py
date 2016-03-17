# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import enumfields.fields
import shoop.social_media.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SocialMediaLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', enumfields.fields.EnumIntegerField(default=0, help_text='Type of social media link.', enum=shoop.social_media.models.SocialMediaLinkType, verbose_name='type')),
                ('url', models.URLField(help_text='Social media link URL.', verbose_name='URL')),
                ('ordering', models.IntegerField(default=0, null=True, verbose_name='ordering', blank=True)),
            ],
            options={
                'ordering': ['ordering'],
                'verbose_name': 'Social Media Link',
                'verbose_name_plural': 'Social Media Links',
            },
        ),
    ]
