# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations
import filer.fields.image

from shoop.core.models import Shop


def copy_names(apps, schema_editor):
    for shop in Shop.objects.all():
        for lang_code, lang_name in settings.LANGUAGES:
            shop.set_current_language(lang_code)
            shop.public_name = shop.name
            shop.save()


class Migration(migrations.Migration):

    dependencies = [
        ('filer', '0002_auto_20150606_2003'),
        ('shoop', '0005_drop_defaults_at_moneyfields'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='logo',
            field=filer.fields.image.FilerImageField(verbose_name='logo', blank=True, to='filer.Image', null=True),
        ),
        migrations.AddField(
            model_name='shoptranslation',
            name='public_name',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.RunPython(copy_names, migrations.RunPython.noop),
    ]
