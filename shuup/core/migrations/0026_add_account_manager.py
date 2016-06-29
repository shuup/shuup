# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0025_add_codes_for_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='account_manager',
            field=models.ForeignKey(blank=True, null=True, verbose_name='account manager', to='shuup.PersonContact'),
        ),
    ]
