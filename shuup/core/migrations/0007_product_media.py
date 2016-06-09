# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0006_shop_add_logo_and_public_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productmedia',
            name='external_url',
            field=models.URLField(help_text="Enter URL to external file. If this field is filled, the selected media doesn't apply.", null=True, verbose_name='URL', blank=True),
        ),
    ]
