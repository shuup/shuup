# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from shuup import configuration


def create_default_shop_languages_config(apps, schema_editor):
    for shop in apps.get_model("shuup", "Shop").objects.all():
        if not configuration.get(shop, "languages"):
            configuration.set(shop, "languages", settings.LANGUAGES)


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0006_logmodels'),
    ]

    operations = [
        migrations.RunPython(create_default_shop_languages_config)
    ]
